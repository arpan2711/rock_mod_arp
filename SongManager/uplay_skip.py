r"""Dismiss the Uplay login dialog at Rocksmith startup.

RSMods 1.2.7.4 punches through the logos and profile select by spamming Enter,
but the Uplay dialog only closes on Escape - upstream fixed that in 1.2.8.x,
which this install can't run. So we send the Escape ourselves.

Watches for a window owned by Rocksmith2014.exe and, while it is the focused
window, taps Escape a few times across a bounded stretch of the startup. Only
ever sends to Rocksmith: if you alt-tab away, it stays quiet.

Tune these three if the timing is off for your machine:
"""

import ctypes
import ctypes.wintypes as wt
import sys
import time

START_AFTER = 6.0     # seconds to wait before the first Escape
STOP_AFTER = 50.0     # stop sending once startup should be well past
INTERVAL = 1.5        # seconds between taps

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
VK_ESCAPE = 0x1B
ESC_SCANCODE = 0x01
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002
INPUT_KEYBOARD = 1


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wt.WORD), ("wScan", wt.WORD), ("dwFlags", wt.DWORD),
                ("time", wt.DWORD), ("dwExtraInfo", ctypes.POINTER(wt.ULONG))]


class _INPUTunion(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("padding", ctypes.c_ubyte * 24)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wt.DWORD), ("u", _INPUTunion)]


def tap_escape():
    """Send a real Escape keypress. Scancode-level, so DirectInput sees it."""
    def event(flags):
        return INPUT(type=INPUT_KEYBOARD,
                     u=_INPUTunion(ki=KEYBDINPUT(0, ESC_SCANCODE, flags, 0, None)))

    events = (INPUT * 2)(event(KEYEVENTF_SCANCODE),
                         event(KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP))
    user32.SendInput(2, ctypes.byref(events), ctypes.sizeof(INPUT))


def process_name(pid):
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(512)
        size = wt.DWORD(512)
        if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            return buf.value.rsplit("\\", 1)[-1].lower()
        return ""
    finally:
        kernel32.CloseHandle(handle)


def rocksmith_is_focused():
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return False
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return process_name(pid.value) == "rocksmith2014.exe"


def main():
    print("Uplay skip: waiting %.0fs, then tapping Escape every %.1fs until %.0fs."
          % (START_AFTER, INTERVAL, STOP_AFTER))
    print("Only fires while Rocksmith is the focused window - alt-tab to silence it.")

    start = time.time()
    time.sleep(START_AFTER)
    sent = 0
    while time.time() - start < STOP_AFTER:
        if rocksmith_is_focused():
            tap_escape()
            sent += 1
        time.sleep(INTERVAL)
    print("Done - sent %d Escape taps." % sent)


if __name__ == "__main__":
    sys.exit(main())
