# Copyright (C) 2026 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
#
# API design and architecture by Hong Jen Yee (PCMan).
# Implementation generated with AI assistance from Google Antigravity (Gemini 3.8 Flash).
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

"""Unit tests for CinTableBase."""

import concurrent.futures
import os
import sys
import time
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python")))

from cinbase import CinTableBase


class CinTableBaseTests(unittest.TestCase):
    def test_initial_state(self):
        """Verify initial attribute values and default properties."""
        tbl = CinTableBase()
        self.assertIsNone(tbl.future)
        self.assertFalse(tbl.loading)
        self.assertIsNone(tbl.cin)
        self.assertIsNone(tbl.wait(timeout=0.01))

    def test_future_lifecycle(self):
        """Verify dynamic loading and cin access through Future lifecycle."""
        tbl = CinTableBase()
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        started = False

        def slow_task():
            nonlocal started
            started = True
            time.sleep(0.05)
            return "ready"

        fut = executor.submit(slow_task)
        tbl.future = fut

        self.assertIs(tbl.future, fut)
        self.assertTrue(tbl.loading)
        self.assertIsNone(tbl.cin)

        # wait() awaits completion
        res = tbl.wait(timeout=1.0)
        self.assertEqual(res, "ready")
        self.assertFalse(tbl.loading)
        self.assertEqual(tbl.cin, "ready")

        executor.shutdown(wait=False)

    def test_wait_timeout(self):
        """Verify wait() times out and raises TimeoutError when timeout expires."""
        tbl = CinTableBase()
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        def very_slow_task():
            time.sleep(0.5)
            return "done"

        tbl.future = executor.submit(very_slow_task)
        with self.assertRaises(concurrent.futures.TimeoutError):
            tbl.wait(timeout=0.01)
        self.assertTrue(tbl.loading)

        executor.shutdown(wait=False)

    def test_wait_raises_task_exception(self):
        """Verify wait() and cin propagate exceptions raised inside the task."""
        tbl = CinTableBase()
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        def failing_task():
            raise ValueError("Corrupt CIN table file")

        tbl.future = executor.submit(failing_task)
        with self.assertRaises(ValueError) as ctx:
            tbl.wait(timeout=1.0)
        self.assertIn("Corrupt CIN table file", str(ctx.exception))

        with self.assertRaises(ValueError):
            _ = tbl.cin

        executor.shutdown(wait=False)

    def test_no_setters(self):
        """Verify loading and cin properties cannot be assigned directly."""
        tbl = CinTableBase()
        with self.assertRaises(AttributeError):
            tbl.loading = True
        with self.assertRaises(AttributeError):
            tbl.cin = "custom"


if __name__ == "__main__":
    unittest.main()
