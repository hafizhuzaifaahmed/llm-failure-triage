"""P1/A3: delete-one-bug jackknife SE and normal 95% interval for C1 and C2 (F1+F2 scored tests).

C1 = P(flip|PF) - P(flip|TF);  C2 = P(dec|TF) - P(dec|PF). Rates are pooled test-level proportions,
recomputed with each bug (cluster) deleted in turn. Imports no project module.
Usage: python a3_jackknife.py <rows.json>
"""
import json, math, sys

rows = [r for r in json.load(open(sys.argv[1], encoding="utf-8"))
        if r["tr"] in ("F1", "F2") and r["label"] in ("PF", "TF")]
bugs = sorted({r["bug"] for r in rows})
REG = {"C1": (0.0282, -0.137, 0.274), "C2": (0.2429, 0.114, 0.372)}


def rate(rs, lab, field):
    s = [r for r in rs if r["label"] == lab]
    return sum(bool(r[field]) for r in s) / len(s)


def est(rs, c):
    if c == "C1":
        return rate(rs, "PF", "flip") - rate(rs, "TF", "flip")
    return rate(rs, "TF", "dec") - rate(rs, "PF", "dec")


print(f"n tests {len(rows)}; PF {sum(r['label']=='PF' for r in rows)}; TF {sum(r['label']=='TF' for r in rows)}; bugs (clusters) {len(bugs)}")
for c in ("C1", "C2"):
    full = est(rows, c)
    loo = [est([r for r in rows if r["bug"] != b], c) for b in bugs]
    g = len(loo); mean = sum(loo) / g
    se = math.sqrt((g - 1) / g * sum((x - mean) ** 2 for x in loo))
    lo, hi = full - 1.959964 * se, full + 1.959964 * se
    rp, rlo, rhi = REG[c]
    print(f"{c}: estimate {full:+.4f} (registered {rp:+.4f}); jackknife SE {se:.4f}; normal 95% [{lo:+.3f}, {hi:+.3f}] "
          f"width {hi-lo:.3f} | registered bootstrap [{rlo:+.3f}, {rhi:+.3f}] width {rhi-rlo:.3f}")
