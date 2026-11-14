"""Triage arms: DA, KA, R0, J1, SC, SC-T (Table 10), DEB (Table 9) and the debate ablations A1, A2.

A4 (no failure evidence) and A5 (implementation exposure) are evidence-package variants and therefore
live in `context_builder.build_package`; any arm can be run on such a package.

Every LLM arm returns one decision record. `label_raw` is PROGRAM_FAULT, TEST_FAULT or INVALID;
scoring (INVALID -> TEST_FAULT in the primary analysis) happens in `metrics`, not here.
"""
from __future__ import annotations

import hashlib
import random
from typing import Optional

from . import config
from .context_builder import Package, cited_ids_valid
from .llm import LLMClient, result_cost_dict
from .preprocess import cap_words
from .prompts import PromptSet
from .schema import parse_output

PF, TF, INVALID = "PROGRAM_FAULT", "TEST_FAULT", "INVALID"


def _msg(text: str) -> list[dict]:
    return [{"role": "user", "content": text}]


def _base(instance_id, arm, package: Optional[Package], model_id, replicate):
    return {"instance_id": instance_id, "arm": arm,
            "level": package.level if package else None,
            "variant": package.variant if package else None,
            "model": model_id, "replicate": replicate}


# --------------------------------------------------------------------------------------------
# Non-LLM baselines
# --------------------------------------------------------------------------------------------

def policy_arm(instance_id: str, arm: str) -> dict:
    lab = {"DA": TF, "KA": PF}[arm]
    return {**_base(instance_id, arm, None, None, 0), "label_raw": lab, "cost": result_cost_dict([])}


def r0_features(failure: dict, focal_class: str, focal_method_name: str) -> dict:
    """Three deterministic features (Section 3.6). Computed from the failure on B only."""
    frames = failure.get("frames", [])
    is_assertion = failure.get("outcome_type") == "assertion_failure"
    if not frames:
        deepest = "none"
    elif frames[0].get("in_test"):
        deepest = "test"
    elif focal_class and frames[0]["method"].startswith(focal_class + "."):
        deepest = "focal"
    else:
        deepest = "main"
    raised_in_focal = bool(frames) and frames[0]["method"] == f"{focal_class}.{focal_method_name}"
    return {"is_assertion_failure": is_assertion, "deepest_project_frame": deepest,
            "raised_in_focal": raised_in_focal}


def r0_arm(instance: dict) -> dict:
    feats = r0_features(instance["failure"], instance.get("focal_class", ""), instance.get("focal_method_name", ""))
    pf = (not feats["is_assertion_failure"]) and feats["deepest_project_frame"] in ("focal", "main")
    return {**_base(instance["instance_id"], "R0", None, None, 0), "label_raw": PF if pf else TF,
            "features": feats, "cost": result_cost_dict([])}


# --------------------------------------------------------------------------------------------
# Single-agent LLM arms
# --------------------------------------------------------------------------------------------

def _judge_call(client, prompts, package, model_id, sample_index, tag, prompt_name="judge"):
    res = client.complete(role=prompt_name, model_id=model_id,
                          messages=_msg(prompts.render(prompt_name, package=package.text)),
                          sample_index=sample_index, tag=tag)
    parsed = parse_output(res.text, "judge")
    return res, parsed


def _decision_fields(parsed, package) -> dict:
    if not parsed.ok:
        return {"label_raw": INVALID, "reason_category": None, "evidence_ids": [], "invalid_evidence_ids": [],
                "summary": None, "confidence": None, "parse_error": parsed.error, "repaired": False}
    d = parsed.data
    valid, bad = cited_ids_valid(d["evidence_ids"], package)
    return {"label_raw": d["label"], "reason_category": d["reason_category"], "evidence_ids": valid,
            "invalid_evidence_ids": bad, "summary": d["summary"], "confidence": d["confidence"],
            "parse_error": None, "repaired": parsed.repaired}


def j1_arm(instance_id, package, client: LLMClient, prompts: PromptSet, model_id, replicate=0,
           prompt_name="judge", arm_name="J1") -> dict:
    tag = f"{arm_name}|{package.level}|{package.variant}"
    res, parsed = _judge_call(client, prompts, package, model_id, replicate * 1000, tag, prompt_name)
    return {**_base(instance_id, arm_name, package, model_id, replicate), **_decision_fields(parsed, package),
            "agreement": {}, "cost": result_cost_dict([res])}


def sc_votes(instance_id, package, client, prompts, model_id, k, replicate=0, arm_name="SC"):
    tag = f"{arm_name}|{package.level}|{package.variant}"
    results, votes, samples = [], [], []
    for j in range(k):
        res, parsed = _judge_call(client, prompts, package, model_id, replicate * 1000 + j, tag)
        results.append(res)
        f = _decision_fields(parsed, package)
        votes.append(f["label_raw"])
        samples.append(f)
    return results, votes, samples


def aggregate_votes(votes: list[str], k_allocated: int, threshold: Optional[float] = None) -> dict:
    """Majority over valid votes; a tie among valid votes resolves to TF (Section 3.10).

    With `threshold` (ablation A3) the rule becomes PF iff v >= threshold where v = #PF / k_allocated.
    """
    n_pf = sum(v == PF for v in votes)
    n_tf = sum(v == TF for v in votes)
    n_invalid = sum(v == INVALID for v in votes)
    v = n_pf / k_allocated
    if n_pf + n_tf == 0:
        label = INVALID
    elif threshold is not None:
        label = PF if v >= threshold - 1e-12 else TF
    else:
        label = PF if n_pf > n_tf else TF
    return {"label_raw": label, "vote_share_pf": v, "n_pf": n_pf, "n_tf": n_tf, "n_invalid": n_invalid}


def sc_arm(instance_id, package, client, prompts, model_id, k=config.SC_SAMPLES, replicate=0,
           arm_name="SC") -> dict:
    results, votes, samples = sc_votes(instance_id, package, client, prompts, model_id, k, replicate, arm_name)
    agg = aggregate_votes(votes, k)
    # representative fields: first valid sample agreeing with the majority
    rep = next((s for s in samples if s["label_raw"] == agg["label_raw"]), samples[0])
    return {**_base(instance_id, arm_name, package, model_id, replicate),
            **{k_: rep[k_] for k_ in ("reason_category", "evidence_ids", "invalid_evidence_ids", "summary",
                                       "confidence")},
            "label_raw": agg["label_raw"], "votes": votes,
            "agreement": {"vote_share_pf": agg["vote_share_pf"], "n_pf": agg["n_pf"], "n_tf": agg["n_tf"],
                          "n_invalid": agg["n_invalid"], "k": k},
            "invalid_samples": sum(v == INVALID for v in votes),
            "cost": result_cost_dict(results)}


# --------------------------------------------------------------------------------------------
# Debate
# --------------------------------------------------------------------------------------------

def _arg_text(parsed, raw_text) -> str:
    if parsed.ok:
        d = parsed.data
        ids = ", ".join(d["evidence_ids"]) or "none"
        return f"Position: {d['position']}. Concedes: {str(d['concede']).lower()}. Cited: {ids}.\n{cap_words(d['argument'])}"
    return "(this analyst produced no valid argument)"


def _order_rng(instance_id: str, replicate: int) -> random.Random:
    seed = int(hashlib.sha256(f"{config.SEED_ARGUMENT_ORDER}|{instance_id}|{replicate}".encode()).hexdigest()[:12], 16)
    return random.Random(seed)


def deb_arm(instance_id, package, client: LLMClient, prompts: PromptSet, model_id, replicate=0,
            variant: str = "DEB") -> dict:
    """Five calls: P-R1, T-R1 (independent), P-R2, T-R2, adjudicator.

    variant: DEB (proposed) | A1 (no exchange) | A2 (symmetric neutral debaters)
    """
    assert variant in ("DEB", "A1", "A2")
    tag = f"{variant}|{package.level}|{package.variant}"
    si = replicate * 1000
    call = lambda name, text, idx: client.complete(role=name, model_id=model_id, messages=_msg(text),
                                                   sample_index=si + idx, tag=tag)
    if variant == "A2":
        r1_prompts = ("debater_neutral_r1", "debater_neutral_r1")
    else:
        r1_prompts = ("advocate_p_r1", "advocate_t_r1")

    # Round 1 — each side sees the package only
    p1 = call(r1_prompts[0], prompts.render(r1_prompts[0], package=package.text), 0)
    t1 = call(r1_prompts[1], prompts.render(r1_prompts[1], package=package.text), 1)
    p1p, t1p = parse_output(p1.text, "advocate"), parse_output(t1.text, "advocate")
    p1s, t1s = _arg_text(p1p, p1.text), _arg_text(t1p, t1.text)

    # Round 2 — DEB/A2 see the opponent's R1 argument; A1 sees only its own
    if variant == "DEB":
        p2_txt = prompts.render("advocate_r2", side="P", position=PF, package=package.text, own=p1s, opponent=t1s)
        t2_txt = prompts.render("advocate_r2", side="T", position=TF, package=package.text, own=t1s, opponent=p1s)
    elif variant == "A1":
        p2_txt = prompts.render("advocate_r2_noexchange", side="P", position=PF, package=package.text, own=p1s)
        t2_txt = prompts.render("advocate_r2_noexchange", side="T", position=TF, package=package.text, own=t1s)
    else:
        p2_txt = prompts.render("debater_neutral_r2", package=package.text, own=p1s, opponent=t1s)
        t2_txt = prompts.render("debater_neutral_r2", package=package.text, own=t1s, opponent=p1s)
    p2 = call("r2_a", p2_txt, 2)
    t2 = call("r2_b", t2_txt, 3)
    p2p, t2p = parse_output(p2.text, "advocate"), parse_output(t2.text, "advocate")
    p2s, t2s = _arg_text(p2p, p2.text), _arg_text(t2p, t2.text)

    # Adjudication — anonymised ("Analyst X/Y"), randomised order
    rng = _order_rng(instance_id, replicate)
    sides = [("A", p1s, p2s, p1p, p2p), ("B", t1s, t2s, t1p, t2p)]
    rng.shuffle(sides)
    blocks = []
    for name, (side, r1s, r2s, _, _) in zip(("X", "Y"), sides):
        blocks.append(f"--- Analyst {name} ---\nFirst statement:\n{r1s}\nSecond statement:\n{r2s}")
    adj = call("adjudicator", prompts.render("adjudicator", package=package.text, arguments="\n\n".join(blocks)), 4)
    adjp = parse_output(adj.text, "judge")
    dec = _decision_fields(adjp, package)

    def pos(p):
        return p.data["position"] if p.ok else None

    last_side = sides[-1]
    last_position = pos(last_side[4]) or pos(last_side[3])
    agreement = {
        "order": [s[0] for s in sides],  # A = program-side (or neutral 1), B = test-side (or neutral 2)
        "r1_positions": [pos(p1p), pos(t1p)], "r2_positions": [pos(p2p), pos(t2p)],
        "r1_concede": [p1p.data.get("concede") if p1p.ok else None, t1p.data.get("concede") if t1p.ok else None],
        "r2_concede": [p2p.data.get("concede") if p2p.ok else None, t2p.data.get("concede") if t2p.ok else None],
        "sided_with_last_presented": (dec["label_raw"] == last_position) if last_position else None,
        "no_evidence_cited": dec["label_raw"] != INVALID and not dec["evidence_ids"],
        "invalid_advocate_outputs": sum(not p.ok for p in (p1p, t1p, p2p, t2p)),
    }
    results = [p1, t1, p2, t2, adj]
    return {**_base(instance_id, variant, package, model_id, replicate), **dec, "agreement": agreement,
            "rounds": {"r1": [p1.key, t1.key], "r2": [p2.key, t2.key], "adjudicator": adj.key},
            "cost": result_cost_dict(results)}
