from ctypes import *
from functools import partial
import sys

_libchewing = None
if sys.platform == "win32": # Windows
    import os.path
    import platform
    # find in current dir first
    dll_path = os.path.dirname(__file__)
    # load different dll files for 64 bit and 32 bit python
    if platform.architecture()[0] == "64bit":
        dll_path = os.path.join(dll_path, "x64\\chewing.dll")
    else:
        dll_path = os.path.join(dll_path, "x86\\chewing.dll")
    if not os.path.exists(dll_path):
        dll_path = "chewing.dll" # search in system path
    _libchewing = CDLL(dll_path)
else: # UNIX-like systems
    _libchewing = CDLL('libchewing.so.3')

_libchewing.chewing_commit_String.restype = c_char_p
_libchewing.chewing_buffer_String.restype = c_char_p
_libchewing.chewing_cand_String.restype = c_char_p
_libchewing.chewing_zuin_String.restype = c_char_p
_libchewing.chewing_aux_String.restype = c_char_p
_libchewing.chewing_get_KBString.restype = c_char_p


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
        _libchewing.chewing_free(self.ctx)

    def __getattr__(self, name):
        func = 'chewing_' + name
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

    def Configure(self, cpp, maxlen, direction, space, kbtype):
        self.set_candPerPage(cpp)
        self.set_maxChiSymbolLen(maxlen)
        self.set_addPhraseDirection(direction)
        self.set_spaceAsSelection(space)
        self.set_KBType(kbtype)
