# install.ps1
# Installs/updates this Copilot customization pack into $HOME\.copilot.
#
# Coverage:
# - agents
# - skills
# - prompts
# - MCPservers
# - instructions
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\install.ps1
#
# Safe by design:
# - It only copies known customization folders.
# - It does NOT delete unrelated files in $HOME\.copilot.
# - Same-named files are overwritten with the source version.

$ErrorActionPreference = 'Stop'

$sourceRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$targetRoot = [System.IO.Path]::GetFullPath((Join-Path $env:USERPROFILE '.copilot'))

Write-Host "Installing Copilot customizations" -ForegroundColor Cyan
Write-Host "  Source: $sourceRoot" -ForegroundColor DarkCyan
Write-Host "  Target: $targetRoot" -ForegroundColor DarkCyan

$foldersToManage = @('agents', 'skills', 'prompts', 'MCPservers', 'instructions')

# Always ensure canonical folders exist in $HOME\.copilot
foreach ($folder in $foldersToManage) {
    New-Item -ItemType Directory -Force (Join-Path $targetRoot $folder) | Out-Null
}

if ($sourceRoot -ieq $targetRoot) {
    Write-Host "" 
    Write-Host "Source is already the canonical .copilot folder. No copy required." -ForegroundColor Green
    Write-Host "Verified folders: $($foldersToManage -join ', ')" -ForegroundColor Green
} else {
    foreach ($folder in $foldersToManage) {
        $src = Join-Path $sourceRoot $folder
        $dst = Join-Path $targetRoot $folder

        if (Test-Path $src) {
            Copy-Item (Join-Path $src '*') $dst -Recurse -Force
            Write-Host "  + $folder copied" -ForegroundColor Green
        } else {
            Write-Warning "  ! '$folder' not found in source, skipped"
        }
    }
}

Write-Host ""
Write-Host "Done. Reload VS Code so Copilot re-scans customizations." -ForegroundColor Yellow
Write-Host "This setup supports: Agent, Skills, Prompts, and MCP server." -ForegroundColor Yellow
