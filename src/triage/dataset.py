"""From raw execution records to (a) the label store, (b) judge-side instance records, (c) the evaluation
sample with inverse-probability weights, and (d) the exclusion log. Phase 2 C8-C9 and Table 7.

Label store  : data/ground_truth_store/labels_<dataset>.jsonl     (read ONLY by evaluation code)
Instances    : data/processed/instances_<dataset>.jsonl           (no label, no F outcome)
Sample       : data/processed/sample_<dataset>.json               (instance ids + TF weights)
Exclusions   : data/processed/exclusions_<dataset>.jsonl          (every non-instance with its reason)
"""
from __future__ import annotations

import random
import re
from collections import Counter, defaultdict
from pathlib import Path

from . import config, javasrc, labeling, preprocess
from .io_utils import dump_json, read_jsonl, sha256_text, write_jsonl

FAIL = ("assertion_failure", "exception")


def project_packages(focal_package: str) -> list[str]:
    parts = focal_package.split(".")
    return [".".join(parts[:3])] if len(parts) >= 3 else [focal_package]


def _failure_view(run: dict, fqcn: str, src: str, focal_package: str) -> dict:
    norm = preprocess.normalise_stack_trace(run.get("trace", ""), project_packages(focal_package), fqcn)
    line = run.get("failing_test_line")
    lines = src.split("\n")
    expected = actual = None
    m = re.search(r"expected:\s*<(.*?)>\s*but was:\s*<(.*?)>", run.get("message", ""), re.S)
    if m:
        expected, actual = m.group(1), m.group(2)
    return {"outcome_type": run["outcome"], "exception_class": run.get("exception") or None,
            "message": preprocess.truncate_message(preprocess.scrub(run.get("message", ""))),
            "expected": expected, "actual": actual, "failing_test_line": line,
            "failing_test_line_text": lines[line - 1].strip() if line and line <= len(lines) else None,
            "frames": norm["frames"], "rendered_trace": norm["rendered"]}


def guard_record(instance_id: str, bug_name: str, fixed_body: str | None, buggy_body: str) -> dict:
    """Leakage-guard entry for one instance (see context_builder.leakage_check).

    bug_ids     the bug's identifier in the spellings Defects4J uses; matched on word boundaries, any length
    code_lines  lines that exist only in the fixed focal method (>= 12 chars); matched as substrings
    The guard file holds no labels and no outcome on F; it is read only by the pre-call check.
    """
    proj, num = bug_name.rsplit("_", 1)
    ids = [f"{proj}_{num}", f"{proj}-{num}", f"{proj}{num}b", f"{proj}{num}f", f"{proj}_{num}_buggy",
           f"{proj}_{num}_fixed"]
    lines = []
    if fixed_body:
        b_lines = {l.strip() for l in buggy_body.split("\n")}
        lines = [l.strip() for l in fixed_body.split("\n") if len(l.strip()) >= 12 and l.strip() not in b_lines]
    return {"instance_id": instance_id, "bug_ids": ids, "code_lines": lines, "paths": ["triage_work"]}


def build(dataset: str, executions: list[dict], candidates: dict[str, dict], contexts: dict[str, dict],
          fixed_bodies: dict[str, str]) -> dict:
    """executions: raw records from execution.execute_candidate (+ 'focal_id'). Returns counts."""
    labels, instances, exclusions, forbidden = [], [], [], []
    seen_bodies: dict[str, dict] = defaultdict(dict)  # focal_id -> body hash -> first instance id
    for ex in executions:
        cand = candidates[ex["candidate_id"]]
        ctx = contexts[cand["focal_id"]]
        comp = ex["compilation"]
        fq = f"{cand['package']}.{cand['class_name']}" if cand["package"] else cand["class_name"]
        base = {"dataset": dataset, "split": ctx["split"], "project": ctx["project"], "bug_name": ctx["bug_name"],
                "focal_id": ctx["focal_id"], "candidate_id": cand["candidate_id"], "generation": cand["generation"]}
        if comp.get("class_error"):
            exclusions.append({**base, "method": None, "category": "NC_CLASS", "reason": comp["class_error"][:300],
                               "n_methods": len(comp["nc_both"])})
        for name in comp.get("nc_both", []):
            if not comp.get("class_error"):
                exclusions.append({**base, "method": name, "category": "NC", "reason": "does not compile on B or F"})
        for name in comp.get("nc_one_version", []):
            exclusions.append({**base, "method": name, "category": "NC", "reason": "compiles on only one version"})
        for m in ex["methods"]:
            iid = sha256_text(f"{cand['candidate_id']}|{m['method']}")[:16]
            lab = labeling.label(m)
            if not labeling.is_triage_instance(lab["label"]):
                exclusions.append({**base, "instance_id": iid, "method": m["method"], "category": lab["label"],
                                   "reason": lab["reason"]})
                continue
            src = m["source_class"]
            tm = [x for x in javasrc.test_methods(src) if x.name == m["method"]][0]
            body_hash = sha256_text(preprocess.normalise_test_body(tm.text(src)))
            if body_hash in seen_bodies[ctx["focal_id"]]:
                exclusions.append({**base, "instance_id": iid, "method": m["method"], "category": "DUPLICATE",
                                   "reason": f"identical normalised body to {seen_bodies[ctx['focal_id']][body_hash]}"})
                continue
            seen_bodies[ctx["focal_id"]][body_hash] = iid
            failure = _failure_view(m["runs_b"][0], fq, src, ctx["package"])
            feats_deepest = preprocess.deepest_project_frame(failure["frames"], ctx["focal_class"])
            labels.append({"instance_id": iid, **base, "label": lab["label"], "sigma_B": lab["sigma_B"],
                           "sigma_F": lab["sigma_F"], "reason": lab["reason"]})
            instances.append({
                "instance_id": iid, **base, "method": m["method"],
                "test": {"method_source": tm.text(src).strip(), "imports": javasrc.imports_of(src),
                         "fixtures": javasrc.fixtures_of(src)},
                "failure": failure, "sig": ctx["sig"], "doc": ctx["doc"], "impl": ctx["impl_B"],
                "focal_class": ctx["focal_class"], "focal_method_name": ctx["focal_method_name"],
                "covariates": {"test_lines": tm.text(src).count("\n") + 1,
                               "n_assertions": len(re.findall(r"\bassert\w*\s*\(", tm.text(src))),
                               "failure_type": failure["outcome_type"], "deepest_frame": feats_deepest,
                               "javadoc_present": bool(ctx["doc"].get("method_javadoc")),
                               "javadoc_edited_by_fix": ctx.get("javadoc_edited_by_fix", False)},
            })
            forbidden.append(guard_record(iid, ctx["bug_name"], fixed_bodies.get(ctx["focal_id"]), ctx["impl_B"]))
    write_jsonl(config.GT_STORE / f"labels_{dataset}.jsonl", labels)
    write_jsonl(config.LEAKAGE_GUARD / f"guard_{dataset}.jsonl", forbidden)
    write_jsonl(config.PROCESSED / f"instances_{dataset}.jsonl", instances)
    write_jsonl(config.PROCESSED / f"exclusions_{dataset}.jsonl", exclusions)
    counts = {"labels": dict(Counter(l["label"] for l in labels)),
              "exclusions": dict(Counter(e["category"] for e in exclusions)),
              "executed_methods": sum(len(e["methods"]) for e in executions)}
    return counts


def _largest_remainder(total: int, sizes: dict[str, int]) -> dict[str, int]:
    """Allocate `total` draws to strata proportionally to `sizes`, never exceeding a stratum's size."""
    pop = sum(sizes.values())
    total = min(total, pop)
    if not pop or not total:
        return {k: 0 for k in sizes}
    share = {k: total * v / pop for k, v in sizes.items()}
    alloc = {k: min(sizes[k], int(share[k])) for k in sizes}
    for k in sorted(sizes, key=lambda k: (share[k] - int(share[k]), k), reverse=True):
        if sum(alloc.values()) >= total:
            break
        if alloc[k] < sizes[k]:
            alloc[k] += 1
    return alloc


def allocate(labels: list[dict], mode: str = "per_project", ratio: int = config.PF_TO_TF_RATIO,
             seed: int = config.SEED_TF_SAMPLE, cap: int | None = None) -> dict:
    """Evaluation sample (Phase 2 C9: keep all PF, sample TF at random, stratified by project, PF:TF = 1:2).

    mode="per_project" (dev pilot reading; for D1-test the alternative since X-07 was decided, D-53): ratio x PF within each project — the reading the
        pipeline implemented before the corrective pass. A project with 0 PF contributes 0 TF and drops out;
        a project with fewer than 2 x PF TF instances contributes all it has (overall ratio can fall below 1:2).
    mode="proportional" (X-07, decided D-53: PRIMARY for D1-test): the TF quota is
        ratio x (total PF), allocated to projects in proportion to their TF population (largest remainder).
    cap: PILOT ONLY. If PF + TF + AMB would exceed `cap`, PF, TF and AMB are subsampled proportionally
        (seeded) so the judged set fits the pilot budget; PF/AMB then also get weights. Never used for D1-test.
    TF weight = N_TF(project) / n_TF(project) (inverse sampling probability).
    """
    rng = random.Random(seed)
    projects = sorted({l["project"] for l in labels})
    by = {p: {c: sorted([l for l in labels if l["project"] == p and l["label"] == c], key=lambda r: r["instance_id"])
              for c in ("PF", "TF", "AMB")} for p in projects}
    n_pf_total = sum(len(by[p]["PF"]) for p in projects)
    if mode == "proportional":
        quota = _largest_remainder(ratio * n_pf_total, {p: len(by[p]["TF"]) for p in projects})
    elif mode == "per_project":
        quota = {p: min(len(by[p]["TF"]), ratio * len(by[p]["PF"])) for p in projects}
    else:
        raise ValueError(mode)
    chosen = {p: {"PF": list(by[p]["PF"]), "TF": rng.sample(by[p]["TF"], quota[p]), "AMB": list(by[p]["AMB"])}
              for p in projects}
    weights = {}
    for p in projects:
        for r in chosen[p]["TF"]:
            weights[r["instance_id"]] = len(by[p]["TF"]) / quota[p]
    n_all = sum(len(chosen[p][c]) for p in projects for c in chosen[p])
    capped = bool(cap and n_all > cap)
    if capped:
        frac = cap / n_all
        for c in ("PF", "TF", "AMB"):
            sizes = {p: len(chosen[p][c]) for p in projects}
            keep = _largest_remainder(round(frac * sum(sizes.values())), sizes)
            for p in projects:
                before = len(chosen[p][c])
                chosen[p][c] = rng.sample(chosen[p][c], keep[p])
                for r in chosen[p][c]:
                    base = weights.get(r["instance_id"], 1.0)
                    weights[r["instance_id"]] = base * before / keep[p]
    per_project = {p: {"PF": len(by[p]["PF"]), "PF_sampled": len(chosen[p]["PF"]), "TF_total": len(by[p]["TF"]),
                       "TF_sampled": len(chosen[p]["TF"]), "AMB": len(by[p]["AMB"]), "AMB_sampled": len(chosen[p]["AMB"]),
                       "in_sample": bool(chosen[p]["PF"] or chosen[p]["TF"])} for p in projects}
    ids = sorted(r["instance_id"] for p in projects for c in chosen[p] for r in chosen[p][c])
    return {"mode": mode, "ratio": ratio, "seed": seed, "cap": cap, "capped": capped, "instance_ids": ids,
            "tf_weights": {k: v for k, v in weights.items()}, "per_project": per_project,
            "projects_dropped": [p for p in projects if not per_project[p]["in_sample"] and by[p]["TF"]]}


def sample(dataset: str, split: str | None = "test", ratio: int = config.PF_TO_TF_RATIO,
           seed: int = config.SEED_TF_SAMPLE, mode: str = "per_project", cap: int | None = None,
           suffix: str = "") -> dict:
    labels = [l for l in read_jsonl(config.GT_STORE / f"labels_{dataset}.jsonl") if split is None or l["split"] == split]
    out = {"dataset": dataset, "split": split, **allocate(labels, mode, ratio, seed, cap)}
    dump_json(config.PROCESSED / f"sample_{dataset}_{split}{suffix}.json", out)
    return out
