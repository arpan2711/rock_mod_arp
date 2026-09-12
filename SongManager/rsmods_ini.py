r"""RSMods.ini: schema, safe in-place writer, and read-only status for the Settings page.

Stdlib only. Nothing here rewrites the ini from a template. Every edit is a
line-level replacement of one `key = value` inside its section; comments,
blanks, unknown keys, section order and CRLF all survive byte-for-byte.
The one thing the writer may add is a `key = value` line for a key that is
missing from its section (at the end of that section). It never removes.

Paths: Song Manager runs from <game>\SongManager\, so the game copy of
RSMods.ini is one folder up. The repo snapshot (config\RSMods.ini) is found by
find_repo(); both copies are written together so they cannot drift.
"""

import difflib
import hashlib
import os
import re
import subprocess
import sys
import time

# ---------------------------------------------------------------- VK names
# Every name DLL/Settings.hpp keyMap accepts. An unknown name binds silently to
# nothing in the DLL, so the page refuses anything not in this set.
VK_NAMES = frozenset("""
VK_LBUTTON VK_RBUTTON VK_CANCEL VK_MBUTTON VK_XBUTTON1 VK_XBUTTON2 VK_BACK VK_TAB
VK_CLEAR VK_RETURN VK_SHIFT VK_CONTROL VK_MENU VK_PAUSE VK_CAPITAL VK_KANA VK_HANGUEL
VK_HANGUL VK_IME_ON VK_JUNJA VK_FINAL VK_HANJA VK_KANJI VK_IME_OFF VK_ESCAPE VK_CONVERT
VK_NONCONVERT VK_ACCEPT VK_MODECHANGE VK_SPACE VK_PRIOR VK_NEXT VK_END VK_HOME VK_LEFT
VK_UP VK_RIGHT VK_DOWN VK_SELECT VK_PRINT VK_EXECUTE VK_SNAPSHOT VK_INSERT VK_DELETE
VK_HELP 0 1 2 3 4 5 6 7 8 9 A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
VK_LWIN VK_RWIN VK_APPS VK_SLEEP VK_NUMPAD0 VK_NUMPAD1 VK_NUMPAD2 VK_NUMPAD3 VK_NUMPAD4
VK_NUMPAD5 VK_NUMPAD6 VK_NUMPAD7 VK_NUMPAD8 VK_NUMPAD9 VK_MULTIPLY VK_ADD VK_SEPARATOR
VK_SUBTRACT VK_DECIMAL VK_DIVIDE VK_F1 VK_F2 VK_F3 VK_F4 VK_F5 VK_F6 VK_F7 VK_F8 VK_F9
VK_F10 VK_F11 VK_F12 VK_F13 VK_F14 VK_F15 VK_F16 VK_F17 VK_F18 VK_F19 VK_F20 VK_F21
VK_F22 VK_F23 VK_F24 VK_NUMLOCK VK_SCROLL VK_LSHIFT VK_RSHIFT VK_LCONTROL VK_RCONTROL
VK_LMENU VK_RMENU VK_BROWSER_BACK VK_BROWSER_FORWARD VK_BROWSER_REFRESH VK_BROWSER_STOP
VK_BROWSER_SEARCH VK_BROWSER_FAVORITES VK_BROWSER_HOME VK_VOLUME_MUTE VK_VOLUME_DOWN
VK_VOLUME_UP VK_MEDIA_NEXT_TRACK VK_MEDIA_PREV_TRACK VK_MEDIA_STOP VK_MEDIA_PLAY_PAUSE
VK_LAUNCH_MAIL VK_LAUNCH_MEDIA_SELECT VK_LAUNCH_APP1 VK_LAUNCH_APP2 VK_OEM_1 VK_OEM_PLUS
VK_OEM_COMMA VK_OEM_MINUS VK_OEM_PERIOD VK_OEM_2 VK_OEM_3 VK_OEM_4 VK_OEM_5 VK_OEM_6
VK_OEM_7 VK_OEM_8 VK_OEM_102 VK_PROCESSKEY VK_PACKET VK_ATTN VK_CRSEL VK_EXSEL VK_EREOF
VK_PLAY VK_ZOOM VK_NONAME VK_PA1 VK_OEM_CLEAR
""".split())

# What to print on a keycap for a VK name (US layout). Letters and digits are themselves.
VK_LABELS = {
    "VK_OEM_MINUS": "-", "VK_OEM_PLUS": "=", "VK_OEM_4": "[", "VK_OEM_6": "]",
    "VK_OEM_5": "\\", "VK_OEM_7": "'", "VK_OEM_1": ";", "VK_OEM_COMMA": ",",
    "VK_OEM_PERIOD": ".", "VK_OEM_2": "/", "VK_OEM_3": "`", "VK_OEM_102": "\\ (ISO)",
    "VK_BACK": "Backspace", "VK_DELETE": "Delete", "VK_RETURN": "Enter", "VK_ESCAPE": "Esc",
    "VK_TAB": "Tab", "VK_SPACE": "Space", "VK_INSERT": "Insert", "VK_HOME": "Home",
    "VK_END": "End", "VK_PRIOR": "PgUp", "VK_NEXT": "PgDn",
    "VK_UP": "↑", "VK_DOWN": "↓", "VK_LEFT": "←", "VK_RIGHT": "→",
    "VK_CAPITAL": "Caps", "VK_SNAPSHOT": "PrtSc", "VK_PAUSE": "Pause", "VK_SCROLL": "ScrLk",
    "VK_NUMLOCK": "NumLk", "VK_SHIFT": "Shift", "VK_CONTROL": "Ctrl", "VK_MENU": "Alt",
    "VK_LSHIFT": "L Shift", "VK_RSHIFT": "R Shift", "VK_LCONTROL": "L Ctrl",
    "VK_RCONTROL": "R Ctrl", "VK_LMENU": "L Alt", "VK_RMENU": "R Alt",
    "VK_LWIN": "Win", "VK_RWIN": "R Win", "VK_APPS": "Menu",
    "VK_ADD": "Num +", "VK_SUBTRACT": "Num -", "VK_MULTIPLY": "Num *", "VK_DIVIDE": "Num /",
    "VK_DECIMAL": "Num .",
}
for _n in range(10):
    VK_LABELS["VK_NUMPAD%d" % _n] = "Num %d" % _n
for _n in range(1, 25):
    VK_LABELS["VK_F%d" % _n] = "F%d" % _n


def vk_label(name):
    """Keycap text for a VK name; blank stays blank."""
    if not name:
        return ""
    return VK_LABELS.get(name, name if len(name) == 1 else name.replace("VK_", "").title())


# ---------------------------------------------------------------- schema
# Every field the page owns. section/key are the ini names exactly as the DLL reads them.
# kind: key (VK name or blank) | toggle (on/off) | int (bounded integer)
# Defaults are the DLL's own (Settings.cpp), so the page can show "unset -> default".

def _f(section, key, kind, label, help, group, **extra):
    d = {"section": section, "key": key, "kind": kind, "label": label, "help": help, "group": group}
    d.update(extra)
    return d


K, A, T, M = "Keybinds", "Audio Keybindings", "Toggle Switches", "Mod Settings"

FIELDS = [
    # -- practice keys: the cluster that works live inside a song
    _f(K, "RRSpeedKey",         "key", "Speed up",            "Riff Repeater speed up by the step below (works past 100%).", "practice", default="R"),
    _f(K, "RRSpeedDownKey",     "key", "Speed down",          "Riff Repeater speed down by the step below.", "practice", default="VK_OEM_MINUS"),
    _f(K, "LoopStartKey",       "key", "Loop start",          "Set the loop start at the current position.", "practice", default="Y"),
    _f(K, "LoopEndKey",         "key", "Loop end",            "Set the loop end; the section repeats until cleared.", "practice", default="U"),
    _f(K, "LoopClearKey",       "key", "Clear loop",          "Drop both loop points. Ctrl + loop start/end also clears.", "practice", default="VK_OEM_5"),
    _f(K, "RewindKey",          "key", "Rewind",              "Jump back by Rewind distance. While paused, moves the resume point.", "practice", default="Z"),
    _f(K, "ForwardKey",         "key", "Forward",             "Jump forward by Forward distance. While paused, moves the resume point.", "practice", default="VK_DELETE"),
    _f(K, "PauseSongKey",       "key", "Pause / resume",      "Freeze the song in place, no menu. Press again to resume.", "practice", default="P"),
    _f(A, "ToggleAmpSourceKey", "key", "Game amp / pedal only", "Mute the game's guitar tone so only your pedal is heard. Backing track keeps playing.", "practice", default="VK_OEM_7"),

    # -- the rest of the stock keybinds (all blank on this install)
    _f(K, "ToggleLoftKey",         "key", "Toggle loft",          "Show/hide the venue. ToggleLoft below must be on.", "other", default="T"),
    _f(K, "ShowSongTimerKey",      "key", "Song timer",           "Toggle the song timer overlay.", "other", default="N"),
    _f(K, "ForceReEnumerationKey", "key", "Re-enumerate songs",   "Only used when ForceReEnumeration is set to manual.", "other", default="F"),
    _f(K, "RainbowStringsKey",     "key", "Rainbow strings",      "Twitch-era visual; off here.", "other", default="V"),
    _f(K, "RainbowNotesKey",       "key", "Rainbow notes",        "Twitch-era visual; off here.", "other", default="N"),
    _f(K, "RemoveLyricsKey",       "key", "Remove lyrics",        "Only used when RemoveLyricsWhen is manual.", "other", default="L"),
    _f(K, "TuningOffsetKey",       "key", "Tuning offset",        "Only used with AutoTuneForSong.", "other", default="O"),
    _f(K, "ToggleExtendedRangeKey","key", "Extended range",       "Toggle extended-range mode.", "other", default="E"),
    _f(A, "MasterVolumeKey",       "key", "Master volume",        "Volume-control mod; VolumeControl must be on.", "audio", default=""),
    _f(A, "SongVolumeKey",         "key", "Song volume",          "", "audio", default=""),
    _f(A, "Player1VolumeKey",      "key", "Player 1 volume",      "", "audio", default=""),
    _f(A, "Player2VolumeKey",      "key", "Player 2 volume",      "", "audio", default=""),
    _f(A, "MicrophoneVolumeKey",   "key", "Microphone volume",    "", "audio", default=""),
    _f(A, "VoiceOverVolumeKey",    "key", "Voice-over volume",    "", "audio", default=""),
    _f(A, "SFXVolumeKey",          "key", "SFX volume",           "", "audio", default=""),
    _f(A, "DisplayMixerKey",       "key", "Show mixer",           "", "audio", default=""),
    _f(A, "MutePlayer1Key",        "key", "Mute player 1",        "", "audio", default=""),
    _f(A, "MutePlayer2Key",        "key", "Mute player 2",        "", "audio", default=""),

    # -- overlay
    _f(T, "DisplayCurrentAccuracy", "toggle", "Accuracy %",       "Live hit % under the song timer (Learn A Song and Score Attack).", "overlay", default="on"),
    _f(T, "DisplayNoteStreak",      "toggle", "Note streak",      "\"12 in a row, best 37\" under the accuracy line.", "overlay", default="on"),
    _f(T, "DisplayLoopPasses",      "toggle", "Loop passes",      "Pass counter with per-pass % while a loop is set.", "overlay", default="on"),
    _f(T, "ShowSongTimer",          "toggle", "Song timer",       "The timer overlay itself.", "overlay", default="off"),
    _f(T, "ShowCurrentNoteOnScreen","toggle", "Current note",     "Show the note being detected.", "overlay", default="off"),
    _f(T, "ToggleLoft",             "toggle", "Hide the loft",    "Removal switch: on means the venue is gone (ToggleLoftWhen = song).", "overlay", default="on"),

    # -- practice switches: these gate the keys above
    _f(T, "AllowLooping",           "toggle", "Looping",          "Off and the loop keys do nothing.", "switches", default="off"),
    _f(T, "AllowRewind",            "toggle", "Rewind / forward", "Off and the rewind, forward and scrub keys do nothing.", "switches", default="off"),
    _f(T, "RRSpeedAboveOneHundred", "toggle", "Speed past 100%",  "Lets the speed keys go above real tempo.", "switches", default="off"),
    _f(T, "LinearRiffRepeater",     "toggle", "Honest speed %",   "Stock Rocksmith's 68% is really 50%; on makes the number true.", "switches", default="off"),
    _f(T, "PreventMidSongPause",    "toggle", "No pause on Alt-Tab", "Tabbing away mid-song no longer pauses it. Off = stock behaviour.", "switches", default="off"),
    _f(T, "VolumeControl",          "toggle", "Volume keys",      "Enables the audio keybinds group.", "switches", default="off"),

    # -- tunables
    _f(M, "RewindBy",        "int", "Rewind distance",   "How far the rewind key jumps.", "tunables", unit="ms", min=0, max=60000, default="0"),
    _f(M, "ForwardBy",       "int", "Forward distance",  "How far the forward key jumps.", "tunables", unit="ms", min=0, max=60000, default="5000"),
    _f(M, "RRSpeedInterval", "int", "Speed step",        "Per press of the speed keys.", "tunables", unit="%", min=1, max=50, default="0"),
    _f(M, "LoopingLeadUp",   "int", "Loop run-in",       "Played before the loop start on every pass. 0 for a hard cut.", "tunables", unit="ms", min=0, max=10000, default="0"),
]

GROUPS = [
    ("practice", "Practice keys", "Work live inside a song. One key each, no modifier."),
    ("switches", "Practice switches", "These gate the keys above."),
    ("tunables", "Tunables", ""),
    ("overlay", "Overlay", "What is drawn on screen while you play."),
    ("other", "Other keybinds", "Stock RSMods keys. Blank means unbound."),
    ("audio", "Audio keybinds", "Only active with Volume keys on."),
]

FIELD_INDEX = {(f["section"].lower(), f["key"].lower()): f for f in FIELDS}


def field_id(f):
    return "%s/%s" % (f["section"], f["key"])


def lookup(fid):
    """'Section/Key' -> field dict, or None if the page does not own it."""
    if "/" not in fid:
        return None
    section, key = fid.split("/", 1)
    return FIELD_INDEX.get((section.lower(), key.lower()))


def validate(f, value):
    """Return an error string, or None if value is acceptable for field f."""
    if not isinstance(value, str):
        return "must be text"
    v = value.strip()
    if f["kind"] == "key":
        if v and v not in VK_NAMES:
            return "%s is not a key name the DLL knows" % v
    elif f["kind"] == "toggle":
        if v not in ("on", "off"):
            return "must be on or off"
    elif f["kind"] == "int":
        try:
            n = int(v)
        except ValueError:
            return "must be a whole number"
        if n < f["min"] or n > f["max"]:
            return "must be between %d and %d" % (f["min"], f["max"])
    return None


# ---------------------------------------------------------------- ini text

_KEY_LINE = re.compile(r"^(\s*[^=;#\[\]]+?\s*=)(\s*)(.*)$")


def _split(text):
    """Lines with their own endings, so a join reproduces the text exactly."""
    return text.splitlines(keepends=True)


def _body_eol(line):
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n"):
        return line[:-1], "\n"
    return line, ""


def _section_of(body):
    s = body.strip()
    if s.startswith("[") and s.endswith("]"):
        return s[1:-1].strip()
    return None


def _file_eol(text):
    return "\r\n" if "\r\n" in text else "\n"


def read_all(text):
    """{(section_lower, key_lower): value} for every key line in the text."""
    out = {}
    section = ""
    for line in _split(text):
        body, _ = _body_eol(line)
        name = _section_of(body)
        if name is not None:
            section = name.lower()
            continue
        m = _KEY_LINE.match(body)
        if m:
            key = m.group(1)[:-1].strip().lower()
            out[(section, key)] = m.group(3)
    return out


def get(text, section, key, default=None):
    return read_all(text).get((section.lower(), key.lower()), default)


def set_values(text, changes):
    """Return text with each (section, key) -> value applied in place.

    Existing lines keep their exact `key =` prefix and the whitespace after
    the `=`, so `RewindKey = ` stays in that style whether it gets a value or
    goes back to blank. A key missing from its section is appended at the end
    of that section, before any trailing blank lines, using the file's own
    line ending. A missing section is appended at the end of the file.
    """
    pending = {(s.lower(), k.lower()): (s, k, v) for (s, k), v in changes.items()}
    lines = _split(text)
    eol = _file_eol(text)

    # Pass 1: replace in place.
    section = ""
    for i, line in enumerate(lines):
        body, end = _body_eol(line)
        name = _section_of(body)
        if name is not None:
            section = name.lower()
            continue
        m = _KEY_LINE.match(body)
        if not m:
            continue
        key = m.group(1)[:-1].strip().lower()
        hit = pending.pop((section, key), None)
        if hit is None:
            continue
        prefix, sep, _old = m.groups()
        if not sep:
            sep = " " if prefix.endswith(" =") or " = " in prefix else ""
        lines[i] = prefix + sep + hit[2] + end

    # Pass 2: append anything that was not there.
    for (sec_l, _key_l), (sec, key, value) in pending.items():
        # Find the section's line range.
        start = None
        for i, line in enumerate(lines):
            name = _section_of(_body_eol(line)[0])
            if name is not None and name.lower() == sec_l:
                start = i
                break
        new_line = "%s = %s%s" % (key, value, eol)
        if start is None:
            if lines and not lines[-1].endswith(("\n",)):
                lines[-1] += eol
            lines.append("[%s]%s" % (sec, eol))
            lines.append(new_line)
            continue
        end = len(lines)
        for j in range(start + 1, len(lines)):
            if _section_of(_body_eol(lines[j])[0]) is not None:
                end = j
                break
        insert_at = end
        while insert_at - 1 > start and _body_eol(lines[insert_at - 1])[0].strip() == "":
            insert_at -= 1
        if not lines[insert_at - 1].endswith("\n"):
            lines[insert_at - 1] += eol
        lines.insert(insert_at, new_line)

    return "".join(lines)


def unified_diff(a_text, b_text, a_name, b_name):
    return "".join(difflib.unified_diff(
        a_text.splitlines(keepends=True), b_text.splitlines(keepends=True),
        fromfile=a_name, tofile=b_name))


# ---------------------------------------------------------------- paths

def find_repo(here):
    r"""Locate the rock_mod_arp checkout (the folder holding config\RSMods.ini)."""
    candidates = [
        os.environ.get("ROCK_MOD_ARP"),
        os.path.dirname(here),                          # running from <repo>\SongManager
        os.path.join(os.path.expanduser("~"), "rock_mod_arp"),
    ]
    for c in candidates:
        if c and os.path.isfile(os.path.join(c, "config", "RSMods.ini")):
            return os.path.abspath(c)
    return None


class Paths:
    def __init__(self, game, repo):
        self.game = game
        self.repo = repo
        self.game_ini = os.path.join(game, "RSMods.ini")
        self.repo_ini = os.path.join(repo, "config", "RSMods.ini") if repo else None
        self.dll_installed = os.path.join(game, "xinput1_3.dll")
        self.dll_built = os.path.join(repo, "RSMods-src", "Installer", "Resources", "xinput1_3.dll") if repo else None
        self.debug_log = os.path.join(game, "RSMods_debug.txt")
        self.rocksmith_ini = os.path.join(game, "Rocksmith.ini")
        self.rsasio_ini = os.path.join(game, "RS_ASIO.ini")
        self.keymap_script = os.path.join(repo, "docs", "keymap-wooting-80he.py") if repo else None
        self.keymap_png = os.path.join(repo, "docs", "keymap-wooting-80he.png") if repo else None


# ---------------------------------------------------------------- files

def read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def read_text(path):
    return read_bytes(path).decode("utf-8", "replace")


def write_bytes_atomic(path, data):
    tmp = path + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, path)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _file_info(path):
    if not path or not os.path.isfile(path):
        return None
    st = os.stat(path)
    return {"path": path, "sha256": sha256(path), "size": st.st_size,
            "mtime": time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime))}


def _tail(path, n):
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError:
        return []
    lines = data.decode("utf-8", "replace").splitlines()
    return lines[-n:]


def _first_line(path):
    try:
        with open(path, "rb") as fh:
            return fh.readline().decode("utf-8", "replace").strip()
    except OSError:
        return None


def current_values(p):
    """Values of every owned field from the game copy, plus whether each line exists."""
    text = read_text(p.game_ini)
    have = read_all(text)
    values = {}
    for f in FIELDS:
        v = have.get((f["section"].lower(), f["key"].lower()))
        values[field_id(f)] = {"value": v.strip() if v is not None else None,
                               "present": v is not None}
    return values


def sync_state(p):
    """Compare the game ini with the repo snapshot byte-for-byte."""
    if not p.repo_ini or not os.path.isfile(p.repo_ini):
        return {"repoFound": False, "inSync": None, "diff": ""}
    a, b = read_bytes(p.game_ini), read_bytes(p.repo_ini)
    if a == b:
        return {"repoFound": True, "inSync": True, "diff": ""}
    return {"repoFound": True, "inSync": False,
            "diff": unified_diff(a.decode("utf-8", "replace"), b.decode("utf-8", "replace"),
                                 "game\\RSMods.ini", "repo\\config\\RSMods.ini")}


def status(p):
    installed = _file_info(p.dll_installed)
    built = _file_info(p.dll_built)
    if not installed:
        dll_state = "no-install"
    elif not built:
        dll_state = "no-build"
    elif installed["sha256"] == built["sha256"]:
        dll_state = "match"
    else:
        dll_state = "stale"

    rs = read_text(p.rocksmith_ini) if os.path.isfile(p.rocksmith_ini) else ""
    asio = None
    if os.path.isfile(p.rsasio_ini):
        t = read_text(p.rsasio_ini)
        asio = {
            "enabled": get(t, "Config", "EnableAsio", ""),
            "bufferSizeMode": get(t, "Asio", "BufferSizeMode", ""),
            "customBufferSize": get(t, "Asio", "CustomBufferSize", ""),
            "inputDriver": get(t, "Asio.Input.0", "Driver", ""),
            "outputDriver": get(t, "Asio.Output", "Driver", ""),
        }
    return {
        "installed": installed,
        "built": built,
        "dllState": dll_state,
        "version": _first_line(p.debug_log),
        "logTail": _tail(p.debug_log, 10),
        "latencyBuffer": get(rs, "Audio", "LatencyBuffer", None),
        "asio": asio,
        "repo": p.repo,
        "keymapPng": bool(p.keymap_png and os.path.isfile(p.keymap_png)),
    }


# ---------------------------------------------------------------- apply

def apply(p, changes):
    """Validate and write `changes` ({'Section/Key': value}) to both ini copies.

    Returns a dict with ok, and either the written paths or an error (plus a
    diff when the two copies had drifted apart before the edit).
    """
    errors = {}
    typed = {}
    for fid, value in changes.items():
        f = lookup(fid)
        if f is None:
            errors[fid] = "not a setting this page owns"
            continue
        err = validate(f, value)
        if err:
            errors[fid] = err
            continue
        typed[(f["section"], f["key"])] = value.strip()
    if errors:
        return {"ok": False, "error": "some values were rejected", "fieldErrors": errors}
    if not typed:
        return {"ok": True, "wrote": [], "changed": []}

    sync = sync_state(p)
    if sync["repoFound"] and not sync["inSync"]:
        return {"ok": False, "error": "The game's RSMods.ini and the repo snapshot differ. "
                                      "Resolve that first so the two cannot drift.",
                "diff": sync["diff"]}

    before = read_bytes(p.game_ini)
    after = set_values(before.decode("utf-8"), typed).encode("utf-8")
    wrote = []
    if after != before:
        write_bytes_atomic(p.game_ini, after)
        wrote.append(p.game_ini)
        if sync["repoFound"]:
            write_bytes_atomic(p.repo_ini, after)
            wrote.append(p.repo_ini)
    return {"ok": True, "wrote": wrote,
            "changed": ["%s/%s" % k for k in typed]}


def resync(p, source):
    """Copy one ini over the other. source is 'game' or 'repo'."""
    if not p.repo_ini or not os.path.isfile(p.repo_ini):
        return {"ok": False, "error": "repo snapshot not found"}
    if source == "game":
        write_bytes_atomic(p.repo_ini, read_bytes(p.game_ini))
    elif source == "repo":
        write_bytes_atomic(p.game_ini, read_bytes(p.repo_ini))
    else:
        return {"ok": False, "error": "source must be game or repo"}
    return {"ok": True}


def regenerate_keymap(p):
    r"""Re-draw docs\keymap-wooting-80he.png from the current ini. Needs Pillow."""
    if not p.keymap_script or not os.path.isfile(p.keymap_script):
        return {"ran": False, "ok": False, "output": "keymap script not found in the repo"}
    try:
        r = subprocess.run(
            [sys.executable, p.keymap_script, "--ini", p.repo_ini or p.game_ini],
            capture_output=True, text=True, timeout=90, cwd=os.path.dirname(p.keymap_script),
        )
        out = (r.stdout + r.stderr).strip()
        return {"ran": True, "ok": r.returncode == 0, "output": out[-2000:]}
    except Exception as exc:  # noqa: BLE001 - surfaced to the page as text
        return {"ran": True, "ok": False, "output": str(exc)}
