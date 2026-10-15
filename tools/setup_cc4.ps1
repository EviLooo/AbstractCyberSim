param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
$cc4Pin = '8c3c50ca54b176c2de199847944e8dcc035497e3'
$cc4Checkout = Join-Path $projectRoot '.engine/cc4/checkout'
$cc4Python = Join-Path $projectRoot '.engine/cc4/venv/Scripts/python.exe'
function Check-CC4Exit { param([string]$Operation) if ($LASTEXITCODE -ne 0) { throw "$Operation failed." } }
if (-not (Test-Path -LiteralPath (Join-Path $cc4Checkout '.git'))) {
    git clone https://github.com/cage-challenge/cage-challenge-4.git $cc4Checkout
    Check-CC4Exit 'CC4 clone'
    git -C $cc4Checkout checkout --detach $cc4Pin
    Check-CC4Exit 'CC4 pin'
}
$actualPin = git -C $cc4Checkout rev-parse HEAD
Check-CC4Exit 'CC4 revision check'
if ($actualPin -ne $cc4Pin) { throw 'Existing CC4 checkout differs from the required pin. Preserve its work and configure a separate checkout; this script will not reset it.' }
$cc4Changes = git -C $cc4Checkout status --porcelain
Check-CC4Exit 'CC4 source check'
if ($cc4Changes) { throw 'CC4 source has local changes. Preserve them before setting up the pinned unmodified engine.' }
if (-not (Test-Path -LiteralPath $cc4Python)) {
    & $Python -c 'import sys; assert sys.version_info[:2] == (3, 12), "This CC4 adapter is qualified on Python 3.12"'
    Check-CC4Exit 'CC4 Python selection'
    & $Python -m venv (Join-Path $projectRoot '.engine/cc4/venv')
    Check-CC4Exit 'CC4 virtual environment'
}
& $cc4Python -c 'import sys; assert sys.version_info[:2] == (3, 12), "CC4 requires the qualified Python 3.12 environment"'
Check-CC4Exit 'CC4 interpreter version'
& $cc4Python -m pip install -r engine/cc4.requirements.lock
Check-CC4Exit 'CC4 dependencies'
Write-Host 'CC4 installed in its isolated environment. Select Enterprise · CAGE Challenge 4 in the workbench.'
Write-Host 'Simulator-only dependencies; no RL training stack, provider calls or episodes run.'
