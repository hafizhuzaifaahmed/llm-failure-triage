"""D-106: the review-sensitivity analyses run end to end on synthetic decisions (no real output read)."""
import importlib.util
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
spec = importlib.util.spec_from_file_location("review_sensitivity", ROOT / "scripts" / "analysis" / "review_sensitivity.py")
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)

from triage import analysis  # noqa: E402


def synthetic():
    rnd = random.Random(3)
    ids = [f"i{k}" for k in range(90)]
    labels = [{"instance_id": i, "label": "PF" if k % 3 == 0 else "TF", "bug_name": f"b{k // 3}", "project": "P"}
              for k, i in enumerate(ids)]
    lab = {l["instance_id"]: l["label"] for l in labels}
    dec = []
    for arm in ("J1", "SC", "DEB"):
        for lvl in ("S0", "S1", "S2"):
            for rep in range(3):
                for i in ids:
                    right = "PROGRAM_FAULT" if lab[i] == "PF" else "TEST_FAULT"
                    wrong = "TEST_FAULT" if right == "PROGRAM_FAULT" else "PROGRAM_FAULT"
                    d = {"instance_id": i, "arm": arm, "level": lvl, "variant": "full", "replicate": rep,
                         "label_raw": right if rnd.random() < 0.7 else wrong,
                         "agreement": {"vote_share_pf": 0.5, "k": 5}}
                    dec.append(d)
    for i in ids:
        dec.append({"instance_id": i, "arm": "R0", "level": None, "variant": None, "replicate": 0,
                    "label_raw": "PROGRAM_FAULT" if rnd.random() < 0.5 else "TEST_FAULT"})
    return analysis.Evaluation(dec, labels), set(ids[:60])


def test_mcc_family_and_two_level_bootstrap_on_synthetic_data():
    ev, jd = synthetic()
    fam = rs.mcc_family(ev, jd)
    assert [c["name"] for c in fam] == ["H1", "H2a", "H2b", "H3a", "H3b"]
    assert all(0 <= c["p_holm"] <= 1 for c in fam)
    tl = rs.two_level(ev, jd)
    assert len(tl) == 5
    for c in tl:
        if c["widening_factor"] is not None:
            assert c["widening_factor"] > 0.5            # resampling replicates cannot shrink the CI much
