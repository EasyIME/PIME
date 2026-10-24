"""Per-user directory policy (issue #973).

Generated with assistance from omp (deepseek-v4.1-flash).
"""

import os
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
sys.path.insert(0, os.path.join(ROOT, "python"))

import pime_dirs


class EnsureUserDirTest(unittest.TestCase):
    def test_windows_inherits_the_profile_acl(self):
        with mock.patch.object(pime_dirs.sys, "platform", "win32"), \
                mock.patch.object(pime_dirs.os, "makedirs") as makedirs:
            pime_dirs.ensure_user_dir(r"C:\Users\me\AppData\Roaming\PIME\chewing")

        makedirs.assert_called_once_with(
            r"C:\Users\me\AppData\Roaming\PIME\chewing", exist_ok=True)

    def test_posix_keeps_the_directory_private(self):
        with mock.patch.object(pime_dirs.sys, "platform", "linux"), \
                mock.patch.object(pime_dirs.os, "makedirs") as makedirs:
            pime_dirs.ensure_user_dir("/home/me/.config/pime")

        makedirs.assert_called_once_with(
            "/home/me/.config/pime", mode=0o700, exist_ok=True)

    def test_creates_missing_parents(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "PIME", "chewing")
            pime_dirs.ensure_user_dir(path)
            pime_dirs.ensure_user_dir(path)
            self.assertTrue(os.path.isdir(path))


if __name__ == "__main__":
    unittest.main()
