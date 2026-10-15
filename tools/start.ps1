param([int]$Port = 8787)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
$servicePython = Join-Path $projectRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $servicePython)) { throw 'Run tools/setup.ps1 first.' }
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'frontend/dist/index.html'))) { throw 'Run npm run build --prefix frontend first.' }
Write-Host "AbstractCyberSim workbench: http://127.0.0.1:$Port"
Write-Host 'The service starts idle. It does not run experiments or make model calls.'
& $servicePython -m backend.app.cli serve --port $Port
if ($LASTEXITCODE -ne 0) { throw 'Workbench service failed. Check the port and console output.' }
