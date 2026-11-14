"""OSF deposit package for the CFP confirmation (D-140). Nothing here contacts OSF: the authors deposit by hand.

    python scripts/extension/osf_package.py bundle
        -> docs/research_extension/osf_deposit/  (registration text, frozen files, manifests, SHA256SUMS, one zip)
    python scripts/extension/osf_package.py record --osf-id <id> --url <url> --utc <YYYY-MM-DDTHH:MM:SSZ> --decision D-xxx
        -> configs/extension/osf_registration.json  (refuses to overwrite; stores the hash of the registered text)

`record` is run only after the authors have deposited the registration and given its identifier and timestamp.
The readiness gate then requires the registered text to equal the repository's text, hash for hash.
"""
import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "research_extension" / "osf_deposit"
PREREG = ROOT / "docs" / "research_extension" / "OSF_PREREGISTRATION_CFP.md"
REGISTRATION = ROOT / "configs" / "extension" / "osf_registration.json"
FILES = ["docs/research_extension/OSF_PREREGISTRATION_CFP.md", "docs/research_extension/CONTROL_GROUP.md",
         "docs/research_extension/generated/power_planning.md", "configs/extension/cfp_frozen.json",
         "configs/extension/confirm_frame.jsonl", "configs/extension/confirm_frame_summary.json",
         "configs/extension/confirm_dataset_manifest.json", "configs/extension/confirm_runs.json",
         "src/triage_ext/mutate.py", "src/triage_ext/probe.py", "src/triage_ext/ledger.py", "src/triage_ext/policy.py",
         "scripts/extension/run_probes_tranche.py", "scripts/extension/confirm_analysis.py",
         "scripts/extension/build_confirm_frames.py", "scripts/extension/confirm_contexts.py",
         "scripts/extension/confirm_gate.py", "scripts/extension/confirm_generate.py",
         "scripts/extension/power_planning.py", "results/extension/planning/power_planning.json",
         "scripts/extension/confirm_lib.py", "scripts/extension/confirm_pipeline.py",
         "configs/extension/conf_e6b_profile.json"] +         [f"configs/extension/experiments/LOCAL_CONF_VOTE_{m}_{t}.json" for t in ("F1", "F2") for m in ("M1", "M2", "E6B")]


def content_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def bundle():
    OUT.mkdir(parents=True, exist_ok=True)
    lines = [f"{content_hash(ROOT / f)}  {f}" for f in FILES]
    (OUT / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    z = OUT / "cfp_confirmation_frozen_bundle.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in FILES:                                   # fixed timestamps: the archive is reproducible
            info = zipfile.ZipInfo(f, date_time=(2026, 11, 11, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, (ROOT / f).read_bytes().replace(b"\r\n", b"\n"))
        info = zipfile.ZipInfo("SHA256SUMS.txt", date_time=(2026, 11, 11, 0, 0, 0))
        zf.writestr(info, "\n".join(lines) + "\n")
    print("registration text sha256:", content_hash(PREREG))
    print("bundle:", z, hashlib.sha256(z.read_bytes()).hexdigest())


def record(a):
    if REGISTRATION.exists():
        sys.exit(f"{REGISTRATION} exists; a registration record is not rewritten")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", a.utc):
        sys.exit("--utc must look like 2026-11-12T09:30:00Z")
    if not a.url.startswith("https://osf.io/"):
        sys.exit("--url must be an https://osf.io/ address")
    rec = {"osf_id": a.osf_id, "url": a.url, "registered_utc": a.utc, "recorded_in_decision": a.decision,
           "registration_doc": "docs/research_extension/OSF_PREREGISTRATION_CFP.md",
           "registration_doc_sha256": content_hash(PREREG),
           "hash_method": "sha256 of file bytes with CRLF normalised to LF"}
    REGISTRATION.write_text(json.dumps(rec, indent=1), encoding="utf-8", newline="\n")
    print("recorded", REGISTRATION)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("bundle")
    r = sub.add_parser("record")
    r.add_argument("--osf-id", required=True)
    r.add_argument("--url", required=True)
    r.add_argument("--utc", required=True)
    r.add_argument("--decision", required=True)
    a = ap.parse_args()
    bundle() if a.cmd == "bundle" else record(a)


if __name__ == "__main__":
    main()
