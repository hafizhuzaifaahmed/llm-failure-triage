"""Small I/O helpers shared by every stage. Stdlib only, so the WSL execution side can import it."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable, Iterator


def sha256_text(text: str) -> str:
    # surrogatepass: identical bytes for any valid string; defined for a lone surrogate (D-69)
    return hashlib.sha256(text.encode("utf-8", "surrogatepass")).hexdigest()


def _jsonl_line(record: dict) -> str:
    """One JSONL line. A lone surrogate (a model's unescaped backslash-uD83D, parsed from its JSON answer) cannot
    be written as UTF-8, so such a record falls back to ASCII escapes -- lossless on read; every other record is
    written exactly as before (D-69)."""
    line = json.dumps(record, ensure_ascii=False, sort_keys=True)
    try:
        line.encode("utf-8")
    except UnicodeEncodeError:
        line = json.dumps(record, ensure_ascii=True, sort_keys=True)
    return line


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path) -> Iterator[dict]:
    if not Path(path).exists():
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def append_jsonl(path: Path, record: dict) -> None:
    """Append one record and fsync, so an interrupted run never loses a paid call."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(_jsonl_line(record) + "\n")
        f.flush()
        os.fsync(f.fileno())


def write_jsonl(path: Path, records: Iterable[dict]) -> int:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(_jsonl_line(r) + "\n")
            n += 1
    return n


def write_immutable(path: Path, text: str) -> None:
    """Raw artefacts are written once. Re-writing identical content is a no-op; different content is an error."""
    path = Path(path)
    if path.exists():
        if path.read_text(encoding="utf-8") != text:
            raise FileExistsError(f"refusing to overwrite immutable raw artefact {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def dump_json(path: Path, obj: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
