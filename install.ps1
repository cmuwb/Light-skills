#!/usr/bin/env pwsh
# Light installer (Windows / PowerShell)
# Links Light's 27 skills + shared knowledge bases into Claude Code and/or Codex.
# Usage:  pwsh install.ps1            # installs into both clients found
#         pwsh install.ps1 -Client claude
#         pwsh install.ps1 -Client codex

param(
  [ValidateSet('both','claude','codex')]
  [string]$Client = 'both'
)

$ErrorActionPreference = 'Stop'
$Repo = $PSScriptRoot

function Link-Dir($link, $target) {
  if (Test-Path $link) { cmd /c rmdir "$link" 2>$null }
  cmd /c mklink /J "$link" "$target" | Out-Null
}

function Install-Into($skillsDir) {
  $parent = Split-Path $skillsDir -Parent
  New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null
  $n = 0
  Get-ChildItem -Directory "$Repo\skills" -Filter 'light-*' | ForEach-Object {
    Link-Dir "$skillsDir\$($_.Name)" $_.FullName
    if (Test-Path "$skillsDir\$($_.Name)\SKILL.md") { $n++ }
  }
  # shared libraries as siblings so skills' relative paths resolve
  Link-Dir "$parent\databases"   "$Repo\databases"
  Link-Dir "$parent\code_assets" "$Repo\code_assets"
  Write-Host "  $skillsDir  ->  $n/27 skills"
}

if ($Client -in 'both','claude') {
  Write-Host 'Claude Code:'
  Install-Into "$HOME\.claude\skills"
}
if ($Client -in 'both','codex') {
  Write-Host 'Codex:'
  Install-Into "$HOME\.agents\skills"
}
Write-Host 'Done. Restart your client to discover the skills.'
