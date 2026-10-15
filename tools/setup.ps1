param([string]$ServicePython = 'python', [string]$EnginePython = '')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
function Check-NativeExit { param([string]$Operation) if ($LASTEXITCODE -ne 0) { throw "$Operation failed." } }
if (-not (Test-Path -LiteralPath 'CybORG/CybORG/env.py')) {
    git submodule update --init CybORG
    Check-NativeExit 'CybORG checkout'
}
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    & $ServicePython -m venv .venv
    Check-NativeExit 'Service virtual environment'
}
$workbenchPython = Join-Path $projectRoot '.venv/Scripts/python.exe'
& $workbenchPython -c 'import sys; assert sys.version_info >= (3, 12), "Service requires Python 3.12+"'
Check-NativeExit 'Service Python version'
& $workbenchPython -m pip install -r requirements-service.lock
Check-NativeExit 'Service dependency installation'
& $workbenchPython -m pip install --no-deps -e .
Check-NativeExit 'Workbench installation'
& $workbenchPython tools/patch_engine.py
Check-NativeExit 'Reviewed engine source patch'
if (-not $EnginePython) {
    $engineDefault = Join-Path $env:USERPROFILE 'anaconda3/envs/cyborg38/python.exe'
    if (Test-Path -LiteralPath $engineDefault) { $EnginePython = $engineDefault }
}
if ($EnginePython) {
    & $EnginePython -c 'import sys; assert sys.version_info[:2] == (3, 8), "Engine requires Python 3.8"'
    Check-NativeExit 'Engine Python version'
    & $EnginePython -m pip install -r engine/requirements.lock
    Check-NativeExit 'Engine dependencies'
    & $EnginePython -m pip install --no-deps -e CybORG
    Check-NativeExit 'Editable engine installation'
    $env:CYBORG_PYTHON = (Resolve-Path -LiteralPath $EnginePython).Path
} else {
    Write-Warning 'No Python 3.8 engine interpreter found. Create the engine environment described in README, then set CYBORG_PYTHON.'
}
npm ci --prefix frontend
Check-NativeExit 'Frontend dependencies'
npm run build --prefix frontend
Check-NativeExit 'Frontend build'
Write-Host 'Installed. Start with ./tools/start.ps1. No simulations or experiments were run.'
