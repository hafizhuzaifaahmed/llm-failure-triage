"""D-42 — recompute the `imports` field of context files with the fixed `javasrc.imports_of` (static imports keep
their `static ` prefix). Only the `imports` field changes; every other field is left byte-identical. Runs in WSL
(Defects4J checkouts of B).

    wsl -d Ubuntu-22.04 -- bash scripts/wsl/run.sh scripts/local/repair_context_imports.py --split dev

The local scope lock applies: `--split test` is refused while configs/local_scope.json allows only dev. After the
authors approve the held-out run, the same command with `--split test` is a required pre-run step (it reads the
held-out B sources to rebuild their import lists; nothing is generated, executed or judged).
Writes results/<split>/import_repair.json listing every changed context.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from triage import config, frame, javasrc, scope  # noqa: E402
from triage.io_utils import dump_json  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "test"], required=True)
    a = ap.parse_args()
    sc = scope.load(scope.LOCAL_SCOPE_FILE)
    if sc is not None:
        sc.check_split(a.split, "(context import repair)")
    fr = {r["focal_id"]: r for r in map(json.loads, open(config.PROCESSED / "frame_d1.jsonl", encoding="utf-8"))}
    changed, unchanged = [], 0
    for cp in sorted((config.INTERIM / "context").glob("*.json")):
        ctx = json.loads(cp.read_text(encoding="utf-8"))
        if ctx["split"] != a.split:
            continue
        rec = fr[ctx["focal_id"]]
        wb = frame.checkout_version(rec["project"], rec["bug"], "b")
        new = javasrc.imports_of((wb / rec["file"]).read_text(errors="replace"))
        old = ctx.get("imports", [])
        if new == old:
            unchanged += 1
            continue
        if [i.replace("static ", "", 1) for i in new] != old:   # only the static prefix may differ
            raise SystemExit(f"{ctx['focal_id']}: import list differs beyond the static prefix; not touching it")
        ctx["imports"] = new
        dump_json(cp, ctx)
        changed.append({"focal_id": ctx["focal_id"], "file": cp.name,
                        "static_imports": [i for i in new if i.startswith("static ")]})
    out = {"split": a.split, "changed": len(changed), "unchanged": unchanged, "contexts": changed}
    dump_json(config.ROOT / "results" / a.split / "import_repair.json", out)
    print(json.dumps({k: out[k] for k in ("split", "changed", "unchanged")}))


if __name__ == "__main__":
    main()
