"""The chewing binding must fail loudly instead of running on a NULL context.

Generated with assistance from omp (deepseek-v4.1-flash).
"""

import gc
import os
import sys
import unittest
from unittest import mock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
sys.path.insert(0, os.path.join(ROOT, "python"))

try:
    from libchewing import libchewing as libchewing_impl
except OSError:  # the system libchewing is not installed
    libchewing_impl = None


@unittest.skipIf(libchewing_impl is None, "system libchewing is unavailable")
class ChewingContextTest(unittest.TestCase):
    def test_null_context_raises_instead_of_swallowing_keys(self):
        fake = mock.Mock()
        fake.chewing_new2.return_value = 0

        with mock.patch.object(libchewing_impl, "_libchewing", fake):
            with self.assertRaises(RuntimeError) as raised:
                libchewing_impl.ChewingContext(syspath=b"/data", userpath=b"/user")

        self.assertIn("chewing_new2() returned NULL", str(raised.exception))

    def test_null_context_is_never_deleted(self):
        fake = mock.Mock()
        fake.chewing_new2.return_value = 0

        with mock.patch.object(libchewing_impl, "_libchewing", fake):
            with self.assertRaises(RuntimeError):
                libchewing_impl.ChewingContext(syspath=b"/data", userpath=b"/user")
            gc.collect()

        fake.chewing_delete.assert_not_called()

    def test_valid_context_is_deleted_once(self):
        fake = mock.Mock()
        fake.chewing_new2.return_value = 4321

        with mock.patch.object(libchewing_impl, "_libchewing", fake):
            context = libchewing_impl.ChewingContext(syspath=b"/data", userpath=b"/user")
            self.assertEqual(context.ctx, 4321)
            del context
            gc.collect()

        fake.chewing_delete.assert_called_once_with(4321)


if __name__ == "__main__":
    unittest.main()
