"""Zhao et al. replication (zero calls): share of generated tests that are "effective" -- fail on the buggy version and
pass on the fixed one -- computed from the committed generation and execution records (authors' request, 3 Nov).

Definition, as Zhao et al. state it and as our Phase 2 design quotes it: effective = fails on the buggy version, passes
on the fixed one, over all generated tests. Numerator: test methods our committed labeller (`triage.labeling.label`)
marks PF (deterministic failure on B over three fresh-JVM runs, deterministic pass on F). Denominator: every test
method G generated (`n_tests` of each generation record), so tests that do not compile count as not effective; a second
denominator, test methods that compiled on both versions, is reported beside it. Bug-level cluster bootstrap of the
ratio of sums (B = 10,000, the committed seed). Reported for both D1 splits together (the frame Zhao et al. sampled)
and for the held-out split alone.

    python scripts/analysis/zhao_replication.py   -> results/heldout/analysis_final/zhao_replication.json
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import config, labeling  # noqa: E402
from triage.io_utils import dump_json  # noqa: E402

CANDS = ROOT / "data" / "interim" / "candidates_gemma4_26b"
EXECS = ROOT / "data" / "raw" / "executions_gemma4_26b"
OUT = ROOT / "results" / "heldout" / "analysis_final" / "zhao_replication.json"
ZHAO = {"low": 2.09, "high": 4.54, "unit": "percent", "models": 6,
        "source": "Zhao et al. [zhao2026misguidance], as quoted in the Phase 2 design"}


def main():
    split = json.loads((config.PROCESSED / "split_manifest.json").read_text(encoding="utf-8"))
    test_projects = set(split["test_projects"])
    per_bug = defaultdict(lambda: [0, 0, 0])          # bug -> [generated, compiled on both, effective]
    split_of = {}
    for p in CANDS.glob("*.json"):
        c = json.loads(p.read_text(encoding="utf-8"))
        bug = c["focal_id"].split("::")[0]
        per_bug[bug][0] += int(c["n_tests"])
        split_of[bug] = "test" if bug.rsplit("_", 1)[0] in test_projects else "dev"
    for p in EXECS.glob("*.json"):
        e = json.loads(p.read_text(encoding="utf-8"))
        bug = e["focal_id"].split("::")[0]
        for m in e.get("methods", []):
            if m.get("compile_b") and m.get("compile_f"):
                per_bug[bug][1] += 1
            if labeling.label(m)["label"] == labeling.PF:
                per_bug[bug][2] += 1
    rng_seed, B = config.SEED_BOOTSTRAP, config.BOOTSTRAP_RESAMPLES
    out = {"what": "share of generated tests that fail on buggy and pass on fixed (Zhao et al. 'effective')", "zhao_reported": ZHAO,
           "generator": "gemma4:26b (G, frozen), 3 generations per focal method", "subsets": {}}
    for name, bugs in (("all_D1", sorted(per_bug)), ("heldout", sorted(b for b in per_bug if split_of[b] == "test"))):
        arr = np.array([per_bug[b] for b in bugs], dtype=float)
        gen, comp, eff = arr.sum(axis=0)
        W = np.random.default_rng(rng_seed).multinomial(len(bugs), np.full(len(bugs), 1.0 / len(bugs)), size=B).astype(float)
        boot = (W @ arr[:, 2]) / (W @ arr[:, 0])
        boot_c = (W @ arr[:, 2]) / (W @ arr[:, 1])
        share = eff / gen
        out["subsets"][name] = {"bugs": len(bugs), "generated_tests": int(gen), "compiled_both": int(comp), "effective": int(eff),
                                "share_effective": share, "share_effective_pct": 100 * share,
                                "ci95_pct": [100 * float(np.quantile(boot, 0.025)), 100 * float(np.quantile(boot, 0.975))],
                                "share_of_compiled_pct": 100 * eff / comp,
                                "share_of_compiled_ci95_pct": [100 * float(np.quantile(boot_c, 0.025)), 100 * float(np.quantile(boot_c, 0.975))],
                                "within_zhao_range": bool(ZHAO["low"] <= 100 * share <= ZHAO["high"])}
        s = out["subsets"][name]
        print(name, s["bugs"], "bugs", s["generated_tests"], "generated", s["effective"], "effective",
              f"{s['share_effective_pct']:.2f}% [{s['ci95_pct'][0]:.2f}, {s['ci95_pct'][1]:.2f}]",
              f"of compiled {s['share_of_compiled_pct']:.2f}%", "within Zhao range:", s["within_zhao_range"])
    out["verdict_all_D1"] = "replicated" if out["subsets"]["all_D1"]["within_zhao_range"] else "not replicated"
    dump_json(OUT, out)


if __name__ == "__main__":
    main()
