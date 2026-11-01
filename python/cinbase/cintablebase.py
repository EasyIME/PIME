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

"""Base class for CIN table state containers."""

from typing import Optional


class CinTableBase:
    """Base class for CIN table state containers.

    Encapsulates table loading state (cin, loading) and provides
    asynchronous Future-backed synchronization, dynamic loading state,
    and non-blocking table access.
    """

    def __init__(self):
        self.future = None

    @property
    def loading(self):
        """Returns True if a background loading task is currently in progress."""
        if self.future is not None:
            return not self.future.done()
        return False

    @property
    def cin(self):
        """Returns the loaded table instance if ready, or None if still loading."""
        if self.future is not None and self.future.done():
            return self.future.result()
        return None

    def wait(self, timeout: Optional[float] = None):
        """Waits for background loading to complete and returns the table object.

        Args:
            timeout: Maximum seconds to wait. None means wait indefinitely.

        Returns:
            The loaded table instance, or None if no loading task was scheduled.
        """
        if self.future is not None:
            return self.future.result(timeout=timeout)
        return None


__all__ = ["CinTableBase"]
