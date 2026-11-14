"""D2 seeded-fault instances (Phase 2 Section 3.2, C2-C9; experiment E5-R1).

A D2 "focal unit" is one verified mutant of a held-out focal method: B = F + that mutant, F = the fixed checkout.
Its id is `<D1 focal_id>#m<mutant id>`, so every D2 item is traceable to its test-split focal method and the
held-out lock can resolve its split from the D1 context. From there the D1 pipeline is reused unchanged:
context extraction (from D2's B, `frame.extract_context` with explicit workdirs), generation by G, dual execution
(`execution.execute_candidate` with B = the mutant version), labelling (Table 6) and `dataset.build`.

Building contexts and preparing mutant versions needs Defects4J and runs in WSL; nothing here calls a model.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Iterable, Optional

from . import config

D2_SEP = "#m"
CONTEXT_DIR = config.INTERIM / "context_D2"
FIXED_BODIES = config.GT_STORE / "fixed_bodies_D2.jsonl"
MUTANTS_FILE = config.PROCESSED / "d2_mutants.jsonl"


class D2Inconsistent(RuntimeError):
    """A mutant version does not reproduce the verified mutant (source hash or focal body differs)."""


def d2_focal_id(focal_id: str, mutant_id: int) -> str:
    if D2_SEP in focal_id:
        raise ValueError(f"{focal_id!r} is already a D2 id")
    return f"{focal_id}{D2_SEP}{int(mutant_id)}"


def base_focal_id(focal_id: str) -> str:
    """D1 focal id of a D2 id (identity for a D1 id)."""
    return focal_id.split(D2_SEP, 1)[0]


def mutant_id_of(focal_id: str) -> Optional[int]:
    return int(focal_id.split(D2_SEP, 1)[1]) if D2_SEP in focal_id else None


def verified_mutants(records: Iterable[dict]) -> list[tuple[dict, dict]]:
    """(focal record, mutant) for every VERIFIED mutant of every focal method with status OK, in a fixed order."""
    out = []
    for rec in records:
        if rec.get("status") != "OK":
            continue
        for m in rec.get("chosen", []):
            if m.get("verdict") == "VERIFIED":
                out.append((rec, m))
    return sorted(out, key=lambda rm: (rm[0]["focal_id"], rm[1]["mutant_id"]))


def context_file(d2_id: str) -> Path:
    return CONTEXT_DIR / f"{hashlib.sha256(d2_id.encode()).hexdigest()[:16]}.json"


def load_contexts(directory: Path = CONTEXT_DIR) -> dict[str, dict]:
    out = {}
    for p in sorted(Path(directory).glob("*.json")):
        c = json.loads(p.read_text(encoding="utf-8"))
        out[c["focal_id"]] = c
    return out


def _norm(text: Optional[str]) -> Optional[str]:
    return None if text is None else text.replace("\r\n", "\n").replace("\r", "\n")


def same_body(extracted: Optional[str], verified: Optional[str]) -> bool:
    """`extracted` comes from read_text (UTF-8, errors replaced, universal newlines); `verified` from
    mutants.read_src (UTF-8, or Latin-1 when the file is not valid UTF-8, newlines kept)."""
    if extracted is None or verified is None:
        return False
    if _norm(extracted) == _norm(verified):
        return True
    try:
        as_read = verified.encode("latin-1").decode("utf-8", errors="replace")
    except UnicodeEncodeError:
        return False
    return _norm(extracted) == _norm(as_read)


def prepare_mutant_version(project: str, bug: str, mut: dict, meta_f: dict) -> dict:
    """B for one D2 unit: the compiled mutant version `m<id>` next to F (built by `mutants.build_for_focal`).

    Reused when its source file still hashes to the verified `mutated_source_sha256`; otherwise F is copied
    again and the logged diff re-applied with `mutants.materialise`, and the result must hash to the same value.
    Always (re)compiled, so a stale tree can never be executed. Idempotent; WSL only.
    """
    from .execution import WORK, d4j
    from .mutants import materialise, read_src, write_src
    mid, diff = mut["mutant_id"], mut["diff"]
    fdir = Path(meta_f["workdir"])
    vdir = WORK / f"{project}_{bug}" / f"m{mid}"
    want = mut["mutated_source_sha256"]

    def current() -> Optional[str]:
        p = vdir / diff["file"]
        if not p.exists():
            return None
        src, _ = read_src(p)
        return hashlib.sha256(src.encode()).hexdigest()

    if current() != want:
        if vdir.exists():
            shutil.rmtree(vdir)
        shutil.copytree(fdir, vdir, symlinks=True)
        f_src, enc = read_src(fdir / diff["file"])
        new_src = materialise(f_src, {"original": diff["original"], "mutated": diff["mutated"], "offset": diff["offset"]})
        if new_src is None or hashlib.sha256(new_src.encode()).hexdigest() != want:
            raise D2Inconsistent(f"mutant {mid} of {project}_{bug} no longer materialises to its verified source")
        write_src(vdir / diff["file"], new_src, enc)
    d4j("compile", "-w", str(vdir))
    props = {k: d4j("export", "-p", k, "-w", str(vdir)).strip() for k in ("cp.test", "dir.src.classes", "dir.src.tests")}
    meta = {"project": project, "bug": bug, "version": f"m{mid}", "workdir": str(vdir), "mutant_of": "f", **props}
    (vdir.parent / f"meta_m{mid}.json").write_text(json.dumps(meta, indent=2))
    return meta


def context_for_mutant(rec: dict, info: dict, mut: dict, b_workdir: Path, f_workdir: Path) -> tuple[dict, Optional[str]]:
    """D2 context from D2's own B (the mutant version) plus F's focal body for the leakage guard (label side).

    `rec` is the D1 frame record of the focal method; it must belong to the test split. The extracted focal
    body must equal the mutated body recorded when the mutant was verified (line endings normalised).
    """
    from .frame import extract_context
    if rec.get("split") != "test":
        raise ValueError(f"D2 is derived only from test-split methods; {rec['focal_id']} is {rec.get('split')!r}")
    ctx = extract_context(rec, info, b_workdir=Path(b_workdir), f_workdir=Path(f_workdir),
                          mask_lines={mut["diff"]["file"]: {int(mut["line"])}})
    if not same_body(ctx["impl_B"], mut.get("mutated_focal_body")):
        raise D2Inconsistent(f"focal body extracted from m{mut['mutant_id']} differs from the verified mutated body "
                             f"({rec['focal_id']})")
    fixed = ctx.pop("_label_side", {}).get("fixed_body")
    ctx.update({"focal_id": d2_focal_id(rec["focal_id"], mut["mutant_id"]), "base_focal_id": rec["focal_id"],
                "mutant_id": mut["mutant_id"], "operator": mut["operator"], "dataset": "D2", "split": "test",
                "project": rec["project"], "bug_name": rec["bug_name"],
                "javadoc_edited_by_fix": False})   # a mutant never edits the Javadoc
    return ctx, fixed


# ------------------------------------------------------------------------------------------
# pipeline stages (each idempotent; the CLI is scripts/d2_pipeline.py)
# ------------------------------------------------------------------------------------------

def contexts_for_bug(project: str, bug: str, units: list[tuple[dict, dict]], frame_recs: dict[str, dict],
                     info: dict, skip: set[str]) -> list[tuple[str, Optional[dict], Optional[str], Optional[str]]]:
    """WSL. All D2 units of ONE bug, sequentially (they share F's checkout). Returns (d2_id, ctx, fixed, error)."""
    from .execution import prepare_version
    out = []
    todo = [(r, m) for r, m in units if d2_focal_id(r["focal_id"], m["mutant_id"]) not in skip]
    if not todo:
        return out
    try:
        meta_f = prepare_version(project, bug, "f")
    except Exception as e:
        return [(d2_focal_id(r["focal_id"], m["mutant_id"]), None, None, f"prepare F failed: {e}") for r, m in todo]
    for r, m in todo:
        did = d2_focal_id(r["focal_id"], m["mutant_id"])
        try:
            meta_m = prepare_mutant_version(project, bug, m, meta_f)
            ctx, fixed = context_for_mutant(frame_recs[r["focal_id"]], info, m, Path(meta_m["workdir"]),
                                            Path(meta_f["workdir"]))
            out.append((did, ctx, fixed, None))
        except Exception as e:
            out.append((did, None, None, f"{type(e).__name__}: {e}"))
    return out


def generate_units(ctxs: Iterable[dict], client, prompts, model_id: str, out_dir: Path) -> tuple[int, int]:
    """G generation for D2 units: GENERATIONS_PER_FOCAL per unit, the D1 generation code and prompt unchanged.
    Re-running regenerates nothing that is in the call log. Raises StopRequested on a stop request (D-58)."""
    from .generation import generate
    from .io_utils import dump_json
    n_ok = n = 0
    for ctx in ctxs:
        if D2_SEP not in ctx["focal_id"]:
            raise ValueError(f"not a D2 unit: {ctx['focal_id']}")
        for g in range(config.GENERATIONS_PER_FOCAL):
            c = generate(ctx, client, prompts, model_id, g)
            c["dataset"] = "D2"
            dump_json(Path(out_dir) / f"{c['candidate_id']}.json", c)
            n_ok += c["assembled"]
            n += 1
    return n, n_ok


def execute_bug(project: str, bug: str, cands_by_unit: dict[str, list[dict]],
                mutant_of: dict[str, dict]) -> list[tuple[str, Optional[dict], Optional[str]]]:
    """WSL. Dual execution of every candidate of ONE bug's D2 units: B = the unit's mutant version, F = the fixed
    checkout. Returns (candidate_id, execution record, error) like run_execution's bug job."""
    import time
    import traceback
    from . import execution
    out = []
    try:
        meta_f = execution.prepare_version(project, bug, "f")
    except Exception as e:
        return [(c["candidate_id"], None, f"prepare F failed: {e}") for cs in cands_by_unit.values() for c in cs]
    for did, cands in sorted(cands_by_unit.items()):
        try:
            meta_m = prepare_mutant_version(project, bug, mutant_of[did], meta_f)
        except Exception as e:
            out.extend((c["candidate_id"], None, f"prepare mutant failed: {e}") for c in cands)
            continue
        for c in cands:
            try:
                rec = execution.execute_candidate(c, meta_m, meta_f)
                rec.update(focal_id=c["focal_id"], dataset="D2", mutant_version=meta_m["version"],
                           utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
                out.append((c["candidate_id"], rec, None))
            except Exception as e:
                out.append((c["candidate_id"], None, f"{type(e).__name__}: {e}\n{traceback.format_exc()[-800:]}"))
    return out
