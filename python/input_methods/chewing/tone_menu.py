#! python3
# Copyright (C) 2026 PIME contributors
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
# 聲調選單：在編輯區按 ↑，列出游標所在那個字的其他聲調，選了就把那個字換成新聲調。
# libchewing 沒有「改某個字的注音」的 API，所以做法是刪掉那個字，再用新聲調重打一次。
#
# This file was generated with assistance from Claude Code (Claude Opus 5.5).

import os
import tempfile
from ctypes import POINTER, c_ushort, c_void_p, create_string_buffer

# 注音符號在「標準」鍵盤 (KB_DEFAULT) 上的按鍵
_DEFAULT_KEYS = dict(zip(
    "ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙㄧㄨㄩㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦˊˇˋ˙",
    "1qaz2wsxedcrfv5tgbyhnujm8ik,9ol.0p;/-6347"))
_TONE_MARKS = "ˊˇˋ˙"
KB_DEFAULT = 0
TONE_BITS = 7  # libchewing 的 phone 用最低 3 個位元存聲調


def default_keys(bopomofo):
    """Return the keys that type a bopomofo syllable on the default layout.

    A syllable without a tone mark is the first tone, typed with a space.
    """
    keys = "".join(_DEFAULT_KEYS[c] for c in bopomofo)
    return keys if bopomofo and bopomofo[-1] in _TONE_MARKS else keys + " "


def tone_order(bopomofo):
    """Sort key: first tone, ˊ, ˇ, ˋ, then ˙."""
    mark = bopomofo[-1] if bopomofo and bopomofo[-1] in _TONE_MARKS else ""
    return ["", *_TONE_MARKS].index(mark)


class ToneMenu:
    """The other tones of one syllable in the composition buffer."""

    def __init__(self, libchewing, context_class, data_dir):
        self._lib = libchewing
        self._lib.chewing_get_phoneSeq.restype = POINTER(c_ushort)
        self._lib.chewing_get_phoneSeq.argtypes = [c_void_p]
        self._lib.chewing_free.argtypes = [c_void_p]
        # 另一個看不見的新酷音引擎，只用來查每個聲調有哪些字；不碰使用者詞庫
        user_path = os.path.join(tempfile.gettempdir(), "pime_chewing_tone_menu.sqlite3")
        self._lookup = context_class(syspath=data_dir.encode("UTF-8"),
                                     userpath=user_path.encode("UTF-8"))
        self._lookup.set_ChiEngMode(1)
        self._lookup.set_KBType(KB_DEFAULT)
        # Esc 要清掉整個編輯區，否則上一次查的字會留著，下一次查到的是錯的字
        self._lookup.set_escCleanAllBuf(1)
        self.index = None  # 要換聲調的字在編輯區的位置
        self.phones = []  # 選單上每一項的注音碼

    def bopomofo(self, phone):
        buf = create_string_buffer(16)
        self._lib.chewing_phone_to_bopomofo(phone, buf, 16)
        return buf.value.decode("UTF-8")

    def phone_seq(self, ctx):
        n = ctx.get_phoneSeqLen()
        seq = self._lib.chewing_get_phoneSeq(ctx.ctx)
        try:
            return [seq[i] for i in range(n)]
        finally:
            self._lib.chewing_free(seq)

    def candidates(self, phone):
        """The characters of one syllable, most common first."""
        ctx = self._lookup
        ctx.handle_Esc()
        for key in default_keys(self.bopomofo(phone)):
            ctx.handle_Default(ord(key))
        result = []
        if ctx.buffer_Check() and ctx.get_phoneSeqLen() == 1:
            ctx.handle_Down()
            ctx.cand_Enumerate()
            while ctx.cand_hasNext():
                result.append(ctx.cand_String().decode("UTF-8"))
        ctx.handle_Esc()
        ctx.handle_Esc()
        return result

    def open(self, ctx):
        """Build the menu for the character at the cursor.

        Returns the menu labels, e.g. ["ㄅㄧ 逼", "ㄅㄧˊ 鼻", ...], or [] when
        there is nothing to offer. Tones that have no character are left out.
        """
        seq = self.phone_seq(ctx)
        if not seq:
            return []
        # 和 ↓ 選字一樣：游標在最後面時，指的是最後一個字
        self.index = min(ctx.cursor_Current(), len(seq) - 1)
        current = seq[self.index]
        items = []
        # libchewing 的聲調碼：0 一聲、1 輕聲、2 ˊ、3 ˇ、4 ˋ (5 也顯示成一聲，不能用，否則一聲會出現兩次)
        for tone in range(0, 5):
            phone = (current & ~TONE_BITS) | tone
            if phone == current:
                continue
            bopomofo = self.bopomofo(phone)
            if not bopomofo:
                continue
            chars = self.candidates(phone)
            if chars:
                items.append((tone_order(bopomofo), phone, bopomofo + " " + chars[0]))
        items.sort()
        self.phones = [phone for _, phone, _ in items]
        return [label for _, _, label in items]

    def close(self):
        self.index = None
        self.phones = []

    def is_open(self):
        return self.index is not None

    def choose(self, ctx, n, keyboard_layout):
        """Replace the character with menu item n. Returns True on success."""
        index, phone = self.index, self.phones[n]
        old = self.phone_seq(ctx)
        self.close()
        cursor = ctx.cursor_Current()
        self._move_cursor(ctx, index + 1)
        ctx.handle_Backspace()
        self._type(ctx, phone, keyboard_layout)
        if ctx.get_phoneSeqLen() != len(old):  # 新聲調打不出來：把原本的字打回去
            self._type(ctx, old[index], keyboard_layout)
            self._move_cursor(ctx, cursor)
            return False
        self._move_cursor(ctx, cursor)
        return True

    def _type(self, ctx, phone, keyboard_layout):
        ctx.set_KBType(KB_DEFAULT)
        try:
            for key in default_keys(self.bopomofo(phone)):
                ctx.handle_Default(ord(key))
        finally:
            ctx.set_KBType(keyboard_layout)

    @staticmethod
    def _move_cursor(ctx, target):
        # 每次移一格；移不動就停，避免游標卡住時無限迴圈
        for _ in range(ctx.get_phoneSeqLen() + 2):
            now = ctx.cursor_Current()
            if now == target:
                return
            (ctx.handle_Left if now > target else ctx.handle_Right)()
            if ctx.cursor_Current() == now:
                return
