# rock_mod_arp

Rocksmith 2014 Remastered as a guitar-learning tool: a patched RSMods build, the
song-library manager, and the config that makes startup fast and the UI clean.

Game install: `Y:\Rocksmith 2014 Edition - Remastered\`. This repo is the source of
truth for everything hand-made; the game folder is where it gets deployed.

---

## STATUS — 12 Sep 2026

**Installed right now** (branch `mod-update-1.2.8.x`):

| Thing | State | Since |
|---|---|---|
| `Y:\...\xinput1_3.dll` | pause/scrub build, SHA-256 `6b6af655 ab5e3e5e ab62e3f8 81fe9880 5ee5673c d02b5871 5dd8d5f4 48d6379f` | 12 Sep 01:28 |
| RS_ASIO v0.7.5 | `avrt.dll` + `RS_ASIO.dll` + `RS_ASIO.ini` in the game folder; input `NUX Audio` ch 0, output WASAPI, **64-sample buffer** | 11 Sep |
| `Rocksmith.ini` | `LatencyBuffer=2` — the floor: 1 crackles on this PC; everything else as before | 12 Sep |
| `RSMods.ini` | keys re-mapped to one cluster, no Ctrl: `RRSpeedDownKey`, `LoopClearKey` added, `RewindKey = VK_BACK`, `ToggleAmpSourceKey = VK_OEM_7`; plus `PauseSongKey = P`, `ForwardKey = VK_DELETE`, `ForwardBy = 5000`, and `DisplayCurrentAccuracy`, `DisplayNoteStreak`, `DisplayLoopPasses` all `on`; nothing removed | 12 Sep |
| In-game calibration | redone on the ASIO input path, on the usual NUX preset | 11 Sep |
| Windows default input | still the webcam — **irrelevant now**, RS_ASIO binds the NUX by name | — |

Every deployed config file has a byte-identical snapshot under `config/`. To see what any
of them looked like at an earlier point: `git show <commit>:config/Rocksmith.ini`.

**Tested and good (11–12 Sep), in play:** the amp-source toggle; RS_ASIO input at 64
samples with `LatencyBuffer=2` (a full session, clean — `1` crackles, so this is the floor);
accuracy / streak / loop-pass overlay in Learn A Song; the no-Ctrl key cluster; calibration
at full refresh rate; the four 9 Sep ports.

**Not yet tested:** **pause / scrub** (`P`, `Delete`, built 01:28 on 12 Sep) — the first test
answers whether the note highway freezes with the audio; see §Pause and scrub. Also still
unexercised: the Score Attack overlay line. Next decision: the menu tone (backlog #11).

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
| no guitar at all in `GAME AMP`, `PEDAL ONLY` on screen | press `'` — you are muted on purpose |
| song audio stuck paused, or highway and audio out of step after `P` | press `P` once more; if still stuck, Esc → the game's own pause menu → resume, then blank `PauseSongKey = ` in `RSMods.ini` and tell me |
| crash, white screen, hang, anything about the overlay text | step 3 |
| the two new `RSMods.ini` lines bother you | step 4 |

**Step 1 — latency settings** (11 Sep evening, least tested)

- `Y:\...\Rocksmith.ini`: `LatencyBuffer=2` → `3`, then `4` (stock). Do not go to 1 — tried 12 Sep, crackles
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
| `20260911-231651` | `1055e23` (`ab7e5eec…`) | + accuracy overlay |
| `20260912-*` | `95e1650` (`ac288994…`) | + note streak line |
| `20260912-001815` | `0827a56` (`2c2a5aa4…`) | + `RRSpeedDownKey`, `LoopClearKey` |
| `20260912-012814` | `659542c` (`6ecd9865…`) | + hit/total, Score Attack line, loop pass counter |
| *(installed)* | pause/scrub commit (`6b6af655…`) | + `P` pause, `Delete` forward, scrub while paused |

`backups/` is untracked — do not delete it. Any build can also be rebuilt from its commit
with `git checkout <hash> -- RSMods-src && scripts\build-dll.ps1`.

Verify with `Get-FileHash 'Y:\Rocksmith 2014 Edition - Remastered\xinput1_3.dll' -Algorithm SHA256`.

**Step 4 — `RSMods.ini` lines**

`ToggleAmpSourceKey`, `RRSpeedDownKey`, `LoopClearKey`, `PauseSongKey`, `ForwardKey`,
`DisplayCurrentAccuracy`, `DisplayNoteStreak` and `DisplayLoopPasses` can simply be deleted.
All have DLL-side defaults (`VK_OEM_7`, `VK_OEM_MINUS`, `VK_OEM_5`, `P`, `VK_DELETE`, `on`,
`on`, `on`), so deleting the line does not turn the feature off —
set the `Display*` ones to `off`, or a key to blank (`LoopClearKey = `), for that. To get
the old Ctrl-only layout back: `RewindKey = VK_OEM_MINUS`, `ToggleAmpSourceKey = VK_OEM_5`,
blank the two new keys.

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
- [x] **64 samples + `LatencyBuffer=2`** — played fine *(12 Sep)*
- [x] **`LatencyBuffer=1`** — tried, too much crackle, back to 2 *(12 Sep)*
- [x] **Calibration** at the monitor's real refresh rate — done 11 Sep from the in-song tuner
      screen, meter filled and completed
- [x] **Accuracy overlay** — a percentage appears under the song timer (top right) once
      the song starts, moves as you hit and miss, and matches the number on the
      song-review screen at the end. Check Score Attack too. *(11 Sep — Learn A Song confirmed)*
- [x] **Streak line** — under the accuracy %: `12 in a row, best 37` counting up as you hit,
      flipping to `missed 3, best 37` on a dropped run, back to `0 in a row` on the next hit.
      Best should match the review screen's longest streak.
- [x] **No-Ctrl keys** — `-` slows, `\` clears the loop, `Backspace` rewinds, `'` toggles the
      amp; the old `Ctrl` combos still work
- [x] **Overlay details** *(Learn A Song; Score Attack line still unexercised)* — accuracy line reads `94.2%  (184 of 196)`; with a loop set, a
      `pass N` line appears and after each wrap becomes `pass N, last pass 92%`; setting or
      clearing the loop resets it to `pass 1`. In Score Attack a `score …, x4 (best x8), …`
      line appears under the streak.
- [ ] **Pause / scrub** — `P` mid-song: audio stops **and the highway stops**; `P` again
      resumes where it was. Then `P`, `Backspace` × 2, `P`: resumes 10 s earlier; same with
      `Delete` forwards. `Delete` while playing jumps 5 s ahead. Esc over a mod-pause and
      resuming from the menu does not leave things stuck. Check `RSMods_debug.txt` for the
      `(PAUSE) Resuming` line — if `timer now reads` differs from `Paused at`, the game's
      clock kept running while the audio was paused (tell me; it changes the design).
- [x] A normal practice session *(12 Sep)* — loops (`[` `]`), rewind (`-`), RR speed (`=`) all
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
| `docs/keymap-wooting-80he.png` | Picture of every practice key on the Wooting 80HE; `docs/keymap-wooting-80he.py` regenerates it after a keybind change. The key list itself is `ROCKSMITH-PROJECT-NOTES.md` §0 |

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

## Amp source toggle — the `'` key

One key flips between hearing Rocksmith's virtual amp and hearing only your own
pedalboard. Bound to `'` (`VK_OEM_7`), in the same right-hand cluster as the loop and
speed keys so it is reachable without looking. (Was `\` until 12 Sep; `\` is now clear-loop.)

```ini
[Audio Keybindings]
ToggleAmpSourceKey = VK_OEM_7
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
periods. Shipped at 4; **2** with the 64-sample ASIO buffer plays clean. **1 was tried on
12 Sep and crackles** — that is the floor on this PC, so 2 is final. Fallback order if the
guitar ever crackles at 2: `LatencyBuffer` 2 -> 3 first, then `CustomBufferSize` 64 -> 128.
Both are read at launch. If a spike appears only at note
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

## Accuracy, streak and loop-pass overlay — how you are doing, while you play

```ini
[Toggle Switches]
DisplayCurrentAccuracy = on
DisplayNoteStreak = on
DisplayLoopPasses = on
```

Stacked under the song timer, right-aligned:

```
                 1:42
    94.2%  (184 of 196)      <- DisplayCurrentAccuracy: hit / total so far
  12 in a row, best 37       <- DisplayNoteStreak
  pass 4, last pass 92%      <- DisplayLoopPasses: only while a full loop is set
```

- The streak line flips to `missed 3, best 37` while you are dropping notes and back to
  `0 in a row` on the next hit, so a fluffed run is visible without looking away.
- **Loop passes** count each time the loop wraps. `last pass` is the hit % of the pass that
  just finished (the game's counters are cumulative, so it is the delta since the previous
  wrap; the 2 s lead-in is included). Setting, moving or clearing the loop resets to
  `pass 1`. This is the first half of backlog item #3; the auto speed ladder builds on it.
- **Score Attack** adds `score 12345, x4 (best x8), 120 perfect, 30 late` under the streak
  (Learn A Song has no score).

Each line has its own switch; all default **on** in the DLL.

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

The streaks come from the same structs — `currentHitStreak`, `highestHitStreak`,
`currentMissStreak`, plus the hit/missed totals and, for Score Attack, score, multiplier,
perfect and late counts — exposed through one-line getters added to `NoteData.h` (the layout
itself is still upstream's, untouched). `ReadNoteStats()` in `dllmain.cpp` returns all of it
in one struct per frame. Pass counting hooks the loop-wrap seek in `Hook_EndScene`; that
branch fires every frame until the seek lands, so `loopWrapPending` gates it to once per wrap.

This is also the data backlog item #3 (loop pass counter / auto speed ladder) needs to
gate on "clean pass" — `ReadNoteStats()` is the hook.

---

## Pause and scrub — `P`, `Backspace`, `Delete`

```ini
[Keybinds]
PauseSongKey = P
RewindKey = VK_BACK
ForwardKey = VK_DELETE
[Mod Settings]
RewindBy = 5000
ForwardBy = 5000
```

`P` pauses the song in place with no pause menu: it pauses the song's Wwise event
(`ExecuteActionOnEvent("Play_<key>", Pause)`), the same handle rewind and the loop-wrap
seek already use. The note highway follows the song audio — that is why rewind moves the
notes — so pausing the audio should freeze the highway too. **That is the thing the first
test confirms**; the `(PAUSE) Resuming` log line records what the game's timer read while
paused, so a running clock would show up as a mismatch.

While paused, `Backspace` / `Delete` do not seek live; they move a resume point, shown
top-centre as `PAUSED  1:42  ->  1:32`, and `P` seeks there and resumes. Deferring the seek
means the result does not depend on how Wwise treats a seek on a paused voice. If a live
seek turns out to redraw the highway while paused, that is a later upgrade.

`Delete` while playing is the mirror of `Backspace`: seek to `now + ForwardBy`. No cap at the
song end — seeking past it ends the song, which is what you would expect.

Guards: the loop-wrap seek is skipped while paused (otherwise a pause sitting on the loop end
would fire it every frame); leaving the song while paused clears the flag. Gated on
`AllowRewind` and the playing screens only, like rewind.

---

## Ideas backlog — things to add ourselves

Ranked for a practice tool. Effort is a guess.

| # | Idea | Effort | Hangs off |
|---|---|---|---|
| 1 | **Version string bump** so `RSMods_debug.txt` says `1.2.7.4-arp.N` | 1 line | `_RSMODS_VERSION` macro, `dllmain.cpp:16` |
| 2 | **Gate the Crowd Control server** behind `CrowdControlEnabled=off` — 3 threads + a TCP listener for Twitch, started unconditionally | small | `Initialize()` → `CrowdControl::StartServer()`; note it also applies the scroll-speed patch, keep that |
| 3 | **Auto speed ladder** — pass counter and per-pass accuracy are **done (12 Sep)**; left: after N passes at or above X %, bump speed by `RRSpeedInterval` automatically | small now | `loopPass`, `lastPassAccuracy`, `RiffRepeater::SetSpeed` |
| 4 | ~~**Port `DisplayCurrentAccuracy`**~~ — **done 11 Sep 2026**, see §Accuracy overlay | — | `ReadCurrentAccuracy()` in `dllmain.cpp` |
| 5 | **Practice log** — CSV of `timestamp, song key, speed, loop bounds, accuracy`; Song Manager shows last-practised / minutes per song (the thing the profile decrypt failure blocked) | small DLL, medium SongManager | song-key change detection at `dllmain.cpp:107` |
| 6 | **GUI checkbox for `PreventMidSongPause`** added programmatically in `UI.cs` | small-medium | closes the "RSMods.exe drops the key" caveat |
| 7 | ~~**Hit-streak / miss-streak overlay**~~ — **done 11 Sep 2026**, see §Accuracy and streak overlay | — | `ReadNoteStats()` in `dllmain.cpp` |
| 8 | **Strict loop** — miss a note inside a loop and it rewinds to the loop start; toggle key so it is opt-in | small-medium | `totalNotesMissed` delta per frame + the existing loop seek at `dllmain.cpp` |
| 9 | **Switch the MG-300's preset from the game** — the MK2 takes MIDI over USB: CC#60 (or #73) on channel 1, value = preset number selects a preset; program change does *not* work and there is no bypass CC, so "mute the pedal" = switch to a user-made silent preset. Two uses: (a) make `\` also flip the pedal between your playing preset and a silent one, closing the "physical amp still makes noise" gap; (b) per-song pedal preset, the way `AutoTuneForSong` already sends tuning pedals a program change over WinMM MIDI out | medium; USB-MIDI on this pedal is reported as fiddly | `Mods/Midi.cpp` (already has a MIDI-out device picker + send), `ToggleAmpSourceKey` handler |
| 10 | ~~**`LatencyBuffer=1`**~~ — tried 12 Sep, crackles; 2 is the floor | — | `Rocksmith.ini` |
| 11 | **Menu / tuner tone** — the game's out-of-song tone is a hard-wired high-gain preset and Rocksmith has no default-tone setting (Ubisoft confirmed on the Steam forums). Two ways round it, decision pending: **A** clean tone saved to Tone Designer slot 2–4, pressed by hand after every song; **B** (recommended) `MuteGameAmpOutsideSongs=on` — hold `Mixer_Player1` at 0 whenever `currentMenu` is not a song mode, so menus / tuner / lessons are pedal-only and the game amp returns when a song starts, respecting the `'` toggle. ~20 lines on the amp-toggle plumbing | small | `VolumeControl::MutePlayer`, `songModes`, the per-frame block in `Hook_EndScene` |

Suggested order: 11 first (decide A/B, an hour), then 3 → 8 → 5 as the practice arc (7 is done); 9a is the one that finishes the amp toggle properly and is worth a spike to see whether this pedal's USB MIDI behaves; 1, 2, 6 whenever.

Not worth it: auto-loop by song section (needs phrase-boundary offsets — real reverse
engineering); metronome (unclear whether Wwise exposes a click).

---

## Upstream

- Fork (this baseline): https://github.com/keremcanb/RSMods_for_Cracked_Rocksmith_2014
- Upstream: https://github.com/Lovrom8/RSMods — fixes taken from tag
  `RSModsInstaller-v1.2.8.4_OnCommit`
