"""Launch the four WDP retrospective evaluation runs within the D-151 window (WSL entry point).

Not part of the frozen WDP code: it only invokes the frozen driver `scripts/extension/run_wdp_tranche.py`.

    wsl -d Ubuntu-22.04 -- bash scripts/wsl/run.sh scripts/extension/wdp_run_window.py

D-151 rules implemented here:
  * exactly one invocation of the driver per evaluation run, in a fixed order; no retry and no resumption, whatever
    the outcome of a run;
  * every run must finish by 2026-11-14 18:00 +05:00 (13:00 UTC): each invocation gets a timeout ending at that
    moment, and a run whose turn comes after it is not started;
  * a run that is stopped or fails keeps its partial outputs; it is marked incomplete in
    results/extension/wdp/run_status.json, and the frozen analysis must then not be run.
Stdout and stderr of each invocation go to results/extension/wdp/run_logs/<RUN>.log.
"""
import datetime as dt
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "extension"))
import run_wdp_tranche as drv  # noqa: E402  (the frozen driver's own run bindings; nothing in it is changed)

WINDOW_END = dt.datetime(2026, 11, 14, 13, 0, 0, tzinfo=dt.timezone.utc)      # 18:00 +05:00
ORDER = ("WDP_D1_TEST", "WDP_CONF_F1", "WDP_CONF_F2", "WDP_CONF_CTRL")
OUT = ROOT / "results" / "extension" / "wdp"
LOGS = OUT / "run_logs"
STATUS = OUT / "run_status.json"


def now():
    return dt.datetime.now(dt.timezone.utc)


def expected_ids(run):
    b = drv.RUNS[run]
    ids = []
    with open(ROOT / b["instances"], encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                if b["split"] is None or r.get("split") == b["split"]:
                    ids.append(r["instance_id"])
    return ids


def ledger_ids(run):
    p = OUT / run / "ledger.jsonl"
    if not p.exists():
        return []
    out = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    out.append(json.loads(line)["instance_id"])
                except (ValueError, KeyError, TypeError):
                    out.append(None)
    return out


def main():
    assert not STATUS.exists(), "run_status.json exists: the runs were already launched once (no retry under D-151)"
    for run in ORDER:
        assert not (OUT / run).exists(), f"{run} already has outputs (no retry under D-151)"
    LOGS.mkdir(parents=True, exist_ok=True)
    status = {"decision": "D-151", "window_end_utc": WINDOW_END.isoformat(), "invocations_per_run": 1, "runs": {}}
    for run in ORDER:
        rec = {"run": run}
        remaining = (WINDOW_END - now()).total_seconds()
        if remaining <= 0:
            rec.update(started=False, reason="window closed before this run's turn", complete=False)
        else:
            b = drv.RUNS[run]
            cmd = [sys.executable, str(ROOT / "scripts" / "extension" / "run_wdp_tranche.py"), "--run", run,
                   "--instances", b["instances"], "--frame", b["frame"], "--exec-dir", b["exec_dir"],
                   "--cand-dir", b["cand_dir"]] + (["--split", b["split"]] if b["split"] is not None else [])
            rec.update(started=True, command=cmd[1:], utc_start=now().isoformat(), timeout_s=int(remaining))
            with open(LOGS / f"{run}.log", "w", encoding="utf-8") as log:
                p = subprocess.Popen(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    rec["exit_code"] = p.wait(timeout=remaining)
                    rec["timed_out"] = False
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid, signal.SIGKILL)                       # the driver and every JVM it started
                    p.wait()
                    rec["exit_code"], rec["timed_out"] = None, True
            rec["utc_end"] = now().isoformat()
        exp, got = expected_ids(run), ledger_ids(run)
        rec.update(instances_expected=len(exp), records=len(got), duplicated=len(got) - len(set(got)),
                   missing=len(set(exp) - set(got)), extra=len(set(got) - set(exp)))
        rec["complete"] = bool(rec.get("started") and rec.get("exit_code") == 0 and not rec.get("timed_out")
                               and rec["records"] == rec["instances_expected"] and rec["missing"] == 0
                               and rec["duplicated"] == 0 and rec["extra"] == 0)
        status["runs"][run] = rec
        STATUS.write_text(json.dumps(status, indent=1) + "\n", encoding="utf-8")
        print(json.dumps({k: rec[k] for k in ("run", "started", "complete", "records", "instances_expected")
                          if k in rec}), flush=True)
    status["all_complete"] = all(r["complete"] for r in status["runs"].values())
    status["frozen_analysis_may_run"] = status["all_complete"]
    STATUS.write_text(json.dumps(status, indent=1) + "\n", encoding="utf-8")
    print("all_complete:", status["all_complete"], flush=True)


if __name__ == "__main__":
    main()
