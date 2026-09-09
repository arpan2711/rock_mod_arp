# rock_mod_arp

Rocksmith 2014 Remastered as a guitar-learning tool: a patched RSMods build, the
song-library manager, and the config that makes startup fast and the UI clean.

Game install lives at `Y:\Rocksmith 2014 Edition - Remastered\`. This repo is the
source of truth for everything hand-made; the game folder is where it gets deployed.

| Path | What it is |
|---|---|
| `RSMods-src/` | RSMods 1.2.7.4 fork source (`keremcanb/RSMods_for_Cracked_Rocksmith_2014` @ `9a63acd`) with the 1.2.8.x fixes ported in |
| `scripts/` | Build, install, rollback, and the game-folder batch files |
| `SongManager/` | Local web app for enabling/disabling songs in `dlc\` (pure-stdlib Python) |
| `config/` | Snapshots of the deployed `RSMods.ini`, `Rocksmith.ini`, `steam_emu.ini` |
| `backups/` | DLL backups made by `install-dll.ps1` (untracked) |
| `ROCKSMITH-PROJECT-NOTES.md` | Full setup and troubleshooting history |

## Build and install

```powershell
scripts\build-dll.ps1     # Release|Win32 -> RSMods-src\Installer\Resources\xinput1_3.dll
scripts\install-dll.ps1   # backs up the current DLL, then copies the new one in
scripts\restore-dll.ps1   # rollback to the original 1.2.7.4 DLL
```

Close Rocksmith first — it holds `xinput1_3.dll` open, and the install script
refuses to run while the game is up.

**Release|Win32 is mandatory.** `Rocksmith2014.exe` is 32-bit; an x64 build will
not load. The vendored project targets PlatformToolset v142 (VS2019); this machine
has Visual Studio Build Tools 2026 (MSVC 14.51, toolset v145), so `build-dll.ps1`
retargets on the command line rather than editing the vendored `.vcxproj`.

Only the `DLL` project is built. The C# GUI (`RSMods.exe`) and Installer are left
at their shipped 1.2.7.4 binaries.

## What was ported from 1.2.8.x

1.2.8.x is a large refactor — the 73 KB `dllmain.cpp` monolith was split into
`GameState` / `Keyboard` / `ModManager`, so upstream cannot be merged wholesale.
These are cherry-picked into the 1.2.7.4 structure instead.

| Fix | From | Effect |
|---|---|---|
| Uplay login dialog auto-dismissed | 1.2.8.x | No more pressing Escape twice at startup |
| Alt-Tab white-screen semi-crash | 1.2.8.4 | Fixes the crash with "show current note" on |
| Calibration above 100 FPS | 1.2.8.4 | Calibration completes without capping framerate |
| `PreventMidSongPause` | 1.2.8.2 | Optional: tabbing away mid-song no longer pauses it |

Each is one commit, with the reasoning in the commit message.

`RSMods_debug.txt` still reports `1.2.7.4` — the version string is deliberately
unchanged, since this is 1.2.7.4 plus patches, not an upstream release.

## New setting

```ini
[Toggle Switches]
PreventMidSongPause=on
```

Default is `off` (stock behaviour). There is no GUI checkbox for it — adding one
means editing the 480 KB generated `GUI/UI.Designer.cs`. Note that `RSMods.exe`
rewrites `RSMods.ini` when it saves, so it may drop this hand-added key; re-add it
after using the GUI.

## Upstream

- Fork (this baseline): https://github.com/keremcanb/RSMods_for_Cracked_Rocksmith_2014
- Upstream: https://github.com/Lovrom8/RSMods — fixes taken from tag
  `RSModsInstaller-v1.2.8.4_OnCommit`
