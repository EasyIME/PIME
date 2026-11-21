#! python3
# Copyright (C) 2026 Dave Tseng
#
# Architecture and design by Dave Tseng.
# Implementation generated with AI assistance from Claude Code (Claude Opus 5.5).
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

import shutil
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
        # libchewing[name] 每次都新建函式物件，不會像屬性存取那樣快取在共用的 CDLL 上，
        # 所以在這裡設 restype/argtypes 不會改到其他程式碼看到的全域簽章
        self._get_phone_seq = libchewing["chewing_get_phoneSeq"]
        self._get_phone_seq.restype = POINTER(c_ushort)
        self._get_phone_seq.argtypes = [c_void_p]
        self._free = libchewing["chewing_free"]
        self._free.argtypes = [c_void_p]
        # 另一個看不見的新酷音引擎，只用來查每個聲調有哪些字；不碰使用者詞庫。
        # 每個選單自己一個暫存資料夾，不同輸入法工作階段與行程不會共用同一個 SQLite 檔
        self._temp_dir = tempfile.mkdtemp(prefix="pime_tone_menu_")
        user_path = self._temp_dir + "/lookup.sqlite3"
        self._lookup = context_class(syspath=data_dir.encode("UTF-8"),
                                     userpath=user_path.encode("UTF-8"))
        self._lookup.set_ChiEngMode(1)
        self._lookup.set_KBType(KB_DEFAULT)
        # Esc 要清掉整個編輯區，否則上一次查的字會留著，下一次查到的是錯的字
        self._lookup.set_escCleanAllBuf(1)
        self.index = None  # 要換聲調的字在編輯區的位置（含標點、空白等非注音項目）
        self.phone_index = None  # 同一個字在注音序列裡的位置
        self.phones = []  # 選單上每一項的注音碼

    def bopomofo(self, phone):
        buf = create_string_buffer(16)
        self._lib.chewing_phone_to_bopomofo(phone, buf, 16)
        return buf.value.decode("UTF-8")

    def phone_seq(self, ctx):
        n = ctx.get_phoneSeqLen()
        seq = self._get_phone_seq(ctx.ctx)
        try:
            return [seq[i] for i in range(n)]
        finally:
            self._free(seq)

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
        # 和 ↓ 選字一樣：游標在最後面時，指的是最後一個項目
        position = min(ctx.cursor_Current(), len(self._buffer(ctx)) - 1)
        phone_index = self._phone_index(ctx, position, len(seq))
        if phone_index is None:  # 游標在標點或空白上，或對不上：不開選單，免得改到別的字
            return []
        self.index = position
        self.phone_index = phone_index
        current = seq[phone_index]
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
        self.phone_index = None
        self.phones = []

    def dispose(self):
        """Release the lookup engine and delete its temporary database."""
        self._lookup = None  # 先放掉引擎，Windows 才刪得掉它開著的檔案
        shutil.rmtree(self._temp_dir, ignore_errors=True)

    def __del__(self):
        self.dispose()

    def is_open(self):
        return self.index is not None

    def choose(self, ctx, n, keyboard_layout):
        """Replace the character with menu item n. Returns True on success."""
        index, phone_index, phone = self.index, self.phone_index, self.phones[n]
        old = self.phone_seq(ctx)
        chars = self._buffer(ctx)
        self.close()
        cursor = ctx.cursor_Current()
        self._move_cursor(ctx, index + 1)
        ctx.handle_Backspace()
        self._type(ctx, phone, keyboard_layout)
        if ctx.get_phoneSeqLen() != len(old):  # 新聲調打不出來：把原本的字打回去
            self._type(ctx, old[phone_index], keyboard_layout)
            self._keep_characters(ctx, chars, index)
            self._move_cursor(ctx, cursor)
            return False
        self._keep_characters(ctx, chars, index)
        self._move_cursor(ctx, cursor)
        return True

    @staticmethod
    def _buffer(ctx):
        return list(ctx.buffer_String().decode("UTF-8"))

    @staticmethod
    def _is_syllable_char(char):
        """True for a Chinese character; punctuation, spaces and English letters are not."""
        code = ord(char)
        return (0x3400 <= code <= 0x4DBF or 0x4E00 <= code <= 0x9FFF
                or 0xF900 <= code <= 0xFAFF or 0x20000 <= code <= 0x2FA1F)

    def _phone_index(self, ctx, position, phone_count):
        """The place in the phone sequence of the buffer item at position, or None.

        The cursor and the buffer count every item, but the phone sequence holds only
        the Chinese characters, so a comma in the buffer shifts the two apart.
        """
        chars = self._buffer(ctx)
        if position < 0 or not self._is_syllable_char(chars[position]):
            return None
        syllables = [self._is_syllable_char(char) for char in chars]
        if sum(syllables) != phone_count:
            return None
        return sum(syllables[:position])

    def _keep_characters(self, ctx, chars, skip):
        """Choose the original character again wherever retyping changed a neighbour.

        Deleting and retyping a syllable makes libchewing run its automatic phrase
        selection again, which can turn the characters next to it into others
        (today's weather: changing the tone of the second tian turned the following
        character into a different one).
        """
        if len(self._buffer(ctx)) != len(chars):
            return
        for position, char in enumerate(chars):
            if position == skip or self._buffer(ctx)[position] == char:
                continue
            self._move_cursor(ctx, position)
            ctx.handle_Down()
            ctx.cand_Enumerate()
            candidates = []
            while ctx.cand_hasNext():
                candidates.append(ctx.cand_String().decode("UTF-8"))
            if char in candidates:
                ctx.cand_choose_by_index(candidates.index(char))
            else:
                ctx.handle_Esc()

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
        for _ in range(len(ctx.buffer_String().decode("UTF-8")) + 2):
            now = ctx.cursor_Current()
            if now == target:
                return
            (ctx.handle_Left if now > target else ctx.handle_Right)()
            if ctx.cursor_Current() == now:
                return
