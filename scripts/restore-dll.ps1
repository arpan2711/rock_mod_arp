# Puts the original RSMods 1.2.7.4 xinput1_3.dll back. Instant rollback.

param(
    [string]$GameDir = 'Y:\Rocksmith 2014 Edition - Remastered'
)

$ErrorActionPreference = 'Stop'

$repo     = Split-Path -Parent $PSScriptRoot
$pristine = Join-Path $repo 'backups\xinput1_3.dll.1.2.7.4-original'

if (-not (Test-Path $pristine)) { throw "No pristine backup at $pristine" }

$running = Get-Process -Name 'Rocksmith2014' -ErrorAction SilentlyContinue
if ($running) { throw "Rocksmith is running (PID $($running.Id)). Close it first." }

Copy-Item $pristine (Join-Path $GameDir 'xinput1_3.dll') -Force
Write-Host "Restored the original RSMods 1.2.7.4 DLL."
