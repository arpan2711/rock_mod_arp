r"""Tests for the RSMods.ini writer. Run:  py -3 SongManager\test_rsmods_ini.py

The one that matters: writing every owned key back with its current value must
reproduce config\RSMods.ini byte-for-byte, CRLF and all.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rsmods_ini as ini  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT = os.path.join(REPO, "config", "RSMods.ini")


class RoundTrip(unittest.TestCase):
    def setUp(self):
        with open(SNAPSHOT, "rb") as fh:
            self.raw = fh.read()
        self.text = self.raw.decode("utf-8")

    def test_snapshot_is_crlf(self):
        self.assertIn(b"\r\n", self.raw)
        self.assertNotIn(b"\r\r", self.raw)

    def test_rewrite_every_owned_key_is_identity(self):
        have = ini.read_all(self.text)
        changes = {}
        for f in ini.FIELDS:
            v = have.get((f["section"].lower(), f["key"].lower()))
            if v is not None:
                changes[(f["section"], f["key"])] = v
        out = ini.set_values(self.text, changes)
        self.assertEqual(out.encode("utf-8"), self.raw)

    def test_no_changes_is_identity(self):
        self.assertEqual(ini.set_values(self.text, {}), self.text)

    def test_single_change_touches_one_line(self):
        out = ini.set_values(self.text, {("Keybinds", "RewindKey"): "VK_HOME"})
        a, b = self.text.splitlines(True), out.splitlines(True)
        self.assertEqual(len(a), len(b))
        diffs = [(x, y) for x, y in zip(a, b) if x != y]
        self.assertEqual(diffs, [("RewindKey = VK_BACK\r\n", "RewindKey = VK_HOME\r\n")])

    def test_blank_keeps_trailing_space_style(self):
        out = ini.set_values(self.text, {("Keybinds", "PauseSongKey"): ""})
        self.assertIn("PauseSongKey = \r\n", out)

    def test_fill_a_blank_key(self):
        out = ini.set_values(self.text, {("Keybinds", "ToggleLoftKey"): "T"})
        self.assertIn("ToggleLoftKey = T\r\n", out)
        self.assertNotIn("ToggleLoftKey = \r\n", out)

    def test_missing_key_is_appended_to_its_section(self):
        self.assertIsNone(ini.get(self.text, "Toggle Switches", "PreventMidSongPause"))
        out = ini.set_values(self.text, {("Toggle Switches", "PreventMidSongPause"): "on"})
        lines = out.splitlines(True)
        i = lines.index("PreventMidSongPause = on\r\n")
        # Directly before the next section header, i.e. still inside [Toggle Switches].
        self.assertEqual(lines[i + 1], "[String Colors]\r\n")
        self.assertEqual(lines[i - 1], "UseCustomNSPTimer = off\r\n")
        # Nothing else moved.
        self.assertEqual(len(lines), len(self.text.splitlines(True)) + 1)

    def test_key_match_is_case_insensitive_but_keeps_spelling(self):
        out = ini.set_values(self.text, {("keybinds", "rewindkey"): "VK_END"})
        self.assertIn("RewindKey = VK_END\r\n", out)


class LfAndStyles(unittest.TestCase):
    def test_lf_file_stays_lf(self):
        text = "[Keybinds]\nRewindKey = Z\n[Mod Settings]\nRewindBy=0\n"
        out = ini.set_values(text, {("Keybinds", "RewindKey"): "VK_BACK",
                                    ("Mod Settings", "RewindBy"): "5000"})
        self.assertEqual(out, "[Keybinds]\nRewindKey = VK_BACK\n[Mod Settings]\nRewindBy=5000\n")

    def test_append_before_trailing_blank_lines(self):
        text = "[A]\r\nx = 1\r\n\r\n\r\n[B]\r\ny = 2\r\n"
        out = ini.set_values(text, {("A", "new"): "v"})
        self.assertEqual(out, "[A]\r\nx = 1\r\nnew = v\r\n\r\n\r\n[B]\r\ny = 2\r\n")

    def test_append_at_eof_without_trailing_newline(self):
        text = "[A]\r\nx = 1"
        out = ini.set_values(text, {("A", "new"): "v"})
        self.assertEqual(out, "[A]\r\nx = 1\r\nnew = v\r\n")

    def test_missing_section_is_created(self):
        text = "[A]\r\nx = 1\r\n"
        out = ini.set_values(text, {("Z", "k"): "v"})
        self.assertEqual(out, "[A]\r\nx = 1\r\n[Z]\r\nk = v\r\n")

    def test_comments_and_unknown_lines_untouched(self):
        text = "; hello\r\n[A]\r\n# note\r\nx = 1 ; trailing\r\nweird line\r\n"
        out = ini.set_values(text, {("A", "x"): "2"})
        self.assertEqual(out, "; hello\r\n[A]\r\n# note\r\nx = 2\r\nweird line\r\n")


class Validation(unittest.TestCase):
    def f(self, key):
        for f in ini.FIELDS:
            if f["key"] == key:
                return f
        raise KeyError(key)

    def test_keys(self):
        self.assertIsNone(ini.validate(self.f("RewindKey"), ""))
        self.assertIsNone(ini.validate(self.f("RewindKey"), "VK_BACK"))
        self.assertIsNone(ini.validate(self.f("RewindKey"), "P"))
        self.assertIsNotNone(ini.validate(self.f("RewindKey"), "VK_BACKSPACE"))
        self.assertIsNotNone(ini.validate(self.f("RewindKey"), "p"))

    def test_toggles_and_ints(self):
        self.assertIsNone(ini.validate(self.f("AllowLooping"), "on"))
        self.assertIsNotNone(ini.validate(self.f("AllowLooping"), "yes"))
        self.assertIsNone(ini.validate(self.f("RewindBy"), "5000"))
        self.assertIsNotNone(ini.validate(self.f("RewindBy"), "-1"))
        self.assertIsNotNone(ini.validate(self.f("RRSpeedInterval"), "0"))

    def test_lookup_rejects_unowned(self):
        self.assertIsNone(ini.lookup("Toggle Switches/ProfileToLoad"))
        self.assertIsNotNone(ini.lookup("toggle switches/allowlooping"))

    def test_vk_table_size_matches_settings_hpp(self):
        self.assertEqual(len(ini.VK_NAMES), 175)


if __name__ == "__main__":
    unittest.main(verbosity=1)
