# rock_mod_arp

Rocksmith 2014 Remastered as a guitar-learning tool: a patched RSMods build, the
song-library manager, and the config that makes startup fast and the UI clean.

Game install: `Y:\Rocksmith 2014 Edition - Remastered\`. This repo is the source of
truth for everything hand-made; the game folder is where it gets deployed.

---

## STATUS — 11 Sep 2026 (evening)

**Installed right now** (branch `mod-update-1.2.8.x`, HEAD `cf0e208`):

| Thing | State | Since |
|---|---|---|
| `Y:\...\xinput1_3.dll` | accuracy-overlay build, commit `1055e23`, SHA-256 `ab7e5eec c48942e8 bbec3ca3 55f87a75 1c12441e 1d8d5ec4 ef63837b 2ebdc674` | 11 Sep 22:31 |
| RS_ASIO v0.7.5 | `avrt.dll` + `RS_ASIO.dll` + `RS_ASIO.ini` in the game folder; input `NUX Audio` ch 0, output WASAPI, **64-sample buffer** | 11 Sep |
| `Rocksmith.ini` | `LatencyBuffer=2` (was 4); everything else as before | 11 Sep |
| `RSMods.ini` | `ToggleAmpSourceKey = VK_OEM_5`, `DisplayCurrentAccuracy = on` added; nothing removed | 11 Sep |
| In-game calibration | redone on the ASIO input path, on the usual NUX preset | 11 Sep |
| Windows default input | still the webcam — **irrelevant now**, RS_ASIO binds the NUX by name | — |

Every deployed config file has a byte-identical snapshot under `config/`. To see what any
of them looked like at an earlier point: `git show <commit>:config/Rocksmith.ini`.

**Tested and good (11 Sep):** the `\` amp-source toggle; RS_ASIO input at 512, 128 and 256
samples; the accuracy overlay in Learn A Song; calibration at full refresh rate (so the
high-framerate fix is confirmed); the four 9 Sep ports have had a couple of hours of play
without incident.

**Not yet tested:** the current **64-sample / `LatencyBuffer=2`** combination beyond a
quick check — it needs a longer session. If the guitar crackles or drops out, that is the
first suspect; see the rollback ladder.

---

## ROLLBACK — read this first if anything is wrong

Changes are layered. Undo the **most recent layer first** and re-test; each step is
independent of the others. Close Rocksmith before touching `xinput1_3.dll` (it is held
open); the ini files can be edited any time and are read at launch.

**Symptom → first suspect**

| Symptom | Start at |
|---|---|
| crackle / dropouts / stutter in the guitar sound | step 1 |
| spike only at the start of each note, then fine | not a rollback — recalibrate (tuner screen on the way into a song, lower-right, Enter) |
| game says no cable / notes don't register | step 2 |
| no guitar at all in `GAME AMP`, `PEDAL ONLY` on screen | press `\` — you are muted on purpose |
| crash, white screen, hang, anything about the overlay text | step 3 |
| the two new `RSMods.ini` lines bother you | step 4 |

**Step 1 — latency settings** (11 Sep evening, least tested)

- `Y:\...\Rocksmith.ini`: `LatencyBuffer=2` → `4`
- `Y:\...\RS_ASIO.ini`: `CustomBufferSize=64` → `128`, or `BufferSizeMode=custom` → `driver` to
  hand control back to the NUX driver entirely (its default is 512)

Do them one at a time so you know which one it was. Mirror the change in `config/`.

**Step 2 — RS_ASIO entirely**

Delete `avrt.dll` from the game folder (the proxy that loads it). `RS_ASIO.dll` and
`RS_ASIO.ini` are inert without it; delete them too for tidiness. The game is back on
plain WASAPI — which means it takes its guitar from the **Windows default recording
device** again, so set that to `Line (NUX Audio)` (Settings → Sound → Input) before
launching. Recalibrate afterwards; the level differs between the two paths.

**Step 3 — the DLL**

```powershell
scripts\restore-dll.ps1      # -> pristine 1.2.7.4, refuses to run while the game is up
```

Or step back one build at a time by copying a backup over `Y:\...\xinput1_3.dll`:

| `backups\xinput1_3.dll.…` | Build | Has |
|---|---|---|
| `1.2.7.4-original` / `20260909-134102` | stock 1.2.7.4 (`fc7c44e1…`) | nothing of ours |
| `20260911-211546` | `c0817e0` (`7846d005…`) | the four 9 Sep ports only |
| `20260911-212341` | `6e64077` (`f5a2abd2…`) | + amp-source toggle |
| `20260911-223104` | `c0ec81f` (`bb0454c8…`) | + mute logging / never-restore-to-0 guard |
| *(installed)* | `1055e23` (`ab7e5eec…`) | + accuracy overlay |

`backups/` is untracked — do not delete it. Any build can also be rebuilt from its commit
with `git checkout <hash> -- RSMods-src && scripts\build-dll.ps1`.

Verify with `Get-FileHash 'Y:\Rocksmith 2014 Edition - Remastered\xinput1_3.dll' -Algorithm SHA256`.

**Step 4 — `RSMods.ini` lines**

`ToggleAmpSourceKey` and `DisplayCurrentAccuracy` can simply be deleted. Note both have
DLL-side defaults (`VK_OEM_5`, `on`), so deleting the line does not turn the feature off —
set `DisplayCurrentAccuracy = off` / `ToggleAmpSourceKey = ` (blank) for that.

**Calibration** lives in the game profile and cannot be "reverted"; just run it again.

**Nuclear option** (prove a problem is the mod, not the game): `scripts\Test without
RSMods.bat` renames the DLL away; `scripts\Restore RSMods.bat` puts it back. Both live in
the game folder too. RS_ASIO is separate — step 2 for that.

`cache.psarc` and `steam_emu.ini` were never touched (see `ROCKSMITH-PROJECT-NOTES.md`
§4 for *their* backups — `cache.bak`, `*.ini.bak`).

---

## Testing checklist

Do these in order. Tick them off here as they pass.

- [x] Game launches, DLL loads, `RSMods_debug.txt` updates *(9 Sep)*
- [x] `RSMods_debug.txt` shows `Fixed Calibration At High Framerates` *(9 Sep)*
- [ ] **Uplay prompt** clears on its own at startup, lands on profile `arps` at the main menu
- [ ] **Alt-Tab out of a song** with "show current note" on — no white screen, game
      recovers when you tab back
- [x] **Calibration** at the monitor's real refresh rate (no FPS cap) — the meter fills
      and calibration completes *(11 Sep)*
- [ ] **`PreventMidSongPause`** — add `PreventMidSongPause=on` under `[Toggle Switches]`
      in `RSMods.ini`, start a song, Alt-Tab: song keeps playing. *(Optional; off by
      default, so this is only tested if you want the feature.)*
- [x] **Amp source toggle** — press `\` mid-song: the game's guitar tone drops out,
      backing track keeps playing, `PEDAL ONLY` shows top-left. Press again to
      bring the virtual amp back. *(11 Sep — works; see the input-device note below)*
- [x] **RS_ASIO** — game launches with `avrt.dll` in place; `RS_ASIO-log.txt` names
      `NUX Audio` as the input driver; notes register with the webcam still set as the
      Windows default input; the `\` toggle still behaves *(11 Sep — at the driver's
      default 512-sample buffer)*
- [x] **RS_ASIO at 128 samples** — ran, log confirmed `2ms (128 frames)`, but clicks at
      note onset *(11 Sep)*
- [x] **RS_ASIO at 256 samples** — no click, but latency noticeable; back to 128 after
      recalibrating fixed the click *(11 Sep)*
- [ ] **64 samples + `LatencyBuffer=2`** — a full song with no crackle or dropouts;
      `RS_ASIO-log.txt` says `actual buffer duration: 1ms (64 frames)`
- [x] **Calibration** at the monitor's real refresh rate — done 11 Sep from the in-song tuner
      screen, meter filled and completed
- [x] **Accuracy overlay** — a percentage appears under the song timer (top right) once
      the song starts, moves as you hit and miss, and matches the number on the
      song-review screen at the end. Check Score Attack too. *(11 Sep — Learn A Song confirmed)*
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

## RS_ASIO — pin the NUX as the guitar input

Installed 11 Sep 2026: **RS_ASIO v0.7.5** (`avrt.dll` proxy + `RS_ASIO.dll` + `RS_ASIO.ini`)
in the game folder, from https://github.com/mdias/rs_asio. Hashes in
`config/RS_ASIO.version.txt`; the deployed ini is snapshotted at `config/RS_ASIO.ini`.

**Why:** without it the game takes its guitar from the *Windows default recording device*,
which any newly plugged USB device (the webcam did it) can steal. RS_ASIO binds the input to
the driver by name, so the Windows default no longer matters, and ASIO input latency is
lower than WASAPI.

**Routing ("option A"):**

```ini
[Config]
EnableWasapiOutputs=1     ; game audio -> Windows default playback (Realtek desk speakers)
EnableAsio=1
[Asio.Output]
Driver=                   ; deliberately blank - output stays on WASAPI
[Asio.Input.0]
Driver=NUX Audio          ; guitar in over the NUX ASIO driver, channel 0
```

**Buffer:** the NUX driver's default is 512 samples (10.7 ms, 12 ms reported) — the game
asks for 144. `BufferSizeMode=custom` / `CustomBufferSize=64` (1.3 ms) is set; the driver
reports `min: 8 max: 2048`, powers of two. 128 was clean after calibration, so 64 is the
next try (11 Sep, untested). WASAPI output is 3 ms.

**`Rocksmith.ini` `LatencyBuffer`** is the game's own internal input buffering, in audio
periods. Shipped at 4, set to **2** on 11 Sep alongside the 64-sample ASIO buffer (untested).
Fallback order if the guitar crackles or drops out: `LatencyBuffer` 2 -> 3 first, then
`CustomBufferSize` 64 -> 128. Both are read at launch. If a spike appears only at note
onset, that is calibration, not either buffer - see the note below.

**Note-onset click (11 Sep):** at 128 every note started with a spike. 256 removed it but
the extra latency was noticeable, so the real fix was **re-running the in-game
calibration** - the ASIO path hands the game a different input level than the WASAPI
path it was calibrated on, so the noise gate was snapping open on every attack. Calibrate
from the tuner screen that appears on the way into a song (lower-right, Enter), on the
NUX preset you actually play with. If a click ever comes back at 128, calibrate again
before touching the buffer.

Output stays where it was so the amp-source toggle above means the same thing it did
before. The alternative ("option B") is `Asio.Output Driver=NUX Audio` and
`EnableWasapiOutputs=0`, which sends *everything* out of the pedal into your amp.

The NUX ASIO driver was already installed and registered 32-bit
(`HKLM\SOFTWARE\WOW6432Node\ASIO\NUX Audio`), which the 32-bit game needs.
RSMods and RS_ASIO coexist by design — RSMods logs `RS_ASIO Bypass2RTC` at startup.

If `Channel=0` turns out to be the wrong NUX channel (silent, or a dry signal when a
processed one is expected), `RS_ASIO-log.txt` lists the driver's channel names; change
`Channel=` under `[Asio.Input.0]`.

---

## Accuracy overlay — live hit % while you play

```ini
[Toggle Switches]
DisplayCurrentAccuracy = on
```

Port of upstream 1.2.8.4's `DisplayCurrentAccuracy` (`D3DOverlay::ReadAccuracy`, commit
`ee1a587`). Draws `hit / (hit + missed)` as a percentage one line under the song timer,
right-aligned, whenever you are in a Learn A Song / Non-Stop Play / Score Attack screen
and the song clock is running. Default **on** in the DLL, so it survives `RSMods.exe`
rewriting the ini; set it `off` to hide it.

**How it reads the number:** `NoteData.h` (verbatim from upstream) describes the two
counter structs the game keeps — Learn A Song has `totalNotesHit` at `+0x30` and
`totalNotesMissed` at `+0x40`; Score Attack has them at `+0x4C`/`+0x50` with streaks,
phrases, score and multiplier around them. Both hang off the same static pointer,
`baseHandle + 0x00F5F62C` (upstream's `RemasteredSeptember2022` slot), through the chains
`{0xB0, 0x18, 0x4, 0x84, 0x0}` (LAS) and `{0xB0, 0x18, 0x4, 0x4C, 0x0}` (SA). The walk
uses `FindDMAAddy(..., safe = true)` so a not-yet-populated chain reads as 0 % rather than
a crash. The one deviation from upstream: the fork's overlay font is a fixed
`height / 72`, so the line offset is a constant `height / 27` instead of measuring the
font.

This is also the number backlog item #3 (loop pass counter / auto speed ladder) needs to
gate on "clean pass" — `ReadCurrentAccuracy()` in `dllmain.cpp` is the hook.

---

## Ideas backlog — things to add ourselves

Ranked for a practice tool. Effort is a guess.

| # | Idea | Effort | Hangs off |
|---|---|---|---|
| 1 | **Version string bump** so `RSMods_debug.txt` says `1.2.7.4-arp.N` | 1 line | `_RSMODS_VERSION` macro, `dllmain.cpp:16` |
| 2 | **Gate the Crowd Control server** behind `CrowdControlEnabled=off` — 3 threads + a TCP listener for Twitch, started unconditionally | small | `Initialize()` → `CrowdControl::StartServer()`; note it also applies the scroll-speed patch, keep that |
| 3 | **Loop pass counter + auto speed ladder** — overlay `Loop 1:12–1:20 · pass 4 · 82%`; after N passes bump speed by `RRSpeedInterval` | medium | `loopStart`/`loopEnd`, `RiffRepeater::GetSpeed/SetSpeed`, `MemHelpers::DX9DrawText`; loop-wrap seek at `dllmain.cpp:~981` is the "pass done" event |
| 4 | ~~**Port `DisplayCurrentAccuracy`**~~ — **done 11 Sep 2026**, see §Accuracy overlay | — | `ReadCurrentAccuracy()` in `dllmain.cpp` |
| 5 | **Practice log** — CSV of `timestamp, song key, speed, loop bounds, accuracy`; Song Manager shows last-practised / minutes per song (the thing the profile decrypt failure blocked) | small DLL, medium SongManager | song-key change detection at `dllmain.cpp:107` |
| 6 | **GUI checkbox for `PreventMidSongPause`** added programmatically in `UI.cs` | small-medium | closes the "RSMods.exe drops the key" caveat |
| 7 | **Hit-streak / miss-streak overlay** next to the accuracy % — `currentHitStreak`, `highestHitStreak`, `currentMissStreak` are already in `NoteData.h`, just private | small | add getters to `NoteData.h`, draw beside `ReadCurrentAccuracy()` |
| 8 | **Strict loop** — miss a note inside a loop and it rewinds to the loop start; toggle key so it is opt-in | small-medium | `totalNotesMissed` delta per frame + the existing loop seek at `dllmain.cpp` |
| 9 | **Switch the MG-300's preset from the game** — the MK2 takes MIDI over USB: CC#60 (or #73) on channel 1, value = preset number selects a preset; program change does *not* work and there is no bypass CC, so "mute the pedal" = switch to a user-made silent preset. Two uses: (a) make `\` also flip the pedal between your playing preset and a silent one, closing the "physical amp still makes noise" gap; (b) per-song pedal preset, the way `AutoTuneForSong` already sends tuning pedals a program change over WinMM MIDI out | medium; USB-MIDI on this pedal is reported as fiddly | `Mods/Midi.cpp` (already has a MIDI-out device picker + send), `ToggleAmpSourceKey` handler |
| 10 | **`LatencyBuffer=1`** — last software latency step, only if 64/2 holds up over a long session | 1 line | `Rocksmith.ini` |

Suggested order: 7 first (an hour, uses today's plumbing), then 3 → 8 → 5 as the practice arc; 9a is the one that finishes the amp toggle properly and is worth a spike to see whether this pedal's USB MIDI behaves; 1, 2, 6 whenever.

Not worth it: auto-loop by song section (needs phrase-boundary offsets — real reverse
engineering); metronome (unclear whether Wwise exposes a click).

---

## Upstream

- Fork (this baseline): https://github.com/keremcanb/RSMods_for_Cracked_Rocksmith_2014
- Upstream: https://github.com/Lovrom8/RSMods — fixes taken from tag
  `RSModsInstaller-v1.2.8.4_OnCommit`
