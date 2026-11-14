# Client-side Python environment for every session (D-73). Dot-source it in the shell that runs the study's Python
# entry points, before any of them:
#   . scripts\local\session_env.ps1
# PYTHONUTF8=1 makes Python read and write files as UTF-8 regardless of the Windows code page (cp1252 here), which
# the D2 dataset build needs. It is the Python client only: the Ollama server environment stays as frozen in
# configs/local_server_env.json.
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
Write-Output "PYTHONUTF8=$env:PYTHONUTF8 PYTHONIOENCODING=$env:PYTHONIOENCODING"
