# Tests for the chewing tone menu (python/input_methods/chewing/tone_menu.py).
# Generated with assistance from Claude Code (Claude Opus 5.5).
import importlib.util
import os
import struct
import sys
import unittest


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
PYTHON_DIR = os.path.join(ROOT, "python")
if PYTHON_DIR not in sys.path:
    sys.path.insert(0, PYTHON_DIR)

spec = importlib.util.spec_from_file_location(
    "tone_menu_for_test", os.path.join(PYTHON_DIR, "input_methods", "chewing", "tone_menu.py"))
tone_menu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tone_menu)


class DefaultKeysTests(unittest.TestCase):
    # The new syllable is typed on the default layout, whatever layout the user picked,
    # so these keys must be the default layout's.
    def test_tone_marks_use_their_keys(self):
        self.assertEqual(tone_menu.default_keys("ㄅㄧˊ"), "1u6")
        self.assertEqual(tone_menu.default_keys("ㄅㄧˇ"), "1u3")
        self.assertEqual(tone_menu.default_keys("ㄅㄧˋ"), "1u4")
        self.assertEqual(tone_menu.default_keys("ㄅㄧ˙"), "1u7")

    def test_first_tone_ends_with_space(self):
        # The first tone has no mark; without the space the syllable is never finished.
        self.assertEqual(tone_menu.default_keys("ㄅㄧ"), "1u ")

    def test_menu_order_is_first_tone_to_neutral(self):
        labels = ["ㄅㄧ˙", "ㄅㄧˊ", "ㄅㄧˋ", "ㄅㄧ", "ㄅㄧˇ"]
        self.assertEqual(sorted(labels, key=tone_menu.tone_order),
                         ["ㄅㄧ", "ㄅㄧˊ", "ㄅㄧˇ", "ㄅㄧˋ", "ㄅㄧ˙"])


# chewing.dll is 32-bit; the bundled python that loads it is too.
@unittest.skipUnless(sys.platform == "win32" and struct.calcsize("P") == 4,
                     "needs the bundled 32-bit python to load chewing.dll")
class ToneMenuWithLibchewingTests(unittest.TestCase):
    def setUp(self):
        from libchewing import ChewingContext, CHEWING_DATA_DIR
        from libchewing.libchewing import _libchewing
        self.menu = tone_menu.ToneMenu(_libchewing, ChewingContext, CHEWING_DATA_DIR)
        self.ctx = ChewingContext(syspath=CHEWING_DATA_DIR.encode("UTF-8"),
                                  userpath=os.path.join(ROOT, "tests", "tone_menu_test.sqlite3").encode("UTF-8"))
        self.ctx.set_maxChiSymbolLen(50)
        self.ctx.set_ChiEngMode(1)
        self.ctx.set_KBType(1)  # 許氏: the menu must work on a layout other than the default
        for key in "bejbeed":  # ㄅㄧˋ ㄅㄧㄝˊ, which libchewing turns into 必別
            self.ctx.handle_Default(ord(key))

    def tearDown(self):
        del self.ctx
        path = os.path.join(ROOT, "tests", "tone_menu_test.sqlite3")
        if os.path.exists(path):
            os.remove(path)

    def buffer(self):
        return self.ctx.buffer_String().decode("UTF-8")

    def test_menu_lists_the_other_tones_that_have_characters(self):
        self.ctx.handle_Left()
        self.ctx.handle_Left()  # cursor on 必
        labels = self.menu.open(self.ctx)
        # ㄅㄧ˙ has no character, and ㄅㄧˋ is the current tone: neither is offered.
        self.assertEqual([label.split()[0] for label in labels], ["ㄅㄧ", "ㄅㄧˊ", "ㄅㄧˇ"])

    def test_choosing_a_tone_replaces_only_that_character(self):
        self.ctx.handle_Left()
        self.ctx.handle_Left()
        labels = self.menu.open(self.ctx)
        self.assertTrue(self.menu.choose(self.ctx, labels.index("ㄅㄧˊ 鼻"), 1))
        self.assertEqual(self.buffer(), "鼻別")
        self.assertEqual(self.ctx.cursor_Current(), 0)  # the cursor stays where it was
        self.assertFalse(self.menu.is_open())

    def test_a_second_menu_is_not_polluted_by_the_first(self):
        # 2026-10-15: the lookup context kept earlier syllables, so a later
        # lookup returned a wrong character (ㄅㄧ˙ showed 逼).
        self.ctx.handle_Left()
        self.ctx.handle_Left()
        first = self.menu.open(self.ctx)
        self.menu.close()
        self.assertEqual(self.menu.open(self.ctx), first)

    def test_a_first_tone_character_does_not_list_the_first_tone(self):
        # The first tone is stored as 0; listing 5 too showed it twice (2026-10-15).
        self.ctx.set_escCleanAllBuf(1)
        self.ctx.handle_Esc()  # start over with an empty buffer
        self.ctx.set_KBType(0)
        for key in "1u ":  # ㄅㄧ -> 逼
            self.ctx.handle_Default(ord(key))
        labels = self.menu.open(self.ctx)
        self.assertEqual([label.split()[0] for label in labels], ["ㄅㄧˊ", "ㄅㄧˇ", "ㄅㄧˋ"])

    def test_at_the_end_the_menu_is_for_the_last_character(self):
        labels = self.menu.open(self.ctx)  # cursor after 別, as after typing
        self.assertTrue(all(label.startswith("ㄅㄧㄝ") for label in labels))


if __name__ == "__main__":
    unittest.main()
