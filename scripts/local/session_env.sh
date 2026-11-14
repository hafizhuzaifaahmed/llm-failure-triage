#!/usr/bin/env bash
# Client-side Python environment for every session (D-73), for Git Bash on Windows. Source it in the shell that runs
# the study's Python entry points, before any of them:
#   source scripts/local/session_env.sh
# PYTHONUTF8=1 makes Python read and write files as UTF-8 regardless of the Windows code page (cp1252 here), which
# the D2 dataset build needs. It is the Python client only: the Ollama server environment stays as frozen in
# configs/local_server_env.json. WSL entry points get the same setting from scripts/wsl/run.sh.
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8
echo "PYTHONUTF8=$PYTHONUTF8 PYTHONIOENCODING=$PYTHONIOENCODING"
