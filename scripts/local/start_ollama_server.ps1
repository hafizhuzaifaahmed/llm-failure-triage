# Start the Ollama server for the study with the frozen server environment (never the tray app: the tray app
# runs the auto-updater, and the runtime must not change after the freeze).
#   powershell -ExecutionPolicy Bypass -File scripts\local\start_ollama_server.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$cfgPath = Join-Path $root "configs\local_server_env.json"
$cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
foreach ($p in $cfg.env.PSObject.Properties) { Set-Item -Path ("env:" + $p.Name) -Value $p.Value }
Get-Process -Name "ollama app" -ErrorAction SilentlyContinue | Stop-Process -Force -Confirm:$false
if (Get-Process -Name "ollama" -ErrorAction SilentlyContinue) { Write-Output "an ollama server is already running; stop it first to apply the environment"; exit 1 }
$logDir = Join-Path $root "logs\ollama_server"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$exe = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
Start-Process -FilePath $exe -ArgumentList "serve" -WindowStyle Hidden `
  -RedirectStandardError (Join-Path $logDir "server_$stamp.err.log") -RedirectStandardOutput (Join-Path $logDir "server_$stamp.out.log")
Start-Sleep -Seconds 8
(Invoke-RestMethod http://127.0.0.1:11434/api/version).version
