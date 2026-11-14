"""D-70: the E2 mixed-model fit is seeded (statsmodels fit_vb draws its starting SDs from fresh OS entropy unless
given an rng), and figures carry no timestamp and no hash-seed-dependent order, so the fit, its cluster bootstrap and
every analyze.py output file (tables, summary, PDF/PNG figures) are byte-identical on re-run."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from triage import figures, glmm
from test_glmm import simulate

ROOT = Path(__file__).resolve().parents[2]


def _bytes(x) -> str:
    return json.dumps(x, sort_keys=True)


def test_fit_is_identical_on_rerun():
    df = simulate(seed=3, n_proj=6, bugs_per_proj=4)
    assert _bytes(glmm.fit(df)) == _bytes(glmm.fit(df))
    assert glmm.fit(df)["vb_seed"] == glmm.GLMM_VB_SEED


def test_e2_models_and_bootstrap_are_identical_on_rerun():
    df = simulate(seed=4, n_proj=5, bugs_per_proj=3, reps=2)
    assert _bytes(glmm.e2_models(df)) == _bytes(glmm.e2_models(df))
    assert _bytes(glmm.cluster_bootstrap_ci(df, B=2)) == _bytes(glmm.cluster_bootstrap_ci(df, B=2))


SMOKE = ROOT / "results" / "smoke"

# analyze.run on the smoke fixture into argv[1]; run in a fresh interpreter so the hash seed differs
RUN_ANALYZE = r"""
import json, sys
from pathlib import Path
root = Path(sys.argv[2]); sys.path[:0] = [str(root / "scripts"), str(root / "src")]
import importlib.util
spec = importlib.util.spec_from_file_location("analyze_cli", root / "scripts" / "analyze.py")
an = importlib.util.module_from_spec(spec); spec.loader.exec_module(an)
from triage.io_utils import read_jsonl
base = root / "results" / "smoke"
samp = json.loads((base / "synthetic_sample.json").read_text())
excl = an.analysis.abort_exclusions(read_jsonl(base / "SMOKE_synthetic" / "leakage_rejections.jsonl"))
an.run(list(read_jsonl(base / "SMOKE_synthetic" / "decisions.jsonl")), list(read_jsonl(base / "synthetic_labels.jsonl")),
       samp["tf_weights"], Path(sys.argv[1]), True, set(samp["javadoc_ids"]), excl, "test")
"""

# per-project figure with tied and all-NaN projects, built from a set whose order depends on the hash seed
RUN_PER_PROJECT = r"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[2]) / "src"))
from triage import figures
names = {"Lang", "Math", "Time", "Cli", "Csv", "Gson", "Jsoup"}
pp = {"J1|S1": {p: (0.5 if p in ("Lang", "Math", "Time") else float("nan") if p == "Csv" else 0.3) for p in names},
      "SC|S1": {p: (0.5 if p in ("Lang", "Math", "Time") else float("nan") if p == "Csv" else 0.4) for p in names}}
figures.STAMP = "test"
figures.per_project(pp, Path(sys.argv[1]) / "fig_r5_per_project")
"""


def _outputs(script: str, out: Path, hash_seed: int) -> dict:
    env = {**os.environ, "PYTHONHASHSEED": str(hash_seed), "MPLBACKEND": "Agg"}
    subprocess.run([sys.executable, "-c", script, str(out), str(ROOT)], env=env, check=True, capture_output=True,
                   stdin=subprocess.DEVNULL)
    return {p.relative_to(out).as_posix(): p.read_bytes() for p in sorted(out.rglob("*")) if p.is_file()}


def _assert_identical(a: dict, b: dict):
    assert a.keys() == b.keys()
    for name in a:
        assert a[name] == b[name], name


def test_per_project_figure_is_identical_across_hash_seeds(tmp_path):
    runs = [_outputs(RUN_PER_PROJECT, tmp_path / f"h{h}", h) for h in (1, 2, 3, 4)]
    assert {"fig_r5_per_project.pdf", "fig_r5_per_project.png"} <= runs[0].keys()
    for r in runs[1:]:
        _assert_identical(runs[0], r)


def test_project_order_breaks_ties_by_name_and_puts_nan_last():
    pp = {"a": {"Math": 0.5, "Lang": 0.5, "Csv": float("nan"), "Cli": 0.2}, "b": {"Math": 0.5, "Lang": 0.5, "Cli": 0.4}}
    assert figures.project_order(pp) == ["Cli", "Lang", "Math", "Csv"]


@pytest.mark.skipif(not (SMOKE / "SMOKE_synthetic" / "decisions.jsonl").exists(), reason="smoke fixture not generated")
def test_analyze_output_is_byte_identical_on_rerun(tmp_path):
    """Every output file -- tables, summary, PDF and PNG figures -- across two interpreters with different hash seeds."""
    a = _outputs(RUN_ANALYZE, tmp_path / "run0", 11)
    b = _outputs(RUN_ANALYZE, tmp_path / "run1", 12)
    assert "tables/glmm_e2.json" in a and "figures/fig_r5_per_project.pdf" in a and "figures/fig_e1_prf.png" in a
    _assert_identical(a, b)
