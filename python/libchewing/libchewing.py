#
# Copyright (C) libchewing developers
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

from ctypes import *
from functools import partial
import sys

_libchewing = None
if sys.platform == "win32": # Windows
    import os.path
    # find in current dir first
    dll_path = os.path.join(os.path.dirname(__file__), "chewing.dll")
    if not os.path.exists(dll_path):
        dll_path = "chewing.dll" # search in system path
    _libchewing = CDLL(dll_path)
else: # UNIX-like systems
    _libchewing = CDLL('libchewing.so.3')

_libchewing.chewing_commit_String_static.restype = c_char_p
_libchewing.chewing_buffer_String_static.restype = c_char_p
_libchewing.chewing_cand_String_static.restype = c_char_p
_libchewing.chewing_bopomofo_String_static.restype = c_char_p
_libchewing.chewing_aux_String_static.restype = c_char_p
_libchewing.chewing_kbtype_String_static.restype = c_char_p


def Init(datadir, userdir):
    return _libchewing.chewing_Init(datadir, userdir)


class ChewingContext:
    def __init__(self, **kwargs):
        if not kwargs:
            self.ctx = _libchewing.chewing_new()
        else:
            syspath = kwargs.get("syspath", None)
            userpath = kwargs.get("userpath", None)
            self.ctx = _libchewing.chewing_new2(
                syspath,
                userpath,
                None,
                None)

    def __del__(self):
        _libchewing.chewing_delete(self.ctx)

    def __getattr__(self, name):
        func = 'chewing_' + name
        # force the use of the APIs returning const char* to avoid memory leaks
        if name.endswith("_String"):
            func += "_static"
        if func in _libchewing.__dict__:
            wrap = partial(_libchewing.__dict__[func], self.ctx)
            setattr(self, name, wrap)
            return wrap
        elif hasattr(_libchewing, func):
            wrap = partial(_libchewing.__getattr__(func), self.ctx)
            setattr(self, name, wrap)
            return wrap
        else:
            raise AttributeError(name)

    # The original libchewing API is set_selKey (without 's')
    # It only accepts an integer array. Let's create a new API that accepts
    # a python string
    def set_selKeys(self, selKeys):
        selKeyCodes = (c_int * len(selKeys))()
        for i, key in enumerate(selKeys):
            selKeyCodes[i] = ord(key)
        _libchewing.chewing_set_selKey(self.ctx, selKeyCodes, len(selKeys))

    def Configure(self, cpp, maxlen, direction, space, kbtype):
        self.set_candPerPage(cpp)
        self.set_maxChiSymbolLen(maxlen)
        self.set_addPhraseDirection(direction)
        self.set_spaceAsSelection(space)
        self.set_KBType(kbtype)
