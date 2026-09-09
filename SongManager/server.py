r"""Rocksmith song manager - local web app.

Serves a small UI on 127.0.0.1 that lists every song package in dlc\ and
dlc_disabled\, and moves files between the two folders so you can decide what
the game enumerates before you launch it.

Nothing is ever deleted: disabling a song moves the .psarc one folder sideways.
Your profile keeps its scores either way - re-enable and they come back.
"""

import http.server
import json
import os
import socket
import socketserver
import subprocess
import sys
import threading
import time
import traceback
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import psarc  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(HERE)
DLC = os.path.join(GAME, "dlc")
DISABLED = os.path.join(GAME, "dlc_disabled")
EXE = os.path.join(GAME, "Rocksmith2014.exe")
CACHE = os.path.join(HERE, "library.json")
SETLISTS = os.path.join(HERE, "setlists.json")

IDLE_TIMEOUT = 180  # seconds without a browser heartbeat before we shut down

state = {
    "scanning": False,
    "done": 0,
    "total": 0,
    "songs": {},        # filename -> metadata
    "error": None,
    "last_beat": time.time(),
    "scanned_at": None,
}
lock = threading.Lock()


# ---------------------------------------------------------------- scanning

def load_cache():
    try:
        with open(CACHE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def save_cache(songs):
    tmp = CACHE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(songs, fh)
    os.replace(tmp, CACHE)


def list_packages():
    """(filename, folder, enabled) for every psarc in either folder."""
    found = []
    for folder, enabled in ((DLC, True), (DISABLED, False)):
        if not os.path.isdir(folder):
            continue
        for name in os.listdir(folder):
            if name.lower().endswith(".psarc"):
                found.append((name, folder, enabled))
    return found


def scan(force=False):
    cache = {} if force else load_cache()
    packages = list_packages()

    with lock:
        state["scanning"] = True
        state["done"] = 0
        state["total"] = len(packages)
        state["error"] = None

    songs = {}
    for index, (name, folder, enabled) in enumerate(packages):
        path = os.path.join(folder, name)
        try:
            stat = os.stat(path)
            fingerprint = "%d:%d" % (stat.st_size, int(stat.st_mtime))
            hit = cache.get(name)
            if hit and hit.get("fingerprint") == fingerprint:
                meta = dict(hit)
            else:
                described = psarc.describe(path)
                if described is None:
                    described = {
                        "artist": "Unreadable package", "title": name,
                        "album": "", "year": None, "length": 0,
                        "arrangements": [], "tuning": "Unknown", "custom": False,
                        "author": None, "packageVersion": None, "appid": "",
                        "songKey": "", "bundle": False, "bundleCount": 1,
                    }
                meta = dict(described)
                meta["fingerprint"] = fingerprint
                meta["size"] = stat.st_size
            meta["file"] = name
            meta["enabled"] = enabled
            meta["size"] = stat.st_size
            songs[name] = meta
        except Exception:
            songs[name] = {
                "file": name, "enabled": enabled, "artist": "Failed to read",
                "title": name, "album": "", "year": None, "length": 0,
                "arrangements": [], "tuning": "Unknown", "custom": False,
                "author": None, "packageVersion": None, "appid": "",
                "songKey": "", "bundle": False, "bundleCount": 1,
                "size": 0, "fingerprint": "", "broken": True,
            }
        with lock:
            state["done"] = index + 1

    save_cache(songs)
    with lock:
        state["songs"] = songs
        state["scanning"] = False
        state["scanned_at"] = time.time()


def start_scan(force=False):
    with lock:
        if state["scanning"]:
            return
    threading.Thread(target=scan, kwargs={"force": force}, daemon=True).start()


# ---------------------------------------------------------------- actions

def game_is_running():
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Rocksmith2014.exe", "/NH"],
            capture_output=True, text=True, timeout=10,
        ).stdout
        return "Rocksmith2014.exe" in out
    except Exception:
        return False


def apply_changes(enable, disable):
    os.makedirs(DISABLED, exist_ok=True)
    moved = {"enabled": 0, "disabled": 0}
    failures = []

    for name in disable:
        src, dst = os.path.join(DLC, name), os.path.join(DISABLED, name)
        try:
            if os.path.exists(src):
                os.replace(src, dst)
                moved["disabled"] += 1
        except Exception as exc:
            failures.append({"file": name, "error": str(exc)})

    for name in enable:
        src, dst = os.path.join(DISABLED, name), os.path.join(DLC, name)
        try:
            if os.path.exists(src):
                os.replace(src, dst)
                moved["enabled"] += 1
        except Exception as exc:
            failures.append({"file": name, "error": str(exc)})

    stuck = {f["file"] for f in failures}
    moves = [(name, False) for name in disable] + [(name, True) for name in enable]

    with lock:
        for name, now_on in moves:
            if name in state["songs"] and name not in stuck:
                state["songs"][name]["enabled"] = now_on
        songs = dict(state["songs"])

    # Fall back to what's on disk if this process never ran a scan, so a move
    # can never blank the metadata cache.
    if not songs:
        songs = load_cache()
        for name, now_on in moves:
            if name in songs and name not in stuck:
                songs[name]["enabled"] = now_on
    if songs:
        save_cache(songs)

    return {"moved": moved, "failures": failures}


def read_setlists():
    try:
        with open(SETLISTS, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def write_setlists(data):
    tmp = SETLISTS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    os.replace(tmp, SETLISTS)


# ---------------------------------------------------------------- http

class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def _send(self, code, body, content_type="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _guard(self):
        """Only accept requests that came from the loopback UI."""
        host = (self.headers.get("Host") or "").split(":")[0]
        if host not in ("127.0.0.1", "localhost"):
            self._send(403, {"error": "forbidden"})
            return False
        return True

    def do_GET(self):
        if not self._guard():
            return
        path = self.path.split("?")[0]
        try:
            if path in ("/", "/index.html"):
                with open(os.path.join(HERE, "ui.html"), "rb") as fh:
                    self._send(200, fh.read(), "text/html; charset=utf-8")
            elif path == "/api/library":
                with lock:
                    self._send(200, {
                        "scanning": state["scanning"],
                        "done": state["done"],
                        "total": state["total"],
                        "scannedAt": state["scanned_at"],
                        "gameRunning": False,
                        "songs": list(state["songs"].values()) if not state["scanning"] else [],
                    })
            elif path == "/api/setlists":
                self._send(200, read_setlists())
            elif path == "/api/status":
                with lock:
                    state["last_beat"] = time.time()
                self._send(200, {
                    "scanning": state["scanning"],
                    "done": state["done"],
                    "total": state["total"],
                    "gameRunning": game_is_running(),
                })
            else:
                self._send(404, {"error": "not found"})
        except Exception:
            self._send(500, {"error": traceback.format_exc()})

    def do_POST(self):
        if not self._guard():
            return
        path = self.path.split("?")[0]
        length = int(self.headers.get("Content-Length") or 0)
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            payload = {}

        try:
            if path == "/api/rescan":
                start_scan(force=bool(payload.get("force")))
                self._send(200, {"ok": True})
            elif path == "/api/apply":
                if game_is_running():
                    self._send(200, {
                        "ok": False,
                        "error": "Rocksmith is running. Close it first - the game holds "
                                 "the psarc files open and moves will fail.",
                    })
                    return
                result = apply_changes(payload.get("enable", []), payload.get("disable", []))
                result["ok"] = not result["failures"]
                self._send(200, result)
            elif path == "/api/launch":
                if not os.path.exists(EXE):
                    self._send(200, {"ok": False, "error": "Rocksmith2014.exe not found"})
                    return
                subprocess.Popen([EXE], cwd=GAME, close_fds=True)
                self._send(200, {"ok": True})
            elif path == "/api/setlists":
                data = read_setlists()
                name = (payload.get("name") or "").strip()
                if not name:
                    self._send(200, {"ok": False, "error": "name required"})
                    return
                if payload.get("delete"):
                    data.pop(name, None)
                else:
                    data[name] = {
                        "files": payload.get("files", []),
                        "saved": time.strftime("%Y-%m-%d %H:%M"),
                    }
                write_setlists(data)
                self._send(200, {"ok": True, "setlists": data})
            elif path == "/api/quit":
                self._send(200, {"ok": True})
                threading.Thread(target=lambda: (time.sleep(0.4), os._exit(0)), daemon=True).start()
            else:
                self._send(404, {"error": "not found"})
        except Exception:
            self._send(500, {"error": traceback.format_exc()})


class Server(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


def watchdog():
    """Exit once the browser tab has been gone for a while."""
    while True:
        time.sleep(15)
        with lock:
            quiet = time.time() - state["last_beat"]
        if quiet > IDLE_TIMEOUT:
            os._exit(0)


def pick_port(preferred=8734):
    for port in range(preferred, preferred + 40):
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise SystemExit("no free port in range")


def main():
    if not os.path.isdir(DLC):
        raise SystemExit("dlc folder not found next to this script: %s" % DLC)
    os.makedirs(DISABLED, exist_ok=True)

    port = pick_port()
    start_scan()
    threading.Thread(target=watchdog, daemon=True).start()

    url = "http://127.0.0.1:%d/" % port
    print("Rocksmith Song Manager running at", url)
    print("Close the browser tab and this window shuts itself down.")
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()

    with Server(("127.0.0.1", port), Handler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    main()
