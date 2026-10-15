param([string]$ServicePython = 'python', [string]$CC4Python = '')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
function Check-SetupExit { param([string]$Operation) if ($LASTEXITCODE -ne 0) { throw "$Operation failed." } }
$serviceInterpreter = Join-Path $projectRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $serviceInterpreter)) {
    & $ServicePython -c 'import sys; assert sys.version_info >= (3, 12), "Service needs Python 3.12+"'
    Check-SetupExit 'Service interpreter'
    & $ServicePython -m venv (Join-Path $projectRoot '.venv')
    Check-SetupExit 'Service environment'
}
& $serviceInterpreter -m pip install -e '.[dev,analysis]'
Check-SetupExit 'Service and analysis dependencies'
if (-not $CC4Python) { $CC4Python = $ServicePython }
& (Join-Path $PSScriptRoot 'setup_cc4.ps1') -Python $CC4Python
Push-Location (Join-Path $projectRoot 'frontend')
try {
    npm ci
    Check-SetupExit 'Frontend dependencies'
    npm run build
    Check-SetupExit 'Frontend build'
} finally { Pop-Location }
Write-Host 'Research workbench ready. No simulation episodes or model calls were run.'
Write-Host '.venv/Scripts/python.exe -m backend.app.cli serve --port 8787'
