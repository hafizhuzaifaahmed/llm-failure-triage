"""Stage the public release (D-82): a clean export of the committed tree, checked for secrets and size.

    python scripts/release/stage_release.py            -> dist/release/github/   (push this to GitHub)
                                                          dist/release/zenodo_extra_files.txt (files over the GitHub limit)
    python scripts/release/stage_release.py --zenodo   -> also dist/release/zenodo_<commit>.zip (everything, for the DOI)

The export is `git archive HEAD`, so only committed files go out (never the model blobs, local .env files or scratch).
Excluded from the GitHub folder: files over 95 MB (listed for Zenodo), raw Ollama pull logs and runtime caches.
A secrets scan runs over the staged files and stops the script on any hit.
"""
import argparse
import hashlib
import io
import re
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "dist" / "release"
LIMIT = 95 * 1024 * 1024
# docs/source_documents/ holds the course's assignment briefs: not ours to publish (authors, 9 Nov)
EXCLUDE_PREFIX = ("archive/", "logs/ollama_pull/", "mmlc.log", "docs/source_documents/")
# held back until the label audit is scored (v1.0); published with --with-audit (v1.1): the blind rater kit, the
# sealed LLM rater and the hidden execution-label key would let anyone see or bias the audit before it is scored
AUDIT_HOLD = ("docs/audits/kit/", "data/ground_truth_store/audit/", "docs/audits/label_audit_rater_")


def is_env_file(name: str) -> bool:
    """D-97: a .env file (the E9 key file is env/.env) is never staged, even if it were ever committed."""
    base = name.rsplit("/", 1)[-1]
    return base == ".env" or base.startswith(".env.") or base.endswith(".env")
SECRET = re.compile(rb"(sk-[A-Za-z0-9_-]{20,}|sk-ant-[A-Za-z0-9_-]{20,}|sk-or-v1-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,}"
                    rb"|github_pat_[A-Za-z0-9_]{30,}|gho_[A-Za-z0-9]{30,}|(?:ANTHROPIC_API_KEY|ZENODO_[A-Z_]*TOKEN)\s*=\s*[\"']?[A-Za-z0-9_-]{8,}"
                    rb"|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY-----|xox[baprs]-[A-Za-z0-9-]{10,})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zenodo", action="store_true")
    ap.add_argument("--with-audit", action="store_true")
    a = ap.parse_args()
    skip = EXCLUDE_PREFIX if a.with_audit else EXCLUDE_PREFIX + AUDIT_HOLD
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout.strip():
        print("warning: uncommitted changes are NOT in the export (git archive HEAD)")
    tar = subprocess.run(["git", "archive", "--format=tar", "HEAD"], cwd=ROOT, capture_output=True).stdout
    gh = DIST / "github"
    if gh.exists():
        shutil.rmtree(gh)
    gh.mkdir(parents=True)
    big, hits, n, listed = [], [], 0, []
    with tarfile.open(fileobj=io.BytesIO(tar)) as tf:
        for m in tf.getmembers():
            if not m.isfile() or m.name.startswith(skip):
                continue
            if is_env_file(m.name):
                hits.append(m.name + " (.env file)")
                continue
            data = tf.extractfile(m).read()
            if SECRET.search(data):
                hits.append(m.name)
            if m.size > LIMIT:
                big.append((m.name, m.size, hashlib.sha256(data).hexdigest()))
                continue
            p = gh / m.name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            n += 1
            listed.append((m.name, m.size))
    if hits:
        shutil.rmtree(gh)
        sys.exit("SECRET-LIKE STRINGS FOUND, export removed:\n  " + "\n  ".join(hits))
    (DIST / "zenodo_extra_files.txt").write_text(
        "# files over the GitHub limit: publish with the Zenodo archive (sha256)\n"
        + "".join(f"{name}\t{size}\t{sha}\n" for name, size, sha in big), encoding="utf-8")
    held = "included" if a.with_audit else "held back"
    (DIST / "FILE_LIST.txt").write_text(f"# commit {commit}; audit material {held}\n"
                                        + "".join(f"{name}\t{size}\n" for name, size in sorted(listed)), encoding="utf-8")
    print(f"commit {commit}: {n} files staged in {gh}; {len(big)} over the limit (Zenodo only); secrets scan clean; "
          f"audit material {'included' if a.with_audit else 'held back'}; list in {DIST / 'FILE_LIST.txt'}")
    if a.zenodo:
        z = DIST / f"zenodo_{commit}.zip"
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf, tarfile.open(fileobj=io.BytesIO(tar)) as tf:
            for m in tf.getmembers():
                if m.isfile() and not m.name.startswith(skip) and not is_env_file(m.name):
                    zf.writestr(m.name, tf.extractfile(m).read())
        print("zenodo archive", z, z.stat().st_size)


if __name__ == "__main__":
    main()
