#!/usr/bin/env bash
# Record the execution environment (deviation X-04 replaces a Docker digest with this manifest).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
D4J="${D4J_HOME:-$HOME/experiment/defects4j}"
jv=$(java -version 2>&1 | head -1 | sed 's/"/\\"/g')
jc=$(javac -version 2>&1)
os=$(. /etc/os-release && echo "$PRETTY_NAME")
k=$(uname -r)
tag=$(cd "$D4J" && git describe --tags)
commit=$(cd "$D4J" && git rev-parse HEAD)
py=$(python3 --version)
perl=$(perl -e 'print $^V')
cpu=$(nproc); mem=$(free -g | awk '/Mem:/{print $2}')
cat > "$HERE/env/environment_manifest.json" <<JSON
{
  "recorded_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "os": "$os (WSL2 kernel $k)",
  "java_runtime": "$jv",
  "javac": "$jc",
  "defects4j_tag": "$tag",
  "defects4j_commit": "$commit",
  "python_execution_side": "$py",
  "perl": "$perl",
  "wsl_cpus": $cpu,
  "wsl_mem_gib": $mem,
  "tz": "America/Los_Angeles",
  "junit_runner_jar": "junit-4.12-hamcrest-1.3.jar (Defects4J lib)",
  "python_env": {"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", "decision": "D-73", "set_by": "scripts/local/session_env.ps1 or .sh (Windows client, every session); scripts/wsl/run.sh (WSL)"}
}
JSON
cat "$HERE/env/environment_manifest.json"
