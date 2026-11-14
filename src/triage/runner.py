"""Experiment orchestration: conditions x instances x replicates, concurrent, resumable.

A condition is (arm, level, variant, model). Decisions are appended to
results/runs/<run>/decisions.jsonl; a (instance, arm, level, variant, model, replicate) tuple already
present is skipped, and completed LLM calls are served from the content-addressed call log on resume
(see llm.py for the crash cases in which a request can still be sent, and charged, twice).
The runner reads instances, specs and the leakage guard — never the label store. Every evidence package is
checked against the guard BEFORE any LLM call; a hit is logged to leakage_rejections.jsonl and no call is made.
"""
from __future__ import annotations

import hashlib
import json
import random
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from . import arms, config
from .context_builder import LeakageError, build_package, leakage_check
from .io_utils import append_jsonl, dump_json, read_jsonl
from .llm import BudgetExceeded, DeferredCall, LLMClient, ProviderMismatch, StopRequested
from .scope import ScopeViolation
from .ollama import ContextOverflow, DigestMismatch, ResidencyLost
from .prompts import PromptSet

LLM_ARMS = {"J1", "SC", "SC-T", "DEB", "A1", "A2"}


def load_specs(path: Path) -> dict:
    return {r["focal_id"]: r["spec"] for r in read_jsonl(path) if r.get("valid")}


ORDER_BATCH = 8
SEED_ORDER = 20261031


def order_tasks(tasks: list, batch: int = ORDER_BATCH, seed: int = SEED_ORDER) -> list:
    """D-28: instances in a seeded random order, processed in batches; within a batch every arm/level/replicate
    task of those instances is interleaved in a seeded random order. Arms are therefore never run in separate
    blocks of time, so session or thermal effects cannot line up with arm comparisons. Deterministic, so a
    resumed run follows the same order (completed tasks are skipped by decision key)."""
    rng = random.Random(seed)
    ids = sorted({t[0]["instance_id"] for t in tasks})
    rng.shuffle(ids)
    batch_of = {iid: i // batch for i, iid in enumerate(ids)}
    keyed = []
    for t in tasks:
        tie = hashlib.sha256(f"{seed}|{t[0]['instance_id']}|{t[1]}|{t[2]}|{t[3]}|{t[4]}".encode()).hexdigest()
        keyed.append((batch_of[t[0]["instance_id"]], tie, t))
    return [t for _, _, t in sorted(keyed, key=lambda x: (x[0], x[1]))]


def decision_key(d: dict) -> tuple:
    return (d["instance_id"], d["arm"], d.get("level"), d.get("variant"), d.get("model"), d["replicate"])


class Runner:
    def __init__(self, run_dir: Path, client: LLMClient | None, prompts: PromptSet | None, model_id: str | None,
                 specs: dict | None = None, specs_prime: dict | None = None, workers: int = 16,
                 forbidden: dict | None = None, require_guard: bool = True):
        self.run_dir = Path(run_dir)
        self.out = self.run_dir / "decisions.jsonl"
        self.err = self.run_dir / "errors.jsonl"
        self.client, self.prompts, self.model_id = client, prompts, model_id
        self.specs, self.specs_prime = specs or {}, specs_prime or {}
        self.workers = workers
        self.forbidden = forbidden or {}
        self.require_guard = require_guard
        self.rejections = self.run_dir / "leakage_rejections.jsonl"
        self.done = {decision_key(d) for d in read_jsonl(self.out)}
        self._lock = threading.Lock()
        self.stop = False

    def package_for(self, inst: dict, level: str, variant: str):
        inst = dict(inst)
        if level == "S2" or variant == "specprime":
            inst["spec"] = self.specs.get(inst["focal_id"])
        override = self.specs_prime.get(inst["focal_id"]) if variant == "specprime" else None
        pkg = build_package(inst, level, include_failure=(variant != "noF"), include_impl=(variant == "impl"),
                            spec_override=override)
        extra = []
        if variant != "impl":  # body lines (not the signature line, which [Sig] legitimately contains)
            body = inst.get("impl", "")
            body = body[body.find("{") + 1:] if "{" in body else ""
            extra = [l.strip() for l in body.split("\n") if len(l.strip()) >= 25]
        exempt = inst.get("impl") if variant == "impl" else None   # D-72: B's own body is not an F-only leak
        hits = leakage_check(pkg.text, self.forbidden.get(inst["instance_id"]), extra, exempt_body=exempt)
        return pkg, hits

    def one(self, inst: dict, arm: str, level: str | None, variant: str, rep: int, k: int | None) -> dict:
        iid = inst["instance_id"]
        if arm in ("DA", "KA"):
            return arms.policy_arm(iid, arm)
        if arm == "R0":
            return arms.r0_arm(inst)
        if self.require_guard and iid not in self.forbidden:
            raise LeakageError(f"no leakage-guard entry for {iid}; refusing to call a model without one")
        pkg, hits = self.package_for(inst, level, variant)
        if hits:
            raise LeakageError(f"leakage check failed for {iid}: {hits[:3]}")
        if arm == "J1":
            d = arms.j1_arm(iid, pkg, self.client, self.prompts, self.model_id, rep)
        elif arm == "SC":
            d = arms.sc_arm(iid, pkg, self.client, self.prompts, self.model_id, config.SC_SAMPLES, rep)
        elif arm == "SC-T":
            d = arms.sc_arm(iid, pkg, self.client, self.prompts, self.model_id, k, rep, arm_name="SC-T")
        else:
            d = arms.deb_arm(iid, pkg, self.client, self.prompts, self.model_id, rep, variant=arm)
        d["package"] = {"approx_tokens": pkg.approx_tokens, "truncated": pkg.truncated, "has_javadoc": pkg.has_javadoc}
        d["variant"] = variant
        return d

    def run(self, instances: list[dict], conditions: list[dict], replicates: int, max_tasks: int | None = None):
        tasks = []
        for c in conditions:
            arm = c["arm"]
            reps = 1 if arm in ("DA", "KA", "R0") else c.get("replicates", replicates)
            # D-90: a condition may name its replicate indices (E8's fresh J1 calls use indices no committed run used)
            rep_list = c["replicate_indices"] if arm in LLM_ARMS and c.get("replicate_indices") else range(reps)
            for level in c.get("levels", [None]):
                for inst in instances:
                    for rep in rep_list:
                        key = (inst["instance_id"], arm, level if arm in LLM_ARMS else None,
                               c.get("variant", "full") if arm in LLM_ARMS else None,
                               self.model_id if arm in LLM_ARMS else None, rep)
                        if key not in self.done:
                            tasks.append((inst, arm, level, c.get("variant", "full"), rep, c.get("k")))
        tasks = order_tasks(tasks)
        if max_tasks:
            tasks = tasks[:max_tasks]
        print(f"{len(tasks)} decisions to compute ({len(self.done)} already done)", flush=True)
        t0, n = time.time(), 0
        self.deferred = 0
        with ThreadPoolExecutor(self.workers) as ex:
            futs = {ex.submit(self.one, *t): t for t in tasks}
            for f in as_completed(futs):
                t = futs[f]
                try:
                    d = f.result()
                    if d["arm"] in ("DA", "KA", "R0"):
                        d.update(level=None, variant=None, model=None)
                    d["utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    with self._lock:
                        append_jsonl(self.out, d)
                        self.done.add(decision_key(d))
                except LeakageError as e:
                    append_jsonl(self.rejections, {"instance_id": t[0]["instance_id"], "arm": t[1], "level": t[2],
                                                   "variant": t[3], "replicate": t[4], "reason": str(e)[:500]})
                except DeferredCall:          # D-96: queued for the next frontier batch; a later pass completes it
                    self.deferred += 1
                    continue
                except StopRequested as e:
                    print("STOPPED ON REQUEST (D-58):", e, flush=True)
                    ex.shutdown(wait=True, cancel_futures=True)
                    break
                except (BudgetExceeded, ProviderMismatch, ScopeViolation, DigestMismatch, ResidencyLost) as e:
                    print(f"STOPPING RUN ({type(e).__name__}):", e, flush=True)
                    append_jsonl(self.err, {"instance_id": t[0]["instance_id"], "fatal": type(e).__name__,
                                            "error": str(e)[:500]})
                    ex.shutdown(wait=False, cancel_futures=True)
                    break
                except Exception as e:
                    append_jsonl(self.err, {"instance_id": t[0]["instance_id"], "arm": t[1], "level": t[2],
                                            "variant": t[3], "replicate": t[4], "error": f"{type(e).__name__}: {e}",
                                            "trace": traceback.format_exc()[-1500:]})
                n += 1
                if n % 200 == 0:
                    print(f"  {n}/{len(tasks)}  {time.time() - t0:.0f}s", flush=True)
        dump_json(self.run_dir / "run_status.json", {"decisions": len(self.done), "finished_utc":
                                                     time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
