#! python3
# Copyright (C) 2017 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
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

from keycodes import * # for VK_XXX constants
from textService import *
from ..chewing.chewing_ime import ChewingTextService


# 注音符號對實體鍵盤英數按鍵
bopomofo_chars = "ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙㄧㄨㄩㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦ˙ˊˇˋ"
bopomofo_to_keys = [
    "1qaz2wsxedcrfv5tgbyhnujm8ik,9ol.0p;/-7634",        # standard kb
    "bpmfdtnlgkhjvcjvcrzasexuyhgeiawomnkllsdfj",        # hsu
    "1234567890-qwertyuiopasdfghjkl;zxcvbn/m,.",        # IBM
    "2wsx3edcrfvtgb6yhnujm8ik,9ol.0p;/-['=1qaz",        # Gin-yieh
    "bpmfdtnlvkhg7c,./j;'sexuaorwiqzy890-=1234",        # ET
    "bpmfdtnlvkhgvcgycjqwsexuaorwiqzpmntlhdfjk",        # ET26
    "1'a;2,oq.ejpuk5yixfdbghm8ctw9rnv0lsz[7634",        # Dvorak
    "bpmfdtnlgkhjvcjvcrzasexuyhgeiawomnkllsdfj",        # Dvorak Hsu
    "qqazwwsxedcrfvttgbyhnujmuikbiolmoplnpyerd",        # DACHEN-CP26
    "1qaz2wsxedcrfv5tgbyhnujm8ik,9ol.0p;/-7634",        # Hanyu Pinyin
    "1qaz2wsxedcrfv5tgbyhnujm8ik,9ol.0p;/-7634",        # Luoma Pinyin
    "1qaz2wsxedcrfv5tgbyhnujm8ik,9ol.0p;/-7634",        # secondary Bopomofo Pinyin
    "1qdz2gsxmtclnv5wrjyikfap8ue,9bo.0;h/-7634",        # Carpalx
]

# 將注音符號轉換成實體鍵盤的英數按鍵
def get_keys_for_bopomofo(bopomofo_seq, keyboard_type=0):
    keys = []
    kb = bopomofo_to_keys[keyboard_type]
    for bopomofo in bopomofo_seq:
        idx = bopomofo_chars.find(bopomofo)
        key = kb[idx]
        keys.append(key)
    return keys


# 點字六點對注音符號
points_to_bopomofo = {
    "135": "ㄅ",
    "145": "ㄉ",
    "345": "ㄚ",
    "2345": "ㄧㄢ",
    "12456": "ㄨㄢ",
    "2": "ˊ",
    "5": "ˋ ",
    "23": "， ",
    "13": "?",  # 可能是 "ㄍ" or "ㄐ" 無法馬上判定
    "13-2345": "ㄐㄧㄢ",
    "13-12456": "ㄍㄨㄢ"
}


class SixPointTextService(ChewingTextService):

    # 鍵盤按鍵轉成點字 1 - 6 點
    # A-Z 的 Windows virtual key codes = 大寫的 ASCII code
    braille_keys = [
        ord('F'),  # 1
        ord('D'),  # 2
        ord('S'),  # 3
        ord('J'),  # 4
        ord('K'),  # 5
        ord('L'),  # 6
    ]

    def __init__(self, client):
        super().__init__(client)
        self.braille_keys_pressed = False
        self.point_pressed_states = [False] * 6
        self.pending_points = ""

    def reset_braille_mode(self, clear_pending=True):
        # 清除點字 buffer，準備打下一個字
        for i in range(6):
            self.point_pressed_states[i] = False
        if clear_pending:
            self.pending_points = ""
        self.braille_keys_pressed = False

    def has_modifiers(self, keyEvent):
        # 檢查是否 Ctrl, Shift, Alt 的任一個有被按下
        return keyEvent.isKeyDown(VK_SHIFT) or keyEvent.isKeyDown(VK_CONTROL) or keyEvent.isKeyDown(VK_MENU)

    def needs_braille_handling(self, keyEvent):
        # 檢查是否需要處理點字
        # 若 Ctrl, Shift, Alt 任一個被按下，或按鍵不是 printable (方向鍵, page up, backspace 等等)，不使用點字
        if self.has_modifiers(keyEvent) or not keyEvent.isPrintableChar() or keyEvent.charCode == ord(' '):
            self.reset_braille_mode()
            return False
        return True

    def filterKeyDown(self, keyEvent):
        if self.needs_braille_handling(keyEvent):
            return True
        return super().filterKeyDown(keyEvent)

    def onKeyDown(self, keyEvent):
        if self.needs_braille_handling(keyEvent):
            # 點字模式，檢查 6 個點字鍵是否被按下，忽略其餘按鍵
            for i, key in enumerate(self.braille_keys):
                if keyEvent.isKeyDown(key):
                    self.point_pressed_states[i] = 1
                    self.braille_keys_pressed = True
            return True
        return super().onKeyDown(keyEvent)

    def filterKeyUp(self, keyEvent):
        if self.braille_keys_pressed:
            return True
        return super().filterKeyUp(keyEvent)

    def onKeyUp(self, keyEvent):
        if self.braille_keys_pressed:
            all_released = True
            # 檢查是否全部點字鍵都已放開
            for key in self.braille_keys:
                if keyEvent.isKeyDown(key):
                    all_released = False
            if all_released:
                self.handle_braille_keys(keyEvent)
            return True
        return super().onKeyUp(keyEvent)


    # 將點字 6 點轉換成注音按鍵，送給新酷音處理
    def handle_braille_keys(self, keyEvent):
        # 將 6 點狀態轉成用數字表示，例如 [False, True, True, True, True, False] 轉成 "2345"
        points_str = "".join([str(i + 1) for i, pressed in enumerate(self.point_pressed_states) if pressed])

        # 如果有剛剛無法判斷注音的六點輸入，和現在的輸入接在一起判斷
        if self.pending_points:
            points_str = self.pending_points + "-" + points_str

        clear_pending = True
        # 將 6 點轉成注音符號
        bopomofo_seq = points_to_bopomofo.get(points_str)
        print(points_str, "=>", bopomofo_seq)
        if bopomofo_seq:
            # 如果目前 6 點有對應到注音
            if bopomofo_seq == "?":  # 無法馬上判斷，加入 pending points，和下次的輸入一起判斷
                if self.pending_points:
                    self.pending_points = self.pending_points + "-" + points_str
                else:
                    self.pending_points = points_str
                clear_pending = False  # reset 時不要清除 pending_points
            else:
                # 依目前鍵盤對應，把注音符號轉回英數鍵盤按鍵，並且逐一送給新酷音
                for key in get_keys_for_bopomofo(bopomofo_seq):
                    keyEvent.keyCode = ord(key.upper())  # 英文數字的 virtual keyCode 正好 = 大寫 ASCII code
                    keyEvent.charCode = ord(key)  # charCode 為字元內碼
                    # 讓新酷音引擎處理按鍵，模擬按下再放開
                    super().filterKeyDown(keyEvent)
                    super().onKeyDown(keyEvent)
                    super().filterKeyUp(keyEvent)
                    super().onKeyUp(keyEvent)

        # 清除點字 buffer，準備打下一個字
        self.reset_braille_mode(clear_pending=clear_pending)
