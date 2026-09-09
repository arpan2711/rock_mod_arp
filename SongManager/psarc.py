"""Minimal read-only PSARC reader for Rocksmith 2014 archives.

Pure standard library - no pip installs. Only the table of contents is
encrypted (AES-256-CFB, zero IV, the well-known archive key); the data blocks
inside are plain zlib, so reading a song's manifest is cheap.
"""

import json
import struct
import zlib

# --- minimal AES: only the forward block transform, which is all CFB decrypt needs ---

_SBOX = [
    0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
    0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
    0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
    0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
    0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
    0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
    0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
    0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
    0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
    0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
    0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
    0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
    0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
    0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
    0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
    0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16,
]
_RCON = [0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80,0x1b,0x36,0x6c,0xd8,0xab,0x4d]

ARC_KEY = bytes.fromhex(
    "C53DB23870A1A2F71CAE64061FDD0E1157309DC85204D4C5BFDF25090DF2572C"
)


def _xtime(a):
    a <<= 1
    if a & 0x100:
        a ^= 0x11B
    return a & 0xFF


def _expand_key(key):
    nk = len(key) // 4
    nr = nk + 6
    w = [list(key[4 * i:4 * i + 4]) for i in range(nk)]
    for i in range(nk, 4 * (nr + 1)):
        t = list(w[i - 1])
        if i % nk == 0:
            t = t[1:] + t[:1]
            t = [_SBOX[b] for b in t]
            t[0] ^= _RCON[i // nk - 1]
        elif nk > 6 and i % nk == 4:
            t = [_SBOX[b] for b in t]
        w.append([w[i - nk][j] ^ t[j] for j in range(4)])
    return w, nr


def _encrypt_block(block, w, nr):
    s = [list(block[i::4]) for i in range(4)]

    def add_round_key(rnd):
        for c in range(4):
            for r in range(4):
                s[r][c] ^= w[rnd * 4 + c][r]

    add_round_key(0)
    for rnd in range(1, nr + 1):
        for r in range(4):
            for c in range(4):
                s[r][c] = _SBOX[s[r][c]]
        for r in range(1, 4):
            s[r] = s[r][r:] + s[r][:r]
        if rnd != nr:
            for c in range(4):
                a = [s[r][c] for r in range(4)]
                t = a[0] ^ a[1] ^ a[2] ^ a[3]
                mixed = [a[r] ^ t ^ _xtime(a[r] ^ a[(r + 1) % 4]) for r in range(4)]
                for r in range(4):
                    s[r][c] = mixed[r]
        add_round_key(rnd)

    out = bytearray(16)
    for c in range(4):
        for r in range(4):
            out[4 * c + r] = s[r][c]
    return bytes(out)


def cfb_decrypt(data, key, iv=b"\0" * 16):
    w, nr = _expand_key(key)
    out = bytearray()
    prev = iv
    for i in range(0, len(data), 16):
        blk = data[i:i + 16]
        keystream = _encrypt_block(prev, w, nr)
        out += bytes(a ^ b for a, b in zip(blk, keystream))
        prev = blk + keystream[len(blk):]
    return bytes(out)


class Psarc:
    """A parsed PSARC. Entry 0 is always the filename manifest."""

    def __init__(self, path):
        with open(path, "rb") as fh:
            self.data = fh.read()
        if self.data[:4] != b"PSAR":
            raise ValueError("not a PSARC archive")
        (_magic, self.version, _comp, toc_len, _entry_size,
         count, self.block_size, self.flags) = struct.unpack(">4sI4sIIIII", self.data[:32])

        toc = cfb_decrypt(self.data[32:toc_len], ARC_KEY)
        self.entries = []
        for i in range(count):
            raw = toc[i * 30:(i + 1) * 30]
            self.entries.append((
                struct.unpack(">I", raw[16:20])[0],       # first block index
                int.from_bytes(raw[20:25], "big"),         # uncompressed length
                int.from_bytes(raw[25:30], "big"),         # offset into file
            ))

        table = toc[count * 30:]
        width = 2 if self.block_size == 65536 else (3 if self.block_size == 16777216 else 4)
        self.blocks = [
            int.from_bytes(table[i:i + width], "big")
            for i in range(0, len(table), width)
        ]
        self.names = [n.strip() for n in self.read(0).decode("utf-8", "replace").split("\n")]

    def read(self, index):
        first_block, length, offset = self.entries[index]
        out = bytearray()
        pos = offset
        block = first_block
        while len(out) < length:
            size = self.blocks[block]
            block += 1
            if size == 0:
                out += self.data[pos:pos + self.block_size]
                pos += self.block_size
            else:
                chunk = self.data[pos:pos + size]
                pos += size
                try:
                    out += zlib.decompress(chunk)
                except zlib.error:
                    out += chunk
        return bytes(out[:length])

    def find(self, suffix):
        """Indices into self.entries for files whose name ends with suffix."""
        return [i + 1 for i, name in enumerate(self.names) if name.endswith(suffix)]

    def read_text(self, suffix):
        hits = self.find(suffix)
        if not hits:
            return None
        return self.read(hits[0]).decode("utf-8", "replace")


# --- Rocksmith-specific helpers ---

TUNINGS = {
    (0, 0, 0, 0, 0, 0): "E Standard",
    (-1, -1, -1, -1, -1, -1): "Eb Standard",
    (-2, -2, -2, -2, -2, -2): "D Standard",
    (-3, -3, -3, -3, -3, -3): "C# Standard",
    (-4, -4, -4, -4, -4, -4): "C Standard",
    (-5, -5, -5, -5, -5, -5): "B Standard",
    (1, 1, 1, 1, 1, 1): "F Standard",
    (2, 2, 2, 2, 2, 2): "F# Standard",
    (-2, 0, 0, 0, 0, 0): "Drop D",
    (-3, -1, -1, -1, -1, -1): "Eb Drop Db",
    (-4, -2, -2, -2, -2, -2): "D Drop C",
    (-5, -3, -3, -3, -3, -3): "Db Drop B",
    (-6, -4, -4, -4, -4, -4): "C Drop Bb",
    (-7, -5, -5, -5, -5, -5): "B Drop A",
    (0, 0, 0, 0, 0, -2): "DADGAD-ish",
    (-2, -2, -2, -2, -2, -4): "Open D",
    (-2, 0, 0, 0, -2, -2): "Open G",
}

_ARR_ORDER = ["Lead", "Rhythm", "Combo", "Bass", "Vocals"]


def tuning_name(tuning):
    if not isinstance(tuning, dict):
        return "Unknown"
    key = tuple(int(tuning.get("string%d" % i, 0)) for i in range(6))
    if key in TUNINGS:
        return TUNINGS[key]
    return " ".join("%+d" % v if v else "0" for v in key)


def describe(path):
    """Pull the display metadata for one song package."""
    arc = Psarc(path)

    toolkit = arc.read_text("toolkit.version")
    appid = (arc.read_text("appid.appid") or "").strip()

    hsan_hits = arc.find(".hsan")
    if not hsan_hits:
        return None

    manifest = json.loads(arc.read(hsan_hits[0]).decode("utf-8", "replace"))
    entries = list(manifest.get("Entries", {}).values())
    if not entries:
        return None

    by_song = {}
    for entry in entries:
        attrs = entry.get("Attributes", {})
        key = attrs.get("SongKey") or attrs.get("DLCKey") or "?"
        slot = by_song.setdefault(key, {"arrangements": set(), "attrs": attrs})
        name = attrs.get("ArrangementName")
        if name:
            slot["arrangements"].add(name)
        # Prefer an entry that carries a real title over a sparse vocals entry.
        if attrs.get("SongName") and not slot["attrs"].get("SongName"):
            slot["attrs"] = attrs

    bundle = len(by_song) > 1
    first = next(iter(by_song.values()))
    attrs = first["attrs"]

    arrangements = set()
    for slot in by_song.values():
        arrangements |= slot["arrangements"]

    def order(name):
        return (_ARR_ORDER.index(name), name) if name in _ARR_ORDER else (99, name)

    author = None
    package_version = None
    if toolkit:
        for line in toolkit.splitlines():
            if line.startswith("Package Author:"):
                author = line.split(":", 1)[1].strip()
            elif line.startswith("Package Version:"):
                package_version = line.split(":", 1)[1].strip()

    return {
        "artist": attrs.get("ArtistName") or "Unknown artist",
        "title": attrs.get("SongName") or "Unknown title",
        "album": attrs.get("AlbumName") or "",
        "year": attrs.get("SongYear") or None,
        "length": round(float(attrs.get("SongLength") or 0), 1),
        "arrangements": sorted(arrangements, key=order),
        "tuning": tuning_name(attrs.get("Tuning")),
        "custom": toolkit is not None,
        "author": author,
        "packageVersion": package_version,
        "appid": appid,
        "songKey": attrs.get("SongKey") or attrs.get("DLCKey") or "",
        "bundle": bundle,
        "bundleCount": len(by_song) if bundle else 1,
    }
