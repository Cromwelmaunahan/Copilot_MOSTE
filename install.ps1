# install.ps1
# Copies the Super MOS TE agent + skills from this repo into your
# personal GitHub Copilot folder (%USERPROFILE%\.copilot), where Copilot reads them.
#
# Usage (from the cloned repo folder):
#   powershell -ExecutionPolicy Bypass -File .\install.ps1
#
# Safe by design: it only copies the 'agents' and 'skills' folders shipped here.
# It does NOT delete your other agents/skills. Same-named items are overwritten.

$ErrorActionPreference = 'Stop'

$repo   = $PSScriptRoot
$target = Join-Path $env:USERPROFILE '.copilot'

Write-Host "Installing Copilot_MOSTE ->" $target -ForegroundColor Cyan

# Ensure destination folders exist
New-Item -ItemType Directory -Force (Join-Path $target 'agents') | Out-Null
New-Item -ItemType Directory -Force (Join-Path $target 'skills') | Out-Null

# Copy agent(s)
$srcAgents = Join-Path $repo 'agents'
if (Test-Path $srcAgents) {
    Copy-Item (Join-Path $srcAgents '*') (Join-Path $target 'agents') -Recurse -Force
    Write-Host "  + agents copied" -ForegroundColor Green
} else {
    Write-Warning "  ! no 'agents' folder found in repo"
}

# Copy skill(s)
$srcSkills = Join-Path $repo 'skills'
if (Test-Path $srcSkills) {
    Copy-Item (Join-Path $srcSkills '*') (Join-Path $target 'skills') -Recurse -Force
    Write-Host "  + skills copied" -ForegroundColor Green
} else {
    Write-Warning "  ! no 'skills' folder found in repo"
}

Write-Host ""
Write-Host "Done. Now RESTART / RELOAD VS Code so Copilot re-scans." -ForegroundColor Yellow
Write-Host "Then open Copilot Chat -> the 'Super MOS TE' agent should appear." -ForegroundColor Yellow
