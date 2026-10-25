#!/usr/bin/env python3
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import keycodes

class TestKeycodesBitmasks(unittest.TestCase):
    def test_bitmask_constants(self):
        # Per Windows SDK GetKeyState / GetAsyncKeyState documentation:
        # High-order bit (0x8000) indicates whether key is down.
        # Low-order bit (0x0001) indicates toggle state (GetKeyState) or
        # whether key was pressed after previous call (GetAsyncKeyState).
        self.assertEqual(keycodes.KEY_STATE_DOWN, 0x8000)
        self.assertEqual(keycodes.KEY_STATE_TOGGLED, 0x0001)
        self.assertEqual(keycodes.KEY_STATE_WAS_PRESSED, 0x0001)
        self.assertEqual(keycodes.KEY_PRESSED_MASK, 0x8001)

    def test_simulated_key_states(self):
        # When key is currently down, GetAsyncKeyState / GetKeyState sets bit 15 (0x8000).
        # In a 16-bit signed SHORT, this value is negative (-32768 or -32767).
        down_short = -32768
        down_and_recent_short = -32767
        recent_only_short = 1
        up_short = 0

        # Legacy check (val >= 1) failed for held keys because of signed negative SHORT:
        self.assertFalse(down_short >= 1)

        # Mask checks:
        self.assertTrue(bool(down_short & keycodes.KEY_PRESSED_MASK))
        self.assertTrue(bool(down_and_recent_short & keycodes.KEY_PRESSED_MASK))
        self.assertTrue(bool(recent_only_short & keycodes.KEY_PRESSED_MASK))
        self.assertFalse(bool(up_short & keycodes.KEY_PRESSED_MASK))

        # Toggle state check:
        self.assertTrue(bool(1 & keycodes.KEY_STATE_TOGGLED))
        self.assertFalse(bool(0 & keycodes.KEY_STATE_TOGGLED))

if __name__ == '__main__':
    unittest.main()
