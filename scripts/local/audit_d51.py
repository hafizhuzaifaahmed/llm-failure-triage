"""D-51 defect audit (no prompt, gate or threshold change). Dev pilot only.

    python scripts/local/audit_d51.py --run results/dev/GATE_M1b

For every judged J1 decision of the run, takes the EXACT prompt from the local call log and checks:
  (1) Table 8 fields: [F1] outcome + exception, [F2] message, [F3] failing test line, >= 1 stack frame line
      "at Class.method(File.java:N)" when the instance has frames, [T] test code, [Sig1] signature, and a [Doc]
      section that carries the method Javadoc when the instance has one;
  (2) the information R0 uses is present and readable: F1's outcome equals the instance outcome_type, and the
      instance's deepest frame (frames[0]) appears verbatim as [F4];
  (3) label mapping and join: every decision's instance_id is in the label store; PROGRAM_FAULT is scored as PF
      (analysis.Evaluation confusion counts recomputed by hand must match);
  (4) for the R0-right / J1-wrong cases among the picked instances: does J1 cite any F-frame id (F4+)?
Writes <run>/audit_D51.json.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import analysis, config  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402
from triage.ollama import LOCAL_CALL_LOG_DIR  # noqa: E402

FRAME = re.compile(r"^\[F(\d+)\] at [\w.$<>]+\([\w$.]+\.java:\d+\)", re.M)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--picked", default=str(ROOT / "results" / "dev" / "audit_D51" / "picked.json"))
    a = ap.parse_args()
    run = Path(a.run)
    calls = {}
    for f in Path(LOCAL_CALL_LOG_DIR).glob("*.jsonl"):
        if not f.name.startswith("_"):
            calls.update({r["key"]: r for r in read_jsonl(f)})
    inst = {i["instance_id"]: i for i in read_jsonl(config.PROCESSED / "instances_D1.jsonl")}
    labels = {l["instance_id"]: l for l in read_jsonl(config.GT_STORE / "labels_D1.jsonl")}
    decs = list(read_jsonl(run / "decisions.jsonl"))
    j1 = {d["instance_id"]: d for d in decs if d["arm"] == "J1"}
    r0 = {d["instance_id"]: d for d in decs if d["arm"] == "R0"}
    rows, problems = [], []
    for iid, d in sorted(j1.items()):
        text = calls[d["cost"]["call_keys"][0]]["messages"][0]["content"]
        f = inst[iid]["failure"]
        frames = f.get("frames", [])
        has_doc = bool((inst[iid].get("doc") or {}).get("method_javadoc"))
        checks = {
            "F1_outcome_exception": bool(re.search(r"^\[F1\] outcome=\w+; exception=", text, re.M)),
            "F2_message": "[F2] message:" in text,
            "F3_failing_line": "[F3] failing test line:" in text,
            "frames_present": (len(FRAME.findall(text)) > 0) if frames else True,
            "T_test_code": "[T1]" in text,
            "Sig1": "[Sig1]" in text,
            "Doc_method_javadoc": ("[Doc1]" in text) if has_doc else True,
            "R0_outcome_matches_F1": f"[F1] outcome={f['outcome_type']};" in text,
            "R0_frame0_is_F4": (f"[F4] at {frames[0]['method']}({frames[0]['location']})" in text) if frames else True,
        }
        bad = [k for k, v in checks.items() if not v]
        if bad:
            problems.append({"instance_id": iid, "failed": bad})
        rows.append({"instance_id": iid, "frames_in_instance": len(frames),
                     "frames_in_prompt": len(FRAME.findall(text)), **checks})
    # (3) mapping and join
    missing = [i for i in j1 if i not in labels]
    lab_pf = {i for i, l in labels.items() if l["label"] == "PF"}
    sample = json.loads((config.PROCESSED / "sample_D1_dev_pilot.json").read_text())
    ev = analysis.Evaluation(decs, [labels[i] for i in j1 if i in labels], sample["tf_weights"])
    s = ev.summary("J1|S1")
    hand = {"TP": 0, "FP": 0, "FN": 0, "TN": 0}
    for i, d in j1.items():
        if labels[i]["label"] not in ("PF", "TF") or d["label_raw"] == "INVALID":
            continue
        pred, true = d["label_raw"] == "PROGRAM_FAULT", i in lab_pf
        hand["TP" if pred and true else "FP" if pred else "FN" if true else "TN"] += 1
    mapping = {"decisions_without_label": missing, "hand_confusion": hand,
               "evaluation_confusion": {k: s[k] for k in ("TP", "FP", "FN", "TN")},
               "match": all(abs(hand[k] - s[k]) < 1e-9 for k in hand)}
    # (4) rationales of the picked R0-right / J1-wrong cases
    picked = json.loads(Path(a.picked).read_text())["r0_right_j1_wrong"]
    rationale = []
    for iid in picked:
        d = j1[iid]
        cited = d.get("evidence_ids") or []
        rationale.append({"instance_id": iid, "true": labels[iid]["label"], "J1": d["label_raw"],
                          "R0": r0[iid]["label_raw"], "R0_features": r0[iid].get("features"),
                          "cited": cited, "cites_F_frame": any(re.fullmatch(r"F([4-9]|\d\d+)", c) for c in cited),
                          "cites_F_any": any(c.startswith("F") for c in cited), "summary": d.get("summary")})
    out = {"run": str(run), "n_prompts_checked": len(rows), "field_problems": problems, "mapping": mapping,
           "rationales_r0_right_j1_wrong": rationale,
           "frames_truncated_instances": sum(r["frames_in_prompt"] < min(r["frames_in_instance"], 25) for r in rows),
           "rows": rows}
    dump_json(run / "audit_D51.json", out)
    print(json.dumps({k: out[k] for k in ("n_prompts_checked", "field_problems", "mapping",
                                           "frames_truncated_instances")}, indent=1))
    for r in rationale:
        print(r["instance_id"], r["true"], "J1", r["J1"], "R0", r["R0"], r["R0_features"], "cited", r["cited"],
              "F-frame", r["cites_F_frame"], "|", (r["summary"] or "")[:200])


if __name__ == "__main__":
    main()
