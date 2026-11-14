"""Prompt sets: load, render, hash. A frozen set lives in prompts/frozen/<name>/ with MANIFEST.json."""
from __future__ import annotations

import json
from pathlib import Path

from . import config
from .io_utils import sha256_text

REQUIRED = ("judge", "advocate_p_r1", "advocate_t_r1", "advocate_r2", "advocate_r2_noexchange",
            "debater_neutral_r1", "debater_neutral_r2", "adjudicator", "spec_inferencer",
            "spec_inferencer_from_body", "generator")


class PromptSet:
    def __init__(self, directory: Path):
        self.dir = Path(directory)
        self.templates = {p.stem: p.read_text(encoding="utf-8") for p in sorted(self.dir.glob("*.txt"))}
        missing = [r for r in REQUIRED if r not in self.templates]
        if missing:
            raise FileNotFoundError(f"prompt set {self.dir} lacks {missing}")

    @classmethod
    def named(cls, name: str) -> "PromptSet":
        for base in (config.PROMPTS / "frozen", config.PROMPTS / "dev"):
            if (base / name).is_dir():
                return cls(base / name)
        raise FileNotFoundError(name)

    def render(self, name: str, **kw) -> str:
        return self.templates[name].format(**kw)

    def hashes(self) -> dict[str, str]:
        return {k: sha256_text(v) for k, v in self.templates.items()}

    def set_hash(self) -> str:
        return sha256_text(json.dumps(self.hashes(), sort_keys=True))
