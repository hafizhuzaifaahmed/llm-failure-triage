"""A8 (P2a, read-only): sealing chronology of the confirmation from git history and the run logs.

Commit times are author/committer times recorded by git; they are not proof of when a file was written.
"""
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
COMMITS = {"1a58e54": "labels sealed", "b332305": "probe ledgers", "ef3e064": "judge votes",
           "6a26c2a": "vote logs", "3b017f2": "analysis"}
LABELS = [f"data/extension/confirm/{t}/labels_D1C_{t}.jsonl" for t in ("F1", "F2", "CTRL")]
LEDGERS = [f"results/extension/probes/CFP_CONF_{t}/ledger.jsonl" for t in ("F1", "F2", "CTRL")]


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def utc(iso):
    return datetime.fromisoformat(iso).astimezone(timezone.utc)


def log_times(path, kind, which):
    pat = re.compile(rf"=== {kind} .* {which} (\S+Z)")
    return [datetime.fromisoformat(m.group(1).replace("Z", "+00:00"))
            for m in map(pat.search, (ROOT / path).read_text(encoding="utf-8").splitlines()) if m]


def main():
    t = {}
    print("| commit | role | author date | committer date | committer (UTC) |\n|---|---|---|---|---|")
    for c, role in COMMITS.items():
        ad, cd = git("show", "-s", "--format=%aI|%cI", c).split("|")
        t[c] = utc(cd)
        print(f"| {c} | {role} | {ad} | {cd} | {t[c].isoformat()} |")
    p_start = min(log_times("results/extension/confirm_logs/probes.log", "PROBE", "start"))
    p_end = max(log_times("results/extension/confirm_logs/probes.log", "PROBE", "end"))
    v_start = min(log_times("results/extension/confirm_logs/votes.log", "VOTE", "start"))
    print(f"\nfirst PROBE start {p_start.isoformat()}; last PROBE end {p_end.isoformat()}; "
          f"first VOTE start {v_start.isoformat()}")
    checks = {"labels commit (1a58e54) precedes first probe start": t["1a58e54"] < p_start,
              "ledger commit (b332305) precedes first vote start": t["b332305"] < v_start}
    head_order = git("rev-list", "--reverse", "HEAD").splitlines()

    def later_than(sealing, path):
        hashes = git("log", "--format=%H", "--", path).splitlines()
        seal = git("rev-parse", sealing)
        return [h[:7] for h in hashes if head_order.index(h) > head_order.index(seal)]
    for f in LABELS:
        print(f"git log --oneline -- {f}:\n  " + git("log", "--oneline", "--", f).replace("\n", "\n  "))
        checks[f"no commit after 1a58e54 touches {f}"] = not later_than("1a58e54", f)
    for f in LEDGERS:
        print(f"git log --oneline -- {f}:\n  " + git("log", "--oneline", "--", f).replace("\n", "\n  "))
        checks[f"no commit after b332305 touches {f}"] = not later_than("b332305", f)
    diff = git("diff", "3b017f2", "--stat", "--", *LABELS, *LEDGERS)
    checks["git diff 3b017f2 --stat over label and ledger files is empty"] = diff == ""
    print()
    for k, v in checks.items():
        print(f"{'PASS' if v else 'FAIL'}  {k}")
    print(f"A8 checks {len(checks)}; failures {sum(not v for v in checks.values())}")


if __name__ == "__main__":
    main()
