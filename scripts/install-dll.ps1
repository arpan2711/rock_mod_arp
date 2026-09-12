# Installs the freshly built xinput1_3.dll into the game folder, backing up
# whatever is there now. Rollback is scripts\restore-dll.ps1.

param(
    [string]$GameDir = 'Y:\Rocksmith 2014 Edition - Remastered'
)

$ErrorActionPreference = 'Stop'

$repo  = Split-Path -Parent $PSScriptRoot
$built = Join-Path $repo 'RSMods-src\Installer\Resources\xinput1_3.dll'

if (-not (Test-Path $built))   { throw "No built DLL at $built - run scripts\build-dll.ps1 first." }
if (-not (Test-Path $GameDir)) { throw "Game folder not found: $GameDir" }

# The game holds xinput1_3.dll open while it runs.
$running = Get-Process -Name 'Rocksmith2014' -ErrorAction SilentlyContinue
if ($running) { throw "Rocksmith is running (PID $($running.Id)). Close it first." }

$target  = Join-Path $GameDir 'xinput1_3.dll'
$backups = Join-Path $repo 'backups'
New-Item -ItemType Directory -Force -Path $backups | Out-Null

if (Test-Path $target) {
    $stamp  = Get-Date -Format 'yyyyMMdd-HHmmss'
    $backup = Join-Path $backups "xinput1_3.dll.$stamp"
    Copy-Item $target $backup
    Write-Host "Backed up current DLL -> $backup"

    # Keep a single stable 'the one that shipped with 1.2.7.4' copy for easy rollback.
    $pristine = Join-Path $backups 'xinput1_3.dll.1.2.7.4-original'
    if (-not (Test-Path $pristine)) {
        Copy-Item $target $pristine
        Write-Host "Saved pristine 1.2.7.4 DLL -> $pristine"
    }
}

Copy-Item $built $target -Force
$f = Get-Item $target
Write-Host "Installed: $($f.FullName)  ($('{0:N0}' -f $f.Length) bytes)"
Write-Host ""
Write-Host "RSMods_debug.txt reports the build as 1.2.7.4-arp.N on the first line."
