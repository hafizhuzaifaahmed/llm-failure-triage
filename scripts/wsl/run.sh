#!/usr/bin/env bash
# Run a project Python entry point inside WSL with the pinned Defects4J environment.
# Usage (from Windows Git Bash or PowerShell):  wsl -d Ubuntu-22.04 -- bash scripts/wsl/run.sh <script.py> [args]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$HERE"
export D4J_HOME="${D4J_HOME:-$HOME/experiment/defects4j}"
export TRIAGE_PERL5LIB="${TRIAGE_PERL5LIB:-$HOME/experiment/perl5/lib/perl5}"
export TRIAGE_WORK="${TRIAGE_WORK:-$HOME/triage_work}"
export PYTHONUTF8=1   # D-73: UTF-8 file I/O whatever the locale (Windows-side equivalent: scripts/local/session_env.*)
exec python3 "$@"
