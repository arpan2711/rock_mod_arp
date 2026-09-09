# Builds the RSMods DLL (xinput1_3.dll) only - not the C# GUI or Installer.
#
# Release|Win32 is mandatory: Rocksmith2014.exe is 32-bit, an x64 build will not load.
#
# The vendored project asks for PlatformToolset v142 (VS2019). This machine has
# Visual Studio Build Tools 2026 (MSVC 14.51, toolset v145) instead, so we retarget
# on the command line rather than editing the vendored .vcxproj.

$ErrorActionPreference = 'Stop'

$repo = Split-Path -Parent $PSScriptRoot
$sln  = Join-Path $repo 'RSMods-src\RSMods.sln'

$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
if (-not (Test-Path $vswhere)) { throw "vswhere.exe not found - is Visual Studio (or Build Tools) installed?" }

$vs = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (-not $vs) { throw "No VS install with the C++ toolset ('Desktop development with C++')." }

$msbuild = Join-Path $vs 'MSBuild\Current\Bin\MSBuild.exe'
if (-not (Test-Path $msbuild)) { throw "MSBuild.exe not found under $vs" }

Write-Host "MSBuild:  $msbuild"
Write-Host "Solution: $sln"
Write-Host ""

& $msbuild $sln `
    -t:DLL `
    -p:Configuration=Release `
    -p:Platform=Win32 `
    -p:PlatformToolset=v145 `
    -p:WindowsTargetPlatformVersion=10.0.26100.0 `
    -m `
    -v:minimal `
    -nologo

if ($LASTEXITCODE -ne 0) { throw "Build failed with exit code $LASTEXITCODE" }

# The project's post-build step copies the DLL here.
$dll = Join-Path $repo 'RSMods-src\Installer\Resources\xinput1_3.dll'

Write-Host ""
if (Test-Path $dll) {
    $f = Get-Item $dll
    Write-Host "Built: $($f.FullName)  ($('{0:N0}' -f $f.Length) bytes, $($f.LastWriteTime))"
    Write-Host "Install it with: scripts\install-dll.ps1"
} else {
    Write-Warning "Build reported success but xinput1_3.dll was not found where expected."
}
