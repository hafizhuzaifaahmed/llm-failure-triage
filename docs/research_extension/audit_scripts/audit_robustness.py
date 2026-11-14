"""Second read-only pass: robustness of C1/C2, exploratory ranking, cost; uses rows.json from audit1.py."""
import json, sys
from collections import Counter, defaultdict
import numpy as np
rows = json.load(open(sys.argv[1]))
S = [r for r in rows if r["tr"] in ("F1", "F2") and r["label"] in ("PF", "TF")]
y = np.array([r["label"] == "PF" for r in S], float)
dec = np.array([r["dec"] for r in S], float); flip = np.array([r["flip"] for r in S], float)

def clus_boot(R, fn, key, B=10000, seed=5):
    ks = sorted({r[key] for r in R}); ki = np.array([ks.index(r[key]) for r in R])
    W = np.random.default_rng(seed).multinomial(len(ks), np.full(len(ks), 1 / len(ks)), size=B).astype(float)[:, ki]
    d = fn(W); d = d[~np.isnan(d)]
    return [round(float(np.quantile(d, .025)), 3), round(float(np.quantile(d, .975)), 3)], round(float(min(1, 2 * min((np.sum(d <= 0) + 1) / (len(d) + 1), (np.sum(d >= 0) + 1) / (len(d) + 1)))), 4), len(d)
def c2fn(R):
    yy = np.array([r["label"] == "PF" for r in R], float); f = np.array([r["dec"] for r in R], float)
    def fn(W):
        with np.errstate(invalid="ignore", divide="ignore"):
            return (W * (1 - yy) * f).sum(1) / (W * (1 - yy)).sum(1) - (W * yy * f).sum(1) / (W * yy).sum(1)
    return fn
print("C2 project-level cluster bootstrap (12 projects):", clus_boot(S, c2fn(S), "proj"))
# leave-one-project-out with bug-level CI
for p in ("JacksonDatabind", "JacksonCore", "Lang", "Math"):
    R = [r for r in S if r["proj"] != p]
    pt = np.mean([r["dec"] for r in R if r["label"] == "TF"]) - np.mean([r["dec"] for r in R if r["label"] == "PF"])
    print(f"  C2 without {p}: {pt:.3f}", clus_boot(R, c2fn(R), "bug"), "PF", sum(r["label"] == "PF" for r in R), "decTF", sum(r["dec"] for r in R if r["label"] == "TF"))
R = [r for r in S if not r["proj"].startswith("Jackson")]
pt = np.mean([r["dec"] for r in R if r["label"] == "TF"]) - np.mean([r["dec"] for r in R if r["label"] == "PF"])
print(f"  C2 without both Jackson projects: {pt:.3f}", clus_boot(R, c2fn(R), "bug"), "n", len(R), "PF", sum(r["label"] == "PF" for r in R), "decTF", sum(r["dec"] for r in R if r["label"] == "TF"), "decPF", sum(r["dec"] for r in R if r["label"] == "PF"))
# within-project (Mantel-Haenszel style risk difference, weights n_pf*n_tf/n)
num = den = 0
for p in sorted({r["proj"] for r in S}):
    R = [r for r in S if r["proj"] == p]; pf = [r for r in R if r["label"] == "PF"]; tf = [r for r in R if r["label"] == "TF"]
    if pf and tf:
        w = len(pf) * len(tf) / len(R); num += w * (np.mean([r["dec"] for r in tf]) - np.mean([r["dec"] for r in pf])); den += w
print("C2 project-stratified (MH weights) risk difference:", round(num / den, 3))
# jackknife influence over bugs for C2
bugs = sorted({r["bug"] for r in S}); infl = []
full = dec[y == 0].mean() - dec[y == 1].mean()
for b in bugs:
    m = np.array([r["bug"] != b for r in S])
    infl.append((round(float((dec[m & (y == 0)].mean() - dec[m & (y == 1)].mean()) - full), 4), b))
print("C2 jackknife: largest drops", sorted(infl)[:4], "largest rises", sorted(infl)[-3:])
# decoupled bug-level: among bugs with >=1 decoupled test
print("tests in the 6 bugs with most decoupled TF:", sum(1 for r in S if r["bug"] in ("JacksonDatabind_90", "JacksonDatabind_70", "JacksonDatabind_30", "JacksonCore_7", "JacksonDatabind_53", "JacksonDatabind_61") and r["dec"]), "of 136")
# C1 conditional on having >=1 compiled mutant, and bug-level
A = [r for r in S if r["ncomp"] >= 1]
print("flip | ncomp>=1: PF %d/%d TF %d/%d" % (sum(r["flip"] for r in A if r["label"] == "PF"), sum(r["label"] == "PF" for r in A), sum(r["flip"] for r in A if r["label"] == "TF"), sum(r["label"] == "TF" for r in A)))
for t in ("F1", "F2"):
    A2 = [r for r in A if r["tr"] == t]
    print("   ", t, "PF %d/%d TF %d/%d" % (sum(r["flip"] for r in A2 if r["label"] == "PF"), sum(r["label"] == "PF" for r in A2), sum(r["flip"] for r in A2 if r["label"] == "TF"), sum(r["label"] == "TF" for r in A2)))
pfb = defaultdict(list); tfb = defaultdict(list)
for r in S: (pfb if r["label"] == "PF" else tfb)[r["bug"]].append(r)
print("bug level: PF-bearing bugs with a flipping PF test %d/%d; bugs with only TF having any flip %d/%d" % (
    sum(any(r["flip"] for r in v) for v in pfb.values()), len(pfb),
    sum(any(r["flip"] for r in v) for b, v in tfb.items() if b not in pfb), sum(1 for b in tfb if b not in pfb)))
print("zero-mutant PF tests by bug:", Counter(r["bug"] for r in S if r["label"] == "PF" and r["ncomp"] == 0), "; PF with ncomp<10 by bug:", Counter(r["bug"] for r in S if r["label"] == "PF" and r["ncomp"] < 10))

def auc(score, yy):
    s = np.asarray(score, float); yy = np.asarray(yy, bool)
    order = np.argsort(s, kind="mergesort"); ranks = np.empty(len(s));
    # average ranks
    ss = s[order]; i = 0; r = np.empty(len(s))
    while i < len(ss):
        j = i
        while j + 1 < len(ss) and ss[j + 1] == ss[i]: j += 1
        r[i:j + 1] = (i + j) / 2 + 1; i = j + 1
    ranks[order] = r
    n1 = yy.sum(); n0 = (~yy).sum()
    return round(float((ranks[yy].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)), 3)
print("== exploratory ranking (score high = more likely PF), all 572 unless votes needed")
print("  AUROC coupled_fraction:", auc([r["cf"] or 0 for r in S], y), " flip_fraction:", auc([r["ff"] or 0 for r in S], y), " not-decoupled:", auc(1 - dec, y))
V = [r for r in S if len(r["votes"]) == 3]; vy = np.array([r["label"] == "PF" for r in V])
npf = np.array([sum(v == "PROGRAM_FAULT" for v in r["votes"].values()) for r in V], float)
vd = np.array([r["dec"] for r in V], float)
print("  (561) AUROC #PF votes:", auc(npf, vy), "; votes then decoupled demoted:", auc(npf - 0.5 * vd, vy), "; votes, decoupled forced to bottom:", auc(np.where(vd == 1, -1, npf), vy))
for t in ("F1", "F2"):
    m = np.array([r["tr"] == t for r in V])
    print("   ", t, "AUROC votes:", auc(npf[m], vy[m]), " with decoupled bottom:", auc(np.where(vd == 1, -1, npf)[m], vy[m]))
for m in ("M1", "M2", "M3"):
    k = np.array([r["votes"][m] == "PROGRAM_FAULT" for r in V])
    print("  ", m, "TPR", round(float(k[vy].mean()), 3), "TNR", round(float((~k[~vy]).mean()), 3))
print("== judge-call saving if decoupled tests are discarded before judging: %d of %d (%.1f%%); TF among them %d, PF %d" % (int(dec.sum()), len(S), 100 * dec.mean(), int((dec * (1 - y)).sum()), int((dec * y).sum())))
print("   unanimity pattern among decoupled TF (561): #TF-votes", Counter(3 - int(n) for n, d, yy in zip(npf, vd, vy) if d and not yy))
print("   inspection workload: tests kept by KUU %d (PF %d) -> precision %.3f; KUU+CD %d (PF %d) -> %.3f; 2of3 kept precision" % (
    0, 0, 0, 0, 0, 0) if False else "")
def prec(keepfn):
    k = np.array([keepfn(r) for r in V]); return int(k.sum()), int((k & vy).sum()), round(float((k & vy).sum() / k.sum()), 3)
kuu = lambda r: not all(v == "TEST_FAULT" for v in r["votes"].values())
maj = lambda r: sum(v == "TEST_FAULT" for v in r["votes"].values()) < 2
print("   kept (n, PF, precision): keep-all", prec(lambda r: True), "KUU", prec(kuu), "KUU+CD", prec(lambda r: kuu(r) and not r["dec"]), "2of3", prec(maj), "2of3+CD", prec(lambda r: maj(r) and not r["dec"]))
# cheap-feature comparators
for name, f in (("exception & deepest frame not focal", lambda r: r["ft"] == "exception" and r["df"] != "focal"),
                ("exception (any)", lambda r: r["ft"] == "exception"),
                ("decoupled", lambda r: r["dec"]),
                ("decoupled & exception-not-in-focal", lambda r: r["dec"] and r["ft"] == "exception" and r["df"] != "focal"),
                ("decoupled & assertion", lambda r: r["dec"] and r["ft"] == "assertion_failure")):
    print("  discard-if [%s]: PF flagged %d/55, TF flagged %d/517" % (name, sum(f(r) for r in S if r["label"] == "PF"), sum(f(r) for r in S if r["label"] == "TF")))
print("== mutant counts among decoupled: ncomp quartiles", np.percentile([r["ncomp"] for r in S if r["dec"]], [0, 25, 50, 75, 100]), "; decoupled with ncomp<=15:", sum(1 for r in S if r["dec"] and r["ncomp"] <= 15),
      "; TF not decoupled only for lack of mutants (ncomp<10 & no flip/shift):", sum(1 for r in S if r["label"] == "TF" and r["ncomp"] < 10 and r["nflip"] + r["nshift"] == 0), "PF same:", sum(1 for r in S if r["label"] == "PF" and r["ncomp"] < 10 and r["nflip"] + r["nshift"] == 0))
