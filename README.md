# rock_mod_arp

Rocksmith 2014 Remastered as a guitar-learning tool: a patched RSMods build, the
song-library manager, and the config that makes startup fast and the UI clean.

Game install: `Y:\Rocksmith 2014 Edition - Remastered\`. This repo is the source of
truth for everything hand-made; the game folder is where it gets deployed.

---

## STATUS — 9 Sep 2026

**Installed right now:** the patched DLL built from the amp-source-toggle commit
(branch `mod-update-1.2.8.x`).

| File | SHA-256 | What it is |
|---|---|---|
| `Y:\...\xinput1_3.dll` | `bb0454c8 72ef20b7 ead0b988 02a08a29 d709a2c6 9a38dcee 29fdf6c4 478daf56` | **patched build, currently installed** |
| `backups\xinput1_3.dll.1.2.7.4-original` | `fc7c44e1 35a6717f a6f44f7d abc1d960 f86a931c 7cebef92 4af5dbde 4ed6976f` | **the original — rollback target** |
| `backups\xinput1_3.dll.20260909-134102` | same as original | timestamped copy of the same file |

**Smoke test (9 Sep):** game launches with the new DLL. `RSMods_debug.txt` from that
run shows:

- `(BUG PREVENTION) Fixed Calibration At High Framerates` — the hook-site byte check
  passed and the calibration hook is placed
- all the usual bug-prevention lines present, so the DLL loaded and initialised
- **zero** `Invalid Pointer: GetCurrentMenu` errors (the previous log had ~14)
- still reports `1.2.7.4` — expected, version string deliberately unchanged

**Full testing has NOT been done yet.** See the checklist below.

---

## ROLLBACK — read this first if anything is wrong

Close Rocksmith (it holds `xinput1_3.dll` open), then:

```powershell
scripts\restore-dll.ps1
```

That copies `backups\xinput1_3.dll.1.2.7.4-original` over the game's `xinput1_3.dll`.
It refuses to run while the game is up.

**Manual version** if PowerShell will not cooperate — it is only a file copy:

```
copy /Y "C:\Users\arpan\rock_mod_arp\backups\xinput1_3.dll.1.2.7.4-original" "Y:\Rocksmith 2014 Edition - Remastered\xinput1_3.dll"
```

**Verify the rollback took** — the game's DLL should hash to `fc7c44e1…`:

```powershell
Get-FileHash 'Y:\Rocksmith 2014 Edition - Remastered\xinput1_3.dll' -Algorithm SHA256
```

**Nuclear option** (run the game with no RSMods at all, e.g. to prove a problem is the
mod and not the game): `scripts\Test without RSMods.bat` renames the DLL away;
`scripts\Restore RSMods.bat` puts it back. Both live in the game folder too.

Nothing else on disk was changed by the install. `cache.psarc`, `RSMods.ini`,
`Rocksmith.ini`, `steam_emu.ini` are all as they were (see
`ROCKSMITH-PROJECT-NOTES.md` §4 for *their* backups — `cache.bak`, `*.ini.bak`).

---

## Testing checklist

Do these in order. Tick them off here as they pass.

- [x] Game launches, DLL loads, `RSMods_debug.txt` updates *(9 Sep)*
- [x] `RSMods_debug.txt` shows `Fixed Calibration At High Framerates` *(9 Sep)*
- [ ] **Uplay prompt** clears on its own at startup, lands on profile `arps` at the main menu
- [ ] **Alt-Tab out of a song** with "show current note" on — no white screen, game
      recovers when you tab back
- [ ] **Calibration** at the monitor's real refresh rate (no FPS cap) — the meter fills
      and calibration completes
- [ ] **`PreventMidSongPause`** — add `PreventMidSongPause=on` under `[Toggle Switches]`
      in `RSMods.ini`, start a song, Alt-Tab: song keeps playing. *(Optional; off by
      default, so this is only tested if you want the feature.)*
- [x] **Amp source toggle** — press `\` mid-song: the game's guitar tone drops out,
      backing track keeps playing, `PEDAL ONLY` shows top-left. Press again to
      bring the virtual amp back. *(11 Sep — works; see the input-device note below)*
- [ ] A normal practice session — loops (`[` `]`), rewind (`-`), RR speed (`=`) all
      still behave as in `ROCKSMITH-PROJECT-NOTES.md` §0

**If a step fails:** roll back (above), then note *which* step in this file. Each fix
is its own commit, so a failing one can be reverted individually with
`git revert <hash>` and rebuilt — the others stay.

| Fix | Commit |
|---|---|
| Uplay login dialog | `fa38c0a` |
| Alt-Tab white-screen | `cb57043` |
| Calibration > 100 FPS | `f616620` |
| PreventMidSongPause | `efd1863` + `c0817e0` |

---

## Repo layout

| Path | What it is |
|---|---|
| `RSMods-src/` | RSMods 1.2.7.4 fork source (`keremcanb/RSMods_for_Cracked_Rocksmith_2014` @ `9a63acd`) with the 1.2.8.x fixes ported in |
| `scripts/` | `build-dll.ps1`, `install-dll.ps1`, `restore-dll.ps1`, plus the game-folder batch files |
| `SongManager/` | Local web app for enabling/disabling songs in `dlc\` (pure-stdlib Python) |
| `config/` | Snapshots of the deployed `RSMods.ini`, `Rocksmith.ini`, `steam_emu.ini` |
| `backups/` | DLL backups made by `install-dll.ps1` — **untracked, do not delete** |
| `ROCKSMITH-PROJECT-NOTES.md` | Full setup and troubleshooting history |

Every commit is authored `arpan2711 <arpan.uon@gmail.com>`; git identity is set
locally in this repo as well as globally.

---

## Build and install

```powershell
scripts\build-dll.ps1     # Release|Win32 -> RSMods-src\Installer\Resources\xinput1_3.dll
scripts\install-dll.ps1   # backs up the current DLL (timestamped + pristine), then installs
scripts\restore-dll.ps1   # rollback to the pristine 1.2.7.4 DLL
```

Close Rocksmith first; the install and restore scripts refuse to run while it is up.

**Release|Win32 is mandatory.** `Rocksmith2014.exe` is 32-bit; an x64 build will not
load. The vendored project targets PlatformToolset v142 (VS2019); this machine has
**Visual Studio Build Tools 2026** (MSVC 14.51, toolset v145, Windows SDK 10.0.26100)
so `build-dll.ps1` retargets on the command line rather than editing the vendored
`.vcxproj`. No Visual Studio Community install was needed.

Only the `DLL` project is built. The C# GUI (`RSMods.exe`) and Installer stay at their
shipped 1.2.7.4 binaries. Build output goes to `Installer\Resources\`, **not**
`Release\`. Expect ~17 pre-existing warnings and no errors.

The CRT is statically linked — the built DLL imports exactly the same 8 system DLLs as
the original, so the toolset jump added no VC redistributable dependency.

---

## What was ported from 1.2.8.x

1.2.8.x is a large refactor — the 73 KB `dllmain.cpp` monolith was split into
`GameState` / `Keyboard` / `ModManager` plus ~35 new files — so upstream cannot be
merged wholesale. These were cherry-picked into the 1.2.7.4 structure instead, one
commit each, 114 lines across 8 files. The reasoning is in each commit message.

| Fix | From | Effect |
|---|---|---|
| Uplay login dialog auto-dismissed | 1.2.8.x | No more pressing Escape twice at startup |
| Alt-Tab white-screen semi-crash | 1.2.8.4 | Fixes the crash with "show current note" on |
| Calibration above 100 FPS | 1.2.8.4 | Calibration completes without capping framerate |
| `PreventMidSongPause` | 1.2.8.2 | Optional: tabbing away mid-song no longer pauses it |

**Why upstream's Remastered offsets are trusted here:** three offsets the fork already
defines for this exe — `ptr_disableTrueTuning 0x004DCCF2`, `ptr_WindowNotInFocusValue
0xEC5D46`, `ptr_sampleRateBuffer 0x1251A9C` — are identical to upstream's
`RemasteredSeptember2022` slot values. Same build, same addresses. On top of that the
calibration hook verifies the 10 bytes it steals before patching (upstream hooks
blindly); the exe is Steam-stub packed so this cannot be checked on disk.

**Review (9 Sep):** all four re-verified after the fact — runtime imports, auto-load
gating vs upstream, `songModes` parity, ImGui frame balance, hook stack discipline. One
defect found and fixed (`c0817e0`): the fork hands messages to ImGui at the *end* of
`WndProc`, so `PreventMidSongPause` was swallowing `WM_KILLFOCUS` before ImGui could
clear its key-down state. Known trade-off inherited from upstream: any yes/no dialog
that appears *before* the main menu gets Escape+Enter spammed.

`RSMods_debug.txt` still reports `1.2.7.4` — the version string is deliberately
unchanged, since this is 1.2.7.4 plus patches, not an upstream release.

---

## New setting

```ini
[Toggle Switches]
PreventMidSongPause=on
```

Default `off` (stock behaviour). No GUI checkbox — adding one means editing the 480 KB
generated `GUI/UI.Designer.cs`. **`RSMods.exe` rewrites `RSMods.ini` when it saves, so
it may drop this hand-added key; re-add it after using the GUI.**

---

## Amp source toggle — the `\` key

One key flips between hearing Rocksmith's virtual amp and hearing only your own
pedalboard. Default bind is `\` (`VK_OEM_5`), which sits next to the loop keys
`[` `]` so it is reachable without looking.

```ini
[Audio Keybindings]
ToggleAmpSourceKey = VK_OEM_5
```

**What it does:** mutes and unmutes the Wwise RTPC `Mixer_Player1` — the game's
processed guitar tone. `Mixer_Music` is untouched, so the backing track keeps playing
in both modes. Works in menus and mid-song, and is *not* gated behind
`VolumeControl=on`.

**On screen:** `PEDAL ONLY` stays in the top-left for as long as the game amp is
muted; `GAME AMP` flashes for three seconds when you switch back. It draws one line
below the volume overlay so the two never collide.

**The rig this is for:** guitar → NUX MG-300 MK2 → amp (that is the "pedalboard"
sound in the room), and MG-300 → USB → PC → desk speakers (that is where Rocksmith's
audio comes out).

| Mode | Desk speakers | Your amp |
|---|---|---|
| `GAME AMP` | backing track **+ Rocksmith's virtual amp** | still making noise |
| `PEDAL ONLY` | backing track only | your actual tone |

**Input device gotcha (found 11 Sep):** without RS_ASIO the game takes its guitar signal
from the *Windows default recording device*. A webcam (`Microphone (Anker PowerConf C200)`)
had become the default, so `GAME AMP` was amplifying the webcam and the toggle looked
broken. Set **Line (NUX Audio)** as the default input before launching, or install RS_ASIO
to pin it. `MutePlayer` now logs the captured volume and never restores to 0.

**Known limit:** the PC cannot silence your physical amp, so in `GAME AMP` mode you
hear both unless you turn the amp (or the MG-300's master) down yourself. If the
MG-300 MK2 accepts MIDI CC over USB, the mod could send it a mute or bypass on the
same key — RSMods already has MIDI-out plumbing for tuning pedals (`Mods/Midi.cpp`).
Not attempted yet; the pedal's MIDI support has not been confirmed.

---

## Ideas backlog — things to add ourselves

Ranked for a practice tool. Effort is a guess.

| # | Idea | Effort | Hangs off |
|---|---|---|---|
| 1 | **Version string bump** so `RSMods_debug.txt` says `1.2.7.4-arp.N` | 1 line | `_RSMODS_VERSION` macro, `dllmain.cpp:16` |
| 2 | **Gate the Crowd Control server** behind `CrowdControlEnabled=off` — 3 threads + a TCP listener for Twitch, started unconditionally | small | `Initialize()` → `CrowdControl::StartServer()`; note it also applies the scroll-speed patch, keep that |
| 3 | **Loop pass counter + auto speed ladder** — overlay `Loop 1:12–1:20 · pass 4 · 82%`; after N passes bump speed by `RRSpeedInterval` | medium | `loopStart`/`loopEnd`, `RiffRepeater::GetSpeed/SetSpeed`, `MemHelpers::DX9DrawText`; loop-wrap seek at `dllmain.cpp:~981` is the "pass done" event |
| 4 | **Port `DisplayCurrentAccuracy`** from 1.2.8.2 — live accuracy % in-song; also what #3 needs to gate on "clean pass" | medium | upstream `NoteData.h` + `ptr_noteData` (Remastered `0x00F5F62C`, rebased on `baseHandle`) |
| 5 | **Practice log** — CSV of `timestamp, song key, speed, loop bounds, accuracy`; Song Manager shows last-practised / minutes per song (the thing the profile decrypt failure blocked) | small DLL, medium SongManager | song-key change detection at `dllmain.cpp:107` |
| 6 | **GUI checkbox for `PreventMidSongPause`** added programmatically in `UI.cs` | small-medium | closes the "RSMods.exe drops the key" caveat |

Suggested order: 1 and 2 now (trivial, zero risk), then 4 → 3 → 5 as one arc.

Not worth it: auto-loop by song section (needs phrase-boundary offsets — real reverse
engineering); metronome (unclear whether Wwise exposes a click).

---

## Upstream

- Fork (this baseline): https://github.com/keremcanb/RSMods_for_Cracked_Rocksmith_2014
- Upstream: https://github.com/Lovrom8/RSMods — fixes taken from tag
  `RSModsInstaller-v1.2.8.4_OnCommit`
