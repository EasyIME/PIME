#!/usr/bin/env python3
import sys
import os
import unittest
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from cinbase import LoadCinTable, LoadRCinTable, LoadHCinTable
from input_methods.chepinyin.chepinyin_ime import CinTable, RCinTable, HCinTable

class TestCinBaseLoadingEvent(unittest.TestCase):
    def test_loaded_event_initial_state(self):
        self.assertFalse(CinTable.loading)
        self.assertTrue(CinTable.loaded_event.is_set())
        self.assertFalse(RCinTable.loading)
        self.assertTrue(RCinTable.loaded_event.is_set())
        self.assertFalse(HCinTable.loading)
        self.assertTrue(HCinTable.loaded_event.is_set())

    def test_loaded_event_synchronization(self):
        event = CinTable.loaded_event
        # Simulate background load
        CinTable.loading = True
        event.clear()

        unblocked = []

        def waiter():
            event.wait()
            unblocked.append(True)

        t = threading.Thread(target=waiter)
        t.start()

        # Small sleep to ensure waiter is waiting
        time.sleep(0.05)
        self.assertEqual(len(unblocked), 0)

        # Signal completion
        CinTable.loading = False
        event.set()
        t.join(timeout=1.0)

        self.assertEqual(len(unblocked), 1)
        self.assertTrue(unblocked[0])

if __name__ == '__main__':
    unittest.main()
