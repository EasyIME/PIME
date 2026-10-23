"""Per-user directories shared by the PIME backends.

On Windows, ``os.makedirs(..., mode=0o700)`` does not set POSIX permission
bits: CPython turns the mode into a DACL for the creating token. A launcher
started elevated creates the directory owned by ``BUILTIN\\Administrators``,
so the next non-elevated backend cannot enter it (issue #973). The profile
directory already carries a user-only inherited ACL, so let the child inherit
it. On POSIX, keep ``mode=0o700`` so other local users cannot read IME data.

Generated with assistance from omp (deepseek-v4.1-flash).
"""

import os
import sys


def ensure_user_dir(path):
    """Create *path* and its parents under the current user's profile."""
    if sys.platform == "win32":
        os.makedirs(path, exist_ok=True)
    else:
        os.makedirs(path, mode=0o700, exist_ok=True)
