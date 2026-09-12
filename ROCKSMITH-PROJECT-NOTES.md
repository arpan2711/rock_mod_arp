# Rocksmith 2014 — setup, fixes, and open work

**Last worked on:** 2026-09-09
**Machine:** Windows 11, `Y:\Rocksmith 2014 Edition - Remastered\`
**Goal:** use Rocksmith primarily as a guitar-learning tool — fast startup, clean UI,
custom songs working, minimal game fluff.

---

## 0. CONTROLS — practice keys (read this one)

All of these work **live, inside a song**. No menus.

One key each, no modifiers, all in the right-hand cluster of the main block (re-mapped
12 Sep 2026; picture in `docs/keymap-wooting-80he.png`):

| Key | Does |
|---|---|
| `Backspace` | **Back 5 seconds** instantly |
| `Delete` | **Forward 5 seconds** instantly |
| `P` | **Pause / resume in place**, no pause menu. While paused, `Backspace` / `Delete` move the resume point (shown top-centre) and `P` resumes from there |
| `[` | Set **loop start** |
| `]` | Set **loop end** — the section then repeats forever |
| `\` | **Clear** the loop |
| `=` | Riff Repeater speed **up** (2% per press) |
| `-` | Riff Repeater speed **down** |
| `'` | **Game amp ↔ pedal only** (mutes the game's guitar tone; backing track keeps going) |
| `Ctrl` + `A` | Reload `RSMods.ini` without restarting |

`Ctrl`+`[`/`]` (clear) and `Ctrl`+`=` (slow down) still work as before, for muscle memory.

Workflow: drop `[` and `]` around a few bars, tap `-` to slow it down, work the passage,
then tap `=` past 100% so real tempo feels easy afterwards; `\` clears the loop.

**Tunable in `RSMods.ini`:**

| Setting | Now | What it does |
|---|---|---|
| `RewindBy` | `5000` | Back-scrub distance, ms |
| `ForwardBy` | `5000` | Forward-scrub distance, ms |
| `LoopingLeadUp` | `2000` | Run-in *before* the loop point each pass, ms. Set 0 for a hard cut |
| `RRSpeedInterval` | `2` | Speed step size, % |
| `LinearRiffRepeater` | `on` | Makes the speed % honest — stock Rocksmith's 68% is really 50% |

Keys are set with `VK_` names (`LoopStartKey = VK_OEM_4` etc). Valid names live in
`DLL/Settings.hpp` → `keyMap`. **An unrecognised name binds silently to nothing**, so
check the table rather than guessing. `[`=`VK_OEM_4`, `]`=`VK_OEM_6`, `\`=`VK_OEM_5`,
`'`=`VK_OEM_7`, `=`=`VK_OEM_PLUS`, `-`=`VK_OEM_MINUS`, `Backspace`=`VK_BACK`, `Delete`=`VK_DELETE`. Function keys
`VK_F1`–`VK_F24` all exist.

Backup before these were set: `RSMods.ini.before-practice`.

---

## 1. The install

| | |
|---|---|
| Build | CODEX repack of Rocksmith 2014 **Remastered**, Steam appid `221680` |
| Executable | `Rocksmith2014.exe` — **32-bit (i386)**, Steam-stub packed (`steam_api.cdx`) |
| Song library | **1,309** `.psarc` in `dlc\` (1,306 official + 3 custom) |
| Official DLC | Repacked pack — every `appid.appid` rewritten to `221680` (not a normal install) |
| Mod loader | **RSMods 1.2.7.4**, injected via `xinput1_3.dll` |
| RSMods source | `github.com/keremcanb/RSMods_for_Cracked_Rocksmith_2014` (fork of `Lovrom8/RSMods`) |
| CDLC enabler | `D3DX9_42.dll` = **RSCDLCEnabler** (see §3) |
| Profile | `arps` — saves live in `C:\Users\Public\Documents\Steam\CODEX\221680\remote\` |
| Audio | **RS_ASIO v0.7.5** (installed 11 Sep 2026): guitar in over the `NUX Audio` ASIO driver, game audio out over WASAPI to the Windows default playback device (Realtek desk speakers). `Rocksmith.ini` still has exclusive mode + ultra-low-latency on. Config snapshot: `config/RS_ASIO.ini`. |

---

## 2. Problem 1 — CDLC didn't appear in the song list (SOLVED)

**Cause:** the game reads `appid.appid` out of each `.psarc` and asks the Steam emulator
whether that app is owned. Custom songs ship `248750` (the Cherub Rock DLC, which every
legitimate owner has). The repacked official songs all carry `221680`. With
`DLCUnlockall=0` in `steam_emu.ini`, only the officials passed.

**Fix:** `steam_emu.ini` → `DLCUnlockall=1`.

Also patched the three customs' internal `appid.appid` from `248750` → `221680` while
diagnosing. Harmless but now redundant. Originals in `SongManager\backups\`.

---

## 3. Problem 2 — CDLC loaded to the tuning screen then froze, silently (SOLVED)

Symptom: song appeared, tuning screen worked, then venue/speakers rendered with **no
fretboard, no notes, and no audio**.

**Cause:** the **CDLC enabler DLL was missing entirely.** Rocksmith verifies song package
signatures; custom songs fail that check. The community patch is a proxy
`D3DX9_42.dll` that NOPs the check out at runtime. The game folder had no `d3dx9_42.dll`
at all.

**Fix:** installed `D3DX9_42.dll` (RSCDLCEnabler) into the game root.

```
sha256  c09dacbd428a5b55db814b46401224fd7ea9c295057112334eb50c1768d3c776
size    133,632 bytes
```

Verified before install: 32-bit, 329 exports (all genuine D3DX names), imports
**KERNEL32 only**, proxies to the real system DLL via
`GetSystemDirectoryA`+`LoadLibraryA`, patches via `VirtualProtect`. No network, no
injection, no registry, no shell. Embedded build path
`C:\Users\antsa\Source\Repos\RSCDLCEnabler\Release\RSCDLCEnabler.pdb` and the giveaway
strings `"Patch verify_signature success!"` / `"Failed to patch verify_signature!"`.

### Things ruled out along the way (all verified clean — don't re-check these)

The three custom `.psarc` files are structurally identical to working official songs:

- PSARC container, encryption, TOC — valid
- Every one of 20 referenced amps/cabs/pedals present in `gears.psarc`
- Tone key references resolve internally; RSMods `FixBrokenTones` was active and didn't help
- Wwise soundbanks: version **91**, same BKHD/DIDX/DATA/HIRC/STID layout as official
- Audio: Vorbis codec `0xffff` @ 48 kHz, same as official
- **`.sng` note data decrypts with the PC key and inflates to the exact declared byte count**
- `d3dx9_42.dll` correctly present in SysWOW64 (a known false lead)
- **Library size is NOT a problem** — people run 7,000 songs; 1,309 is unremarkable

---

## 4. Configuration changes made

### `Rocksmith.ini` — backup: `Rocksmith.ini.bak`

| Setting | Value | Why |
|---|---|---|
| `DisableBrowser` | `1` | Embedded Ubisoft browser — pure startup cost here |
| `UseProxy` | `0` | Stop routing net calls through the system proxy |
| `EnableShadows` | `0` | No gameplay value |
| `EnableDepthOfField` | `0` | Blurred the far highway, hurt note reading |
| `EnablePostEffects` | `0` | Sharper notes |
| `Fullscreen` | **`0`** | **Windowed — deliberate, do not change.** Was set to 1 once; reverted on request. |

### `steam_emu.ini` — backups: `steam_emu.ini.bak`, `.bak2`

`DLCUnlockall=1`, `Offline=1`.
Untouched deliberately: `AppId`, `[Interfaces]`, `[Crack]`.
Not yet tried: `LobbyEnabled=0`, `Overlays=0`.

### `RSMods.ini` — backups: `RSMods.ini.bak`, `RSMods.ini.before-autoload`

| Setting | Value | Effect |
|---|---|---|
| `ForceReEnumeration` | `on` | New CDLC appears without restarting the game |
| `FixBrokenTones` | `on` | Kept on; wasn't the freeze cause but harmless |
| `ToggleLoft` | `on` (+`When=song`) | Hides venue, amps, speaker rings |
| `Skyline` | **`off`** | **Top bar VISIBLE — wanted. Do not re-enable the removal.** |
| `Headstock` | `on` | Headstock hidden in song (was already set before this project) |
| `ForceProfileLoad` | `on` | "Fork in the toaster" — spams Enter through startup |
| `ProfileToLoad` | `arps` | Auto-selects the profile — **confirmed working** |

> RSMods toggles are **removal** switches: `on` means the thing is *gone*.

### RSMods Custom Mods (applied via `RSMods.exe`, repacks `cache.psarc`)

- **Skip intro sequences** — working
- **Add EXIT GAME to Main Menu** — working, replaces the dead UPLAY entry

`cache.psarc` is now 16,218,042 bytes (was 16,345,022). **`cache.bak` is a pristine
byte-identical backup of the original** — instant rollback.

---

## 5. Tools built (all in `SongManager\`, plain Python stdlib, no installs)

**`Song Manager.bat`** — main tool. Local web app: starts a Python server, opens the
browser, console window is the off switch.

- Reads every package in `dlc\` and `dlc_disabled\`, shows artist / song / album / year /
  length / arrangements / tuning / official-vs-custom
- Search, filter, sort; tick songs and **Apply** moves files between `dlc\` and
  `dlc_disabled\` — nothing is ever deleted, profile scores survive
- Named **setlists** — save a selection, reload it later
- Blocks Apply while the game is running (it holds the files open)
- Cold scan ~16 s for 1,309 packages, cached after. Cache: `library.json`

**Supporting files:** `psarc.py` (pure-Python PSARC reader — AES-256-CFB TOC decrypt,
verified against FIPS-197 vectors), `server.py`, `ui.html`.

**In the game folder:**

- `Launch Rocksmith.bat` + `SongManager\uplay_skip.py` — auto-Escape launcher.
  **Timing didn't work, approach rejected. Superseded by §6.**
- `Test without RSMods.bat` / `Restore RSMods.bat` — renames `xinput1_3.dll` to run
  the game completely unmodded. Diagnostic; still useful.

### Useful constants discovered

```
PSARC TOC key (AES-256-CFB, zero IV):
  C53DB23870A1A2F71CAE64061FDD0E1157309DC85204D4C5BFDF25090DF2572C
SNG key (AES-256-CTR, PC):
  CB648DF3D12A16BF71701414E69619EC171CCA5D2A142E3E59DE7ADDA18A3A30
Profile key: the published one does NOT match this build's saves — decrypt fails.
```

---

## 6. DONE — the 1.2.8.x port

**Status:** all four fixes ported, built, committed, and **installed (9 Sep 2026)**. Smoke test passed — DLL loads, calibration hook applied. **Full testing pending.** Rollback, hashes, and the test checklist are in that repo's `README.md`.

Work lives in `C:\Users\arpan\rock_mod_arp` (git repo, branch `mod-update-1.2.8.x`).
One commit per fix, reasoning in the commit messages. See that repo's `README.md`.

### Why porting, not upgrading

1.2.8.x is a large refactor — the 73 KB `dllmain.cpp` monolith was split into
`GameState` / `Keyboard` / `ModManager`, plus ~35 new files. Upstream cannot be
merged wholesale, so each fix was cherry-picked into the 1.2.7.4 structure.

The fork's offsets were confirmed to target the same exe as upstream's
`RemasteredSeptember2022` slot — `ptr_disableTrueTuning` `0x004DCCF2`,
`ptr_WindowNotInFocusValue` `0xEC5D46`, `ptr_sampleRateBuffer` `0x1251A9C`, all
three identical on both sides. So upstream's Remastered addresses are valid here.

### What was fixed

| Fix | From | Effect |
|---|---|---|
| Uplay login dialog auto-dismissed | 1.2.8.x | No more pressing Escape twice at startup |
| Alt-Tab white-screen semi-crash | 1.2.8.4 | Fixes the crash with "show current note" on |
| Calibration above 100 FPS | 1.2.8.4 | Calibration completes without capping framerate |
| `PreventMidSongPause` | 1.2.8.2 | Optional: tabbing away mid-song no longer pauses it |

**Step 0 resolved.** The guess in the old plan was right: `dontAutoEnter` (in
`DLL/D3D/D3DHelper.hpp`, not `D3DHooks.hpp`) contained **both** `"UplayLoginDialog"`
and `"SelectionListDialog"`, so the auto-load block bailed out before running any
logic on that screen. That guard was half the bug; the other half is that the block
only ever sent **Enter**, and the dialog closes on **Escape**. Both are fixed.

`Util::SendKey` in `MemHelpers.hpp` turned out to be byte-for-byte equivalent to
upstream's `Keyboard::SendEscapeKey`, so no new helper was needed — as predicted.

### Build — easier than expected

**Visual Studio Community is not needed. Build Tools 2026 was already installed**
with the C++ workload (MSVC 14.51, toolset v145) and Windows SDK 10.0.26100 with
x86 libs. The project asks for v142; `scripts\build-dll.ps1` retargets to v145 on
the command line rather than editing the vendored `.vcxproj`.

```powershell
scripts\build-dll.ps1     # Release|Win32 -> RSMods-src\Installer\Resources\xinput1_3.dll
scripts\install-dll.ps1   # backs up the current DLL, then installs
scripts\restore-dll.ps1   # instant rollback
```

Builds clean — no errors, only the 17 pre-existing warnings. Output verified as a
32-bit PE32 DLL exporting the 7 XInput entry points. Output goes to
`Installer\Resources\`, **not** `Release\`.

### Verification still owed

Nothing here has been run in the game yet. In order:

1. Startup — does the Uplay prompt clear on its own?
2. Alt-Tab out of a song with "show current note" on — no white screen?
3. Calibration at the monitor's real refresh rate — does the meter fill?
4. `PreventMidSongPause=on` in `RSMods.ini` — does the song keep playing?

`RSMods_debug.txt` reports the build as `1.2.7.4-arp.N` on its first line (bumped per
installed build from 12 Sep 2026; `_RSMODS_VERSION` in `dllmain.cpp`).
It should now also show `(BUG PREVENTION) Fixed Calibration At High Framerates` — if
it instead says the calibration fix was **skipped**, the hook site bytes did not
match and that offset needs revisiting.

### The one thing not ported

`PreventMidSongPause` has **no GUI checkbox** — it is read straight from
`RSMods.ini`. Adding one means editing the 480 KB generated `GUI/UI.Designer.cs`.
`RSMods.exe` rewrites `RSMods.ini` when it saves, so it may drop the hand-added key;
re-add it after using the GUI.

```ini
[Toggle Switches]
PreventMidSongPause=on
```

---

## 7. Optional extras not yet done

- `LobbyEnabled=0` / `Overlays=0` in `steam_emu.ini` — if anything still tries to connect
- ~~**RS_ASIO**~~ — installed 11 Sep 2026, see README §RS_ASIO. `BypassTwoRTCMessageBox` not yet
  turned on; do it if the "two Real Tone Cables" prompt ever appears
- RSMods **Fast Load** custom mod — upstream README recommends pairing it with
  `ForceProfileLoad`
- Wire `Launch Rocksmith.bat` behaviour into the Song Manager's Launch button (only if
  the Uplay fix somehow lands outside the DLL)
