"""Is the per-frame C1 interval gap seed noise? Reproduce the registered seed's stream independently, then vary seeds."""
import json, sys
import numpy as np
rows = json.load(open(sys.argv[1]))
S = [r for r in rows if r["tr"] in ("F1", "F2") and r["label"] in ("PF", "TF")]

def ci(R, key, sign, seed, B=10000):
    bugs = sorted({r["bug"] for r in R}); bi = np.array([bugs.index(r["bug"]) for r in R])
    y = np.array([r["label"] == "PF" for r in R], float); f = np.array([bool(r[key]) for r in R], float)
    W = np.random.default_rng(seed).multinomial(len(bugs), np.full(len(bugs), 1.0 / len(bugs)), size=B).astype(float)[:, bi]
    with np.errstate(invalid="ignore", divide="ignore"):
        d = sign * ((W * y * f).sum(1) / (W * y).sum(1) - (W * (1 - y) * f).sum(1) / (W * (1 - y)).sum(1))
    d = d[~np.isnan(d)]
    return round(float(np.quantile(d, .025)), 4), round(float(np.quantile(d, .975)), 4), len(d)

reg = {("F1", "C1"): [-0.323, 0.2786], ("F2", "C1"): [-0.1264, 0.4133], ("ALL", "C1"): [-0.1372, 0.2735],
       ("ALL", "C2"): [0.114, 0.3723]}
for name in ("ALL", "F1", "F2"):
    R = [r for r in S if name == "ALL" or r["tr"] == name]
    for hyp, key, sign in (("C1", "flip", +1), ("C2", "dec", -1)):
        same = ci(R, key, sign, 20261011)
        others = [ci(R, key, sign, s) for s in range(1, 21)]
        lo = [o[0] for o in others]; hi = [o[1] for o in others]
        print(f"{name} {hyp}: registered-seed stream -> [{same[0]}, {same[1]}] (valid resamples {same[2]});"
              f" 20 other seeds: lower {min(lo):.4f}..{max(lo):.4f}, upper {min(hi):.4f}..{max(hi):.4f}"
              f" (sd upper {np.std(hi):.4f})")
