"""Scope lock for paid runs, read from configs/budget.json (the file whose creation constitutes approval).

    {"approved_usd": 16, "scope": "dev_pilot",
     "allowed_splits": ["dev"], "allowed_experiments": ["PILOT_dev"],
     "allowed_models": ["deepseek/deepseek-chat-v3-0324", "openai/gpt-4.1"],
     "require_pinned_no_fallback": true}

Every paid entry point (generate_tests, infer_specs, run_experiment) and the LLM client check it:
- a context or instance whose split is not allowed is refused before any prompt is built;
- an experiment whose name is not allowed is refused;
- a model not in allowed_models is refused;
- a dataset not in allowed_datasets is refused (absent -> D1 only: D2 and D3 must be listed explicitly);
- routing must name one provider (`only`) with `allow_fallbacks: false`;
- the provider that actually served a call must be the pinned one, otherwise the run stops.
Mock and replay runs need no budget file and are not scope-checked (they cannot spend).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

from . import config

BUDGET_FILE = config.ROOT / "configs" / "budget.json"


class ScopeViolation(RuntimeError):
    pass


@dataclass
class Scope:
    approved_usd: float
    name: str = ""
    allowed_splits: list = field(default_factory=list)
    allowed_experiments: list = field(default_factory=list)
    allowed_models: list = field(default_factory=list)
    require_pinned_no_fallback: bool = True
    allowed_datasets: list = field(default_factory=lambda: ["D1"])

    def check_dataset(self, dataset: Optional[str], what: str = "") -> None:
        if dataset not in self.allowed_datasets:
            raise ScopeViolation(f"dataset {dataset!r} is outside the approved scope {self.allowed_datasets} {what}".strip())

    def check_split(self, split: Optional[str], what: str = "") -> None:
        if split not in self.allowed_splits:
            raise ScopeViolation(f"split {split!r} is outside the approved scope {self.allowed_splits} {what}".strip())

    def check_items(self, items: Iterable[dict], what: str) -> int:
        n = 0
        for it in items:
            self.check_split(it.get("split"), f"({what} {it.get('instance_id') or it.get('focal_id')})")
            n += 1
        return n

    def check_experiment(self, name: str) -> None:
        if name not in self.allowed_experiments:
            raise ScopeViolation(f"experiment {name!r} is not in the approved scope {self.allowed_experiments}")

    def check_model(self, model_id: str, routing: Optional[dict], local: bool = False) -> None:
        if model_id not in self.allowed_models:
            raise ScopeViolation(f"model {model_id!r} is not in the approved scope {self.allowed_models}")
        if local:  # local server: no providers/fallbacks; the weights must be digest-pinned instead
            if not routing or not routing.get("digest"):
                raise ScopeViolation(f"local model {model_id} has no pinned digest")
            return
        if self.require_pinned_no_fallback:
            if not routing or routing.get("allow_fallbacks") is not False or len(routing.get("only") or []) != 1:
                raise ScopeViolation(f"routing for {model_id} must pin exactly one provider with fallbacks disabled")


def load(path: Path = BUDGET_FILE) -> Optional[Scope]:
    if not Path(path).exists():
        return None
    b = json.loads(Path(path).read_text(encoding="utf-8"))
    for k in ("allowed_splits", "allowed_experiments", "allowed_models"):
        if not b.get(k):
            raise ScopeViolation(f"{path} must define a non-empty {k!r}")
    # approved_usd is meaningful only for paid scopes (the paid client separately requires it to be > 0)
    return Scope(float(b.get("approved_usd", 0.0)), b.get("scope", ""), list(b["allowed_splits"]),
                 list(b["allowed_experiments"]), list(b["allowed_models"]), bool(b.get("require_pinned_no_fallback", True)),
                 list(b.get("allowed_datasets") or ["D1"]))


def require(path: Path = BUDGET_FILE) -> Scope:
    s = load(path)
    if s is None:
        raise ScopeViolation(f"{path} is missing: paid runs are not approved")
    return s


LOCAL_SCOPE_FILE = config.ROOT / "configs" / "local_scope.json"


def check_focal_ids_local(focal_ids: Iterable[str], what: str, path: Path = LOCAL_SCOPE_FILE) -> int:
    """Execution-side lock (no LLM involved): while a local scope file exists, every focal method must belong to
    an allowed split, read from its context file; an unknown focal method is refused, not assumed dev.
    A D2 id (`<focal_id>#m<mutant>`) additionally needs D2 in allowed_datasets and takes its base method's split."""
    sc = load(path)
    if sc is None:
        return 0
    split_of = {}
    for cp in (config.INTERIM / "context").glob("*.json"):
        c = json.loads(cp.read_text(encoding="utf-8"))
        split_of[c["focal_id"]] = c["split"]
    n = 0
    for fid in focal_ids:
        if "#m" in fid:
            sc.check_dataset("D2", f"({what} {fid})")
        sc.check_split(split_of.get(fid.split("#m", 1)[0]), f"({what} {fid})")
        n += 1
    return n

