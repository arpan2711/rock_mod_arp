# Rocksmith 2014 — setup, fixes, and open work

**Last worked on:** 2026-09-09
**Machine:** Windows 11, `Y:\Rocksmith 2014 Edition - Remastered\`
**Goal:** use Rocksmith primarily as a guitar-learning tool — fast startup, clean UI,
custom songs working, minimal game fluff.

---

## 0. CONTROLS — practice keys (read this one)

All of these work **live, inside a song**. No menus.

| Key | Does |
|---|---|
| `-` | **Rewind 5 seconds** instantly |
| `[` | Set **loop start** |
| `]` | Set **loop end** — the section then repeats forever |
| `Ctrl` + `[` / `]` | **Clear** the loop |
| `=` | Riff Repeater speed **up** (2% per press) |
| `Ctrl` + `=` | Riff Repeater speed **down** |

Workflow: drop `[` and `]` around a few bars, slow it with `Ctrl`+`=`, work the passage,
then push past 100% with `=` so real tempo feels easy afterwards.

**Tunable in `RSMods.ini`:**

| Setting | Now | What it does |
|---|---|---|
| `RewindBy` | `5000` | Rewind distance, ms |
| `LoopingLeadUp` | `2000` | Run-in *before* the loop point each pass, ms. Set 0 for a hard cut |
| `RRSpeedInterval` | `2` | Speed step size, % |
| `LinearRiffRepeater` | `on` | Makes the speed % honest — stock Rocksmith's 68% is really 50% |

Keys are set with `VK_` names (`LoopStartKey = VK_OEM_4` etc). Valid names live in
`DLL/Settings.hpp` → `keyMap`. **An unrecognised name binds silently to nothing**, so
check the table rather than guessing. `[`=`VK_OEM_4`, `]`=`VK_OEM_6`, `=`=`VK_OEM_PLUS`,
`-`=`VK_OEM_MINUS`. Function keys `VK_F1`–`VK_F24` all exist.

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
| Audio | WASAPI exclusive, ultra-low-latency on. **RS_ASIO is NOT installed.** |

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

## 6. OPEN WORK — kill the Uplay login prompt

**Status:** the only thing left. Everything else works.

Startup is now: launch → logos skipped → **Uplay prompt (must press Escape twice)** →
profile `arps` auto-selected → main menu.

**Why the existing mod doesn't clear it:** `ForceProfileLoad` works by spamming
**Enter**. The Uplay dialog only closes on **Escape**.

**Upstream already fixed this.** RSMods `1.2.8.4` (Aug 2026), in
`DLL/Mods/AutoLoadProfileMod.cpp`:

```cpp
// Skip the UPlay login dialog - depending on the menu it might need either
// ESC or Enter, so spam both.
if (GameState::currentMenu == "SelectionListDialog" ||
    GameState::currentMenu == "UplayLoginDialog") {
    Keyboard::SendEscapeKey();
    Keyboard::AutoEnterGame();
}
```

**The fix ships in a real release** — verified at tag `RSModsInstaller-v1.2.8.4_OnCommit`,
in **`DLL/ModManager.cpp` line ~623** (not `Mods/AutoLoadProfileMod.cpp`; that file is a
later dev-branch refactor). `Keyboard::SendEscapeKey()` exists there too. So this is a
downloadable build, not an unreleased branch.

**Why we can't just update:** the fork is dead — created and last pushed the same day,
**21 Nov 2024**, single release `RSModsInstaller-v1.2.7.4-Cracked`, 15 stars. Upstream
1.2.8.4 has the fix but carries the check this fork exists to remove, so it may not run
on this install.
*(Claude will help port the fix and set up the build; Claude will not work on the
piracy-check removal itself, or source check-removed builds.)*

> **TRY THIS FIRST:** just run the official 1.2.8.4 installer and see whether it works.
> The assumption that the check blocks it is untested — and that assumption was already
> wrong once (the Custom Mods tab worked fine). Ten minutes of testing beats the guess,
> and if it runs, everything below is unnecessary.

### What 1.2.8.x adds over 1.2.7.4

`1.2.8.0` (Jan 2025) — native support for **both** Remastered and Learn & Play.
Note from the release: *"If your game .exe is around 11MB, you can also use 1.2.7.4."*
**This exe is 11.1 MB**, so 1.2.7.4 is legitimately correct here — just old.

- **1.2.8.2** — song accuracy display; configurable overlay font size; **disable pause on
  Alt-Tab while in a song**; RR-over-100% no longer required for related mods
- **1.2.8.3** — permanently remove fingerprints; GuitarSpeak tuning-menu fix
- **1.2.8.4** — **calibration fix for 120+ Hz monitors**; **fixed Alt-Tab semi-crash when
  "show current note" is enabled** (that mod is ON here); crash fix for missing `dlc`
  folder; ASIO buffer cap 4096; setting sanitiser that names the bad INI line
- Unlisted: the Uplay fix, plus the `GameState` / `Keyboard` / `ModManager` split out of
  the 73 KB `dllmain.cpp`

Three of these are directly wanted: the Uplay fix, the Alt-Tab crash fix, and 120 Hz
calibration. **All practice features (looping, rewind, RR speed) already exist in
1.2.7.4** — see §0. Nothing else compelling is being missed.

### The port — where the code lives in 1.2.7.4

Everything is in **`DLL/dllmain.cpp`** (73 KB monolith), not a `Mods/` file.

- **line ~1251** — `AutoEnterGame()`, sends only `VK_RETURN` via `PostMessage`
- **line ~1670** — the `ForceProfileEnabled` block
- `DLL/MemHelpers.hpp` already has a generic sender:
  `namespace Util { inline void SendKey(unsigned int key); }` — **no new function needed**

### Plan

**Step 0 — resolve the unknown first.** `dontAutoEnter` is used at line 1670 but declared
in a header not yet read (probably `DLL/D3D/D3DHooks.hpp`). After cloning:

```
grep -rn dontAutoEnter DLL/
```

**If `UplayLoginDialog` is in that list, that alone is the bug** — the guard skips the
dialog before any logic runs, and removing it may be the whole fix.

**Step 1 — patch** `dllmain.cpp` inside the `ForceProfileEnabled` block:

```cpp
// The Uplay login dialog closes on Escape, not Enter.
if (currentMenu == "UplayLoginDialog" || currentMenu == "SelectionListDialog") {
    Util::SendKey(VK_ESCAPE);
    AutoEnterGame();
}
else if (Settings::ReturnSettingValue("ProfileToLoad") != "" && currentMenu == "ProfileSelect") {
    // ... existing profile-walking code unchanged
```

Menu name strings come from the *game*, not the mod, so upstream's are valid here.

**Step 2 — build.** **Visual Studio Community 2022**, workload *"Desktop development with
C++"*. Not VS Code — this is an MSVC `.sln` and VS Code means hand-wiring MSBuild for no
benefit.

- Open `RSMods.sln`, build the **DLL project only** (skip the C# GUI and Installer)
- Config **Release | x86** — the game is 32-bit, an x64 build won't load
- Dependencies vendored in `DLL/Lib/` (Detours, DirectX, JSON, ImGui) — no vcpkg/NuGet

**Step 3 — install.** Output is `xinput1_3.dll`. Back up the current one, swap it in.

**Step 4 — verify.** Does the prompt clear? (`RSMods_debug.txt` will still report 1.2.7.4
unless the version string is bumped.)

**Rollback:** keep the old `xinput1_3.dll`; swapping back is instant.

---

## 7. Optional extras not yet done

- `LobbyEnabled=0` / `Overlays=0` in `steam_emu.ini` — if anything still tries to connect
- **RS_ASIO** — not installed; the real fix for input latency with an audio interface.
  Pairs with `BypassTwoRTCMessageBox`
- RSMods **Fast Load** custom mod — upstream README recommends pairing it with
  `ForceProfileLoad`
- Wire `Launch Rocksmith.bat` behaviour into the Song Manager's Launch button (only if
  the Uplay fix somehow lands outside the DLL)
