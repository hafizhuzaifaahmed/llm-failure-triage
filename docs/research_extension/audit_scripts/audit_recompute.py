"""Independent read-only recomputation of the CFP confirmation quantities from per-tranche raw records.
Does not import any project module. Own bootstrap, own Holm, own rules."""
import json, sys, math
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

ROOT = Path(sys.argv[1])
def rj(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]

TR = {"F1": "D1C_F1", "F2": "D1C_F2", "CTRL": "D1C_CTRL"}
VOTES = {"F1": {"M1": "LOCAL_CONF_VOTE_M1_F1", "M2": "LOCAL_CONF_VOTE_M2_F1", "M3": "LOCAL_CONF_VOTE_E6B_F1"},
         "F2": {"M1": "LOCAL_CONF_VOTE_M1_F2", "M2": "LOCAL_CONF_VOTE_M2_F2", "M3": "LOCAL_CONF_VOTE_E6B_F2"}}
rows = []
for t, ds in TR.items():
    base = ROOT / "data/extension/confirm" / t
    lab = {r["instance_id"]: r for r in rj(base / f"labels_{ds}.jsonl")}
    ins = {r["instance_id"]: r for r in rj(base / f"instances_{ds}.jsonl")}
    led = {r["instance_id"]: r for r in rj(ROOT / f"results/extension/probes/CFP_CONF_{t}/ledger.jsonl")}
    votes = defaultdict(dict)
    if t in VOTES:
        for m, run in VOTES[t].items():
            for r in rj(base / "votes" / run / "decisions.jsonl"):
                if r.get("replicate") == 80 and r.get("arm") == "J1" and r.get("level") == "S1":
                    votes[r["instance_id"]][m] = r.get("label_raw")
    assert set(lab) == set(ins) == set(led), (t, len(lab), len(ins), len(led))
    for i, l in lab.items():
        s = led[i]["summary"]; c = ins[i].get("covariates", {})
        rows.append(dict(id=i, tr=t, label=l["label"], bug=l["bug_name"], proj=l["project"], focal=l["focal_id"],
                         excl=bool(s.get("excluded")), ncomp=s.get("n_compiled", 0) or 0, nflip=s.get("n_flip", 0) or 0,
                         nshift=s.get("n_shift", 0) or 0, nsame=s.get("n_same", 0) or 0, nerr=s.get("n_err", 0) or 0,
                         flip=bool(s.get("flip")), rcf=bool(s.get("rcf")), dec=bool(s.get("decoupled")),
                         ft=c.get("failure_type"), df=c.get("deepest_frame"), votes=dict(votes.get(i, {})),
                         ff=s.get("flip_fraction"), cf=s.get("coupled_fraction")))
print("== counts per tranche")
for t in TR:
    R = [r for r in rows if r["tr"] == t]
    print(t, len(R), Counter(r["label"] for r in R), "bugs", len({r["bug"] for r in R}),
          "PF-bugs", len({r["bug"] for r in R if r["label"] == "PF"}), "excluded", sum(r["excl"] for r in R),
          "votes3", sum(len(r["votes"]) == 3 for r in R))
ov = {r["bug"] for r in rows if r["tr"] == "F1"} & {r["bug"] for r in rows if r["tr"] == "F2"}
print("bugs in both F1 and F2:", len(ov))

def boot(R, fn, B=10000, seed=777):
    bugs = sorted({r["bug"] for r in R}); bi = np.array([bugs.index(r["bug"]) for r in R])
    rng = np.random.default_rng(seed)
    W = rng.multinomial(len(bugs), np.full(len(bugs), 1 / len(bugs)), size=B).astype(float)[:, bi]
    return fn(np.ones((1, len(R))))[0], fn(W)

def rate_diff(R, key, sign):
    y = np.array([r["label"] == "PF" for r in R], float); f = np.array([bool(r[key]) for r in R], float)
    def fn(W):
        with np.errstate(invalid="ignore", divide="ignore"):
            a = (W * y * f).sum(1) / (W * y).sum(1); b = (W * (1 - y) * f).sum(1) / (W * (1 - y)).sum(1)
        return sign * (a - b)
    pt, d = boot(R, fn); d = d[~np.isnan(d)]
    p = min(1, 2 * min((np.sum(d <= 0) + 1) / (len(d) + 1), (np.sum(d >= 0) + 1) / (len(d) + 1)))
    return round(float(pt), 4), [round(float(np.quantile(d, .025)), 4), round(float(np.quantile(d, .975)), 4)], round(p, 4), len(d)

S = [r for r in rows if r["tr"] in ("F1", "F2") and r["label"] in ("PF", "TF")]
for name, R in (("F1+F2", S), ("F1", [r for r in S if r["tr"] == "F1"]), ("F2", [r for r in S if r["tr"] == "F2"])):
    pf = [r for r in R if r["label"] == "PF"]; tf = [r for r in R if r["label"] == "TF"]
    print(f"== {name}: n={len(R)} PF={len(pf)} TF={len(tf)} bugs={len({r['bug'] for r in R})} PFbugs={len({r['bug'] for r in pf})}")
    print("  flip PF %d/%d TF %d/%d" % (sum(r["flip"] for r in pf), len(pf), sum(r["flip"] for r in tf), len(tf)), "C1", rate_diff(R, "flip", +1))
    print("  dec  PF %d/%d TF %d/%d" % (sum(r["dec"] for r in pf), len(pf), sum(r["dec"] for r in tf), len(tf)), "C2", rate_diff(R, "dec", -1))
    el = [r for r in R if r["ncomp"] >= 10]
    epf = [r for r in el if r["label"] == "PF"]; etf = [r for r in el if r["label"] == "TF"]
    print("  eligible(>=10 compiled) PF %d/%d TF %d/%d; dec|eligible PF %d/%d TF %d/%d" % (
        len(epf), len(pf), len(etf), len(tf), sum(r["dec"] for r in epf), len(epf), sum(r["dec"] for r in etf), len(etf)),
        "C2|eligible", rate_diff(el, "dec", -1) if epf else None)
    print("  ncomp==0: PF %d TF %d ; ncomp median PF %s TF %s" % (sum(r["ncomp"] == 0 for r in pf), sum(r["ncomp"] == 0 for r in tf),
          np.median([r["ncomp"] for r in pf]), np.median([r["ncomp"] for r in tf])))
    print("  rcf PF %d TF %d" % (sum(r["rcf"] for r in pf), sum(r["rcf"] for r in tf)))

# heterogeneity F2 - F1 on C2 and C1 (bugs disjoint -> independent bootstraps)
def bdist(R, key, sign, seed):
    y = np.array([r["label"] == "PF" for r in R], float); f = np.array([bool(r[key]) for r in R], float)
    bugs = sorted({r["bug"] for r in R}); bi = np.array([bugs.index(r["bug"]) for r in R])
    W = np.random.default_rng(seed).multinomial(len(bugs), np.full(len(bugs), 1 / len(bugs)), size=10000).astype(float)[:, bi]
    with np.errstate(invalid="ignore", divide="ignore"):
        return sign * ((W * y * f).sum(1) / (W * y).sum(1) - (W * (1 - y) * f).sum(1) / (W * (1 - y)).sum(1))
for key, sign, nm in (("dec", -1, "C2"), ("flip", +1, "C1")):
    d = bdist([r for r in S if r["tr"] == "F2"], key, sign, 11) - bdist([r for r in S if r["tr"] == "F1"], key, sign, 12)
    d = d[~np.isnan(d)]
    print(f"== heterogeneity {nm}: F2-F1 CI95 [{np.quantile(d,.025):.3f}, {np.quantile(d,.975):.3f}] p={min(1,2*min((np.sum(d<=0)+1)/(len(d)+1),(np.sum(d>=0)+1)/(len(d)+1))):.4f}")

print("== decoupled by failure type / deepest frame (F1+F2)")
for t in ("F1", "F2", "ALL"):
    R = [r for r in S if t == "ALL" or r["tr"] == t]
    tab = defaultdict(lambda: [0, 0, 0, 0])
    for r in R:
        k = (r["ft"], r["df"]); j = 0 if r["label"] == "PF" else 2
        tab[k][j] += 1; tab[k][j + 1] += r["dec"]
    for k in sorted(tab, key=str): print("  ", t, k, "PF n/dec %d/%d  TF n/dec %d/%d" % tuple(tab[k]))

print("== concentration of decoupled TF by bug (F1+F2), top 12")
c = Counter(r["bug"] for r in S if r["dec"] and r["label"] == "TF"); tot = Counter(r["bug"] for r in S if r["label"] == "TF")
print("  bugs with a decoupled TF:", len(c), "of", len(tot), "; top:", [(b, n, tot[b]) for b, n in c.most_common(12)])
print("  decoupled PF:", [(r["bug"], r["tr"], r["focal"], r["ft"], r["df"], r["ncomp"], r["nerr"]) for r in S if r["dec"] and r["label"] == "PF"])
print("  decoupled with n_err>0:", sum(1 for r in S if r["dec"] and r["nerr"] > 0), "; with all-ERR:", sum(1 for r in S if r["dec"] and r["nerr"] == r["ncomp"]))
c = Counter(r["bug"] for r in S if r["flip"] and r["label"] == "TF")
print("  flipping TF: bugs", len(c), "top:", c.most_common(8))
print("  PF by bug:", sorted(Counter(r["bug"] for r in S if r["label"] == "PF").items(), key=lambda x: -x[1]))
print("  PF flip by bug:", sorted(Counter(r["bug"] for r in S if r["label"] == "PF" and r["flip"]).items(), key=lambda x: -x[1]))
print("== by project (F1+F2): proj n PF flipPF TF flipTF decTF")
for p in sorted({r["proj"] for r in S}):
    R = [r for r in S if r["proj"] == p]; pf = [r for r in R if r["label"] == "PF"]; tf = [r for r in R if r["label"] == "TF"]
    print("  ", p, len(R), len(pf), sum(r["flip"] for r in pf), len(tf), sum(r["flip"] for r in tf), sum(r["dec"] for r in tf), "decPF", sum(r["dec"] for r in pf))

# ---------------- rules
PFL, TFL = "PROGRAM_FAULT", "TEST_FAULT"
def k_of_n(vs, k):
    return TFL if sum(v == TFL for v in vs) >= k else PFL
V = [r for r in S if len(r["votes"]) == 3]
print("== votes: with three votes", len(V), "PF", sum(r["label"] == "PF" for r in V), "; missing:", Counter((r["tr"], r["label"]) for r in S if len(r["votes"]) != 3))
print("   raw vote values:", Counter(v for r in V for v in r["votes"].values()))
def keep(r, base, rule):
    b = k_of_n([r["votes"][m] for m in ("M1", "M2", "M3")], 3 if base == "KUU" else 2) if base != "ALL" else PFL
    if "CK" in rule and not r["excl"] and r["rcf"]: return 1
    if "CD" in rule and not r["excl"] and r["dec"]: return 0
    return 1 if b == PFL else 0
def metrics(R, base, rule):
    y = np.array([r["label"] == "PF" for r in R]); k = np.array([keep(r, base, rule) for r in R])
    tpr = k[y].mean(); tnr = (1 - k[~y]).mean(); lost = int((1 - k[y]).sum())
    pfb = {r["bug"] for r in R if r["label"] == "PF"}; keptb = {r["bug"] for r, kk in zip(R, k) if r["label"] == "PF" and kk}
    return round(float(tpr), 4), round(float(tnr), 4), round(float((tpr + tnr) / 2), 4), lost, len(pfb - keptb), len(pfb), int(k.sum()), sorted(pfb - keptb)
for t in ("ALL", "F1", "F2"):
    R = [r for r in V if t == "ALL" or r["tr"] == t]
    print(" --", t, len(R))
    for base, rule in (("KUU", ""), ("KUU", "CD"), ("MAJ", ""), ("MAJ", "CK"), ("KUU", "CK+CD"), ("MAJ", "CK+CD"), ("ALL", "CD")):
        print("   ", base, rule or "-", metrics(R, base, rule))
def ba_diff(R, b0, r0, b1, r1, stat="BA"):
    y = np.array([r["label"] == "PF" for r in R], float); k0 = np.array([keep(r, b0, r0) for r in R], float); k1 = np.array([keep(r, b1, r1) for r in R], float)
    def fn(W):
        def ba(k):
            return ((W * y * k).sum(1) / np.maximum((W * y).sum(1), 1e-12) + (W * (1 - y) * (1 - k)).sum(1) / np.maximum((W * (1 - y)).sum(1), 1e-12)) / 2
        if stat == "BA": return ba(k1) - ba(k0)
        return (W * y * (1 - k1)).sum(1) - (W * y * (1 - k0)).sum(1)
    pt, d = boot(R, fn)
    p = min(1, 2 * min((np.sum(d <= 0) + 1) / (len(d) + 1), (np.sum(d >= 0) + 1) / (len(d) + 1)))
    return round(float(pt), 4), [round(float(np.quantile(d, .025)), 4), round(float(np.quantile(d, .975)), 4)], round(p, 4)
print("C3", ba_diff(V, "KUU", "", "KUU", "CD")); print("C4", ba_diff(V, "MAJ", "", "MAJ", "CK", "LOST"))
# note on degenerate resamples: resamples with no PF bug
bugs = sorted({r["bug"] for r in S}); pfb = np.array([b in {r["bug"] for r in S if r["label"] == "PF"} for b in bugs])
print("P(resample has zero PF bug) ~", (1 - pfb.mean()) ** len(bugs))

# ---------------- control
C = [r for r in rows if r["tr"] == "CTRL"]
ctf = [r for r in C if r["label"] == "TF"]
print("== control:", len(C), Counter(r["label"] for r in C), "bugs", len({r["bug"] for r in C}), "flip TF", sum(r["flip"] for r in ctf), "dec TF", sum(r["dec"] for r in ctf),
      "excluded", sum(r["excl"] for r in C), "elig", sum(r["ncomp"] >= 10 for r in ctf), "ncomp median", np.median([r["ncomp"] for r in ctf]))
def fn(W):
    f = np.array([r["flip"] for r in ctf], float); return (W * f).sum(1) / W.sum(1)
pt, d = boot(ctf, fn); d = d[~np.isnan(d)]
print("   flip rate", round(float(pt), 4), [round(float(np.quantile(d, .025)), 4), round(float(np.quantile(d, .975)), 4)])
print("   control by failure type/frame:", Counter((r["ft"], r["df"], r["dec"]) for r in ctf))
print("   F1/F2 tests in bugs that have a control: PF flip", end=" ")
cb = {r["bug"] for r in C}
R = [r for r in S if r["bug"] in cb]
print(sum(r["flip"] for r in R if r["label"] == "PF"), sum(r["label"] == "PF" for r in R), "TF flip", sum(r["flip"] for r in R if r["label"] == "TF"), sum(r["label"] == "TF" for r in R))

# exact binomial upper bounds
from math import comb
def cp_upper(k, n, a=0.05):
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if sum(comb(n, j) * mid ** j * (1 - mid) ** (n - j) for j in range(k + 1)) > a: lo = mid
        else: hi = mid
    return round(lo, 4)
print("== Clopper-Pearson one-sided 95% upper: ", {k: cp_upper(k, 21) for k in (0, 1, 3, 4)})
print("   decoupled-is-TF: 135/136 tests; bug-level: bugs with a decoupled test", len({r['bug'] for r in S if r['dec']}), "of which carry decoupled PF", len({r['bug'] for r in S if r['dec'] and r['label']=='PF'}))
json.dump(rows, open(Path(sys.argv[2]), "w"))
