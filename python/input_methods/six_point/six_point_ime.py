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
from ..chewing.chewing_ime import ChewingTextService, ENGLISH_MODE, CHINESE_MODE
from .brl_tables import brl_ascii_dic, brl_phonic_dic, phonetic_categories


# 注音符號對實體鍵盤英數按鍵
bopomofo_chars = "ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙㄧㄨㄩㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦ˙ˊˇˋ"
bopomofo_to_keys = "1qaz2wsxedcrfv5tgbyhnujm8ik,9ol.0p;/-7634",        # standard kb

# 將注音符號轉換成實體鍵盤的英數按鍵
def get_keys_for_bopomofo(bopomofo_seq):
    keys = []
    for bopomofo in bopomofo_seq:
        idx = bopomofo_chars.find(bopomofo)
        if idx >= 0:
            key = bopomofo_to_keys[idx]
        else:
            key = bopomofo
        keys.append(key)
    return keys


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
        self.dots_pressed_states = [False] * 6
        self.last_braille = ""

    def applyConfig(self):
        # 攔截 ChewingTextService 的 applyConfig，以便強制關閉某些設定選項
        super().applyConfig()

        # 強制使用預設 keyboard layout
        chewingContext.set_KBType(0);

        # TODO: 強制關閉新酷音某些和點字輸入相衝的功能

    def reset_braille_mode(self, clear_pending=True):
        # 清除點字 buffer，準備打下一個字
        for i in range(6):
            self.dots_pressed_states[i] = False
        if clear_pending:
            self.last_braille = ""
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
                    self.dots_pressed_states[i] = 1
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

    def send_bopomofo_to_chewing(self, bopomofo_seq, keyEvent):
        # 依目前鍵盤對應，把注音符號轉回英數鍵盤按鍵，並且逐一送給新酷音
        for key in get_keys_for_bopomofo(bopomofo_seq):
            keyEvent.keyCode = ord(key.upper())  # 英文數字的 virtual keyCode 正好 = 大寫 ASCII code
            keyEvent.charCode = ord(key)  # charCode 為字元內碼
            # 讓新酷音引擎處理按鍵，模擬按下再放開
            super().filterKeyDown(keyEvent)
            super().onKeyDown(keyEvent)
            super().filterKeyUp(keyEvent)
            super().onKeyUp(keyEvent)

    def get_chewing_bopomofo_buffer(self):
        # access the chewingContext created by ChewingTextService
        if self.chewingContext and self.chewingContext.bopomofo_Check():
            return self.chewingContext.bopomofo_String(None).decode("UTF-8")
        return ""

    # 將點字 6 點轉換成注音按鍵，送給新酷音處理
    def handle_braille_keys(self, keyEvent):
        # 將 6 點狀態轉成用數字表示，例如 [False, True, True, True, True, False] 轉成 "2345"
        current_braille = "".join([str(i + 1) for i, pressed in enumerate(self.dots_pressed_states) if pressed])

        # FIXME: 區分英數和注音模式
        # 6 點轉注音
        clear_pending = True
        if self.langMode == ENGLISH_MODE:
            bopomofo_seq = brl_ascii_dic.get(current_braille)
            self.last_braille = ""
            if keyEvent.isKeyToggled(VK_CAPITAL):  # capslock
                bopomofo_seq = bopomofo_seq.upper()  # convert to upper case
        else:
            bopomofo_seq = brl_phonic_dic.get(current_braille)

        if bopomofo_seq == "CHECK_NEXT":  # 須等待下一個輸入才能判斷
            self.last_braille = current_braille
            clear_pending=False
            bopomofo_seq = None
        elif bopomofo_seq == "CHECK_PREVIOUS":  # 須檢查上一個注音輸入狀態
            last_bopomofo = self.get_chewing_bopomofo_buffer()
            if current_braille == '356': # ['ㄧㄛ', 'ㄟ']
                # 上一個注音不是聲母 => ㄧㄛ, 否則 'ㄟ'
                if not last_bopomofo or phonetic_categories.get(last_bopomofo[-1]) != "聲母":
                    bopomofo_seq = 'ㄧㄛ'
                else:
                    bopomofo_seq = 'ㄟ'
            elif current_braille == '1':  # ['ㄓ', '˙']
                # 沒有前一個注音，或前一個不是韻母 => ㄓ
                if not last_bopomofo or phonetic_categories.get(last_bopomofo[-1]) != "韻母":
                    bopomofo_seq = 'ㄓ'
                else:
                    bopomofo_seq = '˙'
            elif current_braille == '125':  # ['ㄗ', 'ㄛ']
                # 沒有前一個注音 'ㄗ', 否則 'ㄛ'
                bopomofo_seq = 'ㄗ' if not last_bopomofo else 'ㄛ'
            elif current_braille == '156':  # 'ㄦ'
                # FIXME: 也當作捲舌與不捲舌聲母單獨出現時所加的韻母
                bopomofo_seq = 'ㄦ'
            else:
                bopomofo_seq = None

        if self.last_braille and bopomofo_seq:  # 如果有剛剛無法判斷注音的六點輸入，和現在的輸入接在一起判斷
            if len(bopomofo_seq) == 2 and bopomofo_seq[0] in ('ㄧ', 'ㄩ'):
                # ㄧ,ㄩ疊韻
                last_bopomofo = {'13': 'ㄐ', '15': 'ㄒ', '245': 'ㄑ'}.get(self.last_braille)
                bopomofo_seq = last_bopomofo + bopomofo_seq
            elif phonetic_categories.get(bopomofo_seq) == "韻母" or (len(bopomofo_seq) == 2 and bopomofo_seq[0] == 'ㄨ'):
                # 韻母 或 ㄨ疊韻
                last_bopomofo = {'13': 'ㄍ', '15': 'ㄙ', '245': 'ㄘ'}.get(self.last_braille)
                bopomofo_seq = last_bopomofo + bopomofo_seq
            else:
                bopomofo_seq = None

        # FIXME: 處理 space key

        print(current_braille, "=>", bopomofo_seq)
        if bopomofo_seq:
            # 把注音送給新酷音
            self.send_bopomofo_to_chewing(bopomofo_seq, keyEvent)

        # 清除點字 buffer，準備打下一個字
        self.reset_braille_mode(clear_pending=clear_pending)
