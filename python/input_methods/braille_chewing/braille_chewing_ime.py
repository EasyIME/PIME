#! python3
# Copyright (C) 2017 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
# Copyright (C) 2017 Logo-Kuo <logo@forblind.org.tw>
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

import winsound  # for PlaySound
import os

from keycodes import * # for VK_XXX constants
from textService import *
from ..chewing.chewing_ime import ChewingTextService, ENGLISH_MODE, CHINESE_MODE, FULLSHAPE_MODE
from .brl_tables import brl_ascii_dic, brl_buf_state


class BrailleChewingTextService(ChewingTextService):

    # 鍵盤按鍵轉成點字 1 - 8 點
    # A-Z 的 Windows virtual key codes = 大寫的 ASCII code
    braille_keys = [
        ord(' '),  # Space
        ord('F'),  # 1
        ord('D'),  # 2
        ord('S'),  # 3
        ord('J'),  # 4
        ord('K'),  # 5
        ord('L'),  # 6
        ord('A'),  # 7
        ord(';'),  # 8
    ]

    # 注音符號對實體鍵盤英數按鍵
    bopomofo_to_keys = {
        # 標準注音鍵盤
        "ㄅ": "1",
        "ㄆ": "q",
        "ㄇ": "a",
        "ㄈ": "z",
        "ㄉ": "2",
        "ㄊ": "w",
        "ㄋ": "s",
        "ㄌ": "x",
        "ㄍ": "e",
        "ㄎ": "d",
        "ㄏ": "c",
        "ㄐ": "r",
        "ㄑ": "f",
        "ㄒ": "v",
        "ㄓ": "5",
        "ㄔ": "t",
        "ㄕ": "g",
        "ㄖ": "b",
        "ㄗ": "y",
        "ㄘ": "h",
        "ㄙ": "n",
        "ㄧ": "u",
        "ㄨ": "j",
        "ㄩ": "m",
        "ㄚ": "8",
        "ㄛ": "i",
        "ㄜ": "k",
        "ㄝ": ",",
        "ㄞ": "9",
        "ㄟ": "o",
        "ㄠ": "l",
        "ㄡ": ".",
        "ㄢ": "0",
        "ㄣ": "p",
        "ㄤ": ";",
        "ㄥ": "/",
        "ㄦ": "-",
        "˙": "7",
        "ˊ": "6",
        "ˇ": "3",
        "ˋ": "4",
        # 標點、特殊符號鍵盤序列
        "，": "`31",
        "、": "`32",
        "。": "`33",
        "；": "`37",
        "：": "`38",
        "？": "`35",
        "！": "`36",
        "…": "`1",
        "—": "` 49",
        "（": "`41",
        "）": "`42",
        "《": "`4 4",
        "》": "`4 5",
        "〔": "`45",
        "〕": "`46",
        "〈": "`49",
        "〉": "`4 1",
        "「": "`43",
        "」": "`44",
        "『": "`4 2",
        "』": "`4 3",
        "＆": "`3   1",
        "＊": "`3   3",
        "×": "`73",
        "÷": "`74",
        "±": "`79",
        "≠": "`76",
        "∞": "`78",
        "≒": "`77",
        "≦": "`7 6",
        "≧": "`7 7",
        "∩": "`7 8",
        "∪": "`7 9",
        "⊥": "`7  2",
        "∠": "`7  3",
        "∵": "`7   1",
        "∴": "`7   2",
        "≡": "` 43",
        "∥": "` 46",
        "↑": "`81",
        "↓": "`82",
        "←": "`83",
        "→": "`84",
        "△": "`8 8",
        "□": "`8  5",
            # 希臘字母大寫 24 個
        "Α": "`6  7",
        "Β": "`6  8",
        "Γ": "`6  9",
        "Δ": "`6   1",
        "Ε": "`6   2",
        "Ζ": "`6   3",
        "Η": "`6   4",
        "Θ": "`6   5",
        "Ι": "`6   6",
        "Κ": "`6   7",
        "Λ": "`6   8",
        "Μ": "`6   9",
        "Ν": "`6    1",
        "Ξ": "`6    2",
        "Ο": "`6    3",
        "Π": "`6    4",
        "Ρ": "`6    5",
        "Σ": "`6    6",
        "Τ": "`6    7",
        "Υ": "`6    8",
        "Φ": "`6    9",
        "Χ": "`6     1",
        "Ψ": "`6     2",
        "Ω": "`6     3",
            # 希臘字母小寫 24 個
        "α": "`61",
        "β": "`62",
        "γ": "`63",
        "δ": "`64",
        "ε": "`65",
        "ζ": "`66",
        "η": "`67",
        "θ": "`68",
        "ι": "`69",
        "κ": "`6 1",
        "λ": "`6 2",
        "μ": "`6 3",
        "ν": "`6 4",
        "ξ": "`6 5",
        "ο": "`6 6",
        "π": "`6 7",
        "ρ": "`6 8",
        "σ": "`6 9",
        "τ": "`6  1",
        "υ": "`6  2",
        "φ": "`6  3",
        "χ": "`6  4",
        "ψ": "`6  5",
        "ω": "`6  6",
    }
    current_dir = os.path.dirname(__file__)
    sounds_dir = os.path.join(current_dir, "sounds")

    def __init__(self, client):
        super().__init__(client)
        self.braille_keys_pressed = False
        self.dots_pressed_states = [False] * 9
        self.state = brl_buf_state()

    def applyConfig(self):
        # 攔截 ChewingTextService 的 applyConfig，以便強制關閉某些設定選項
        super().applyConfig()

        # 強制使用預設 keyboard layout
        self.chewingContext.set_KBType(0);

        # 強制按下空白鍵時不當做選字指令
        self.chewingContext.set_spaceAsSelection(0)

        # TODO: 強制關閉新酷音某些和點字輸入相衝的功能

    def reset_braille_mode(self, clear_pending=True):
        # 清除點字 buffer，準備打下一個字
        for i in range(len(self.dots_pressed_states)):
            self.dots_pressed_states[i] = False
        if clear_pending:
            self.state.reset()
        self.braille_keys_pressed = False

    def has_modifiers(self, keyEvent):
        # 檢查是否 Ctrl, Shift, Alt 的任一個有被按下
        return keyEvent.isKeyDown(VK_SHIFT) or keyEvent.isKeyDown(VK_CONTROL) or keyEvent.isKeyDown(VK_MENU)

    def needs_braille_handling(self, keyEvent):
        # 檢查是否需要處理點字
        # 若修飾鍵 (Ctrl, Shift, Alt) 都沒有被按下，且按鍵是「可打印」（空白、英數、標點符號等），當成點字鍵處理
        has_modifiers = self.has_modifiers(keyEvent)
        if not has_modifiers and keyEvent.isPrintableChar():
            return True
        # 其他按鍵會打斷正在記錄的點字輸入
        if has_modifiers or keyEvent.keyCode == VK_ESCAPE:
            # 若按壓修飾鍵，會清除所有內部點字狀態
            self.reset_braille_mode()
        else:
            # 其他的不可打印按鍵僅重設八點的輸入狀態，不影響點字組字的部份
            self.reset_braille_mode(False)
        # 未按下修飾鍵，且點字正在組字，仍然當點字鍵處理
        # 許多不可打印按鍵如 Delete 及方向鍵，會於處理點字時忽略，不讓它有異常行為
        return not has_modifiers and self.state.brl_check()

    def filterKeyDown(self, keyEvent):
        if self.needs_braille_handling(keyEvent):
            return True
        return super().filterKeyDown(keyEvent)

    def onKeyDown(self, keyEvent):
        if keyEvent.charCode in range(ord('0'), ord('9') + 1) and self.get_chewing_cand_totalPage() > 0: # selection keys
            pass
        elif keyEvent.keyCode == VK_BACK:
            # 將倒退鍵經過內部狀態處理，取得鍵入序列轉送新酷音
            if self.handle_braille_keys(keyEvent):
                return True
        elif self.needs_braille_handling(keyEvent):
            # 點字模式，檢查 8 個點字鍵是否被按下，忽略其餘按鍵
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

    # 模擬實體鍵盤的英數按鍵送到新酷音
    def send_keys_to_chewing(self, keys, keyEvent):
        if not self.chewingContext:
            print("send_keys_to_chewing:", "chewingContext not initialized")
            return
        # 輸入標點符號，不使用模擬按鍵的方法，因為涉及較多 GUI 反應
        if keys.startswith("`") and len(keys) > 1:
            # 直接將按鍵送給 libchewing, 此時與 GUI 顯示非同步
            for key in keys:
                self.chewingContext.handle_Default(ord(key))
            compStr = ""
            if self.chewingContext.buffer_Check():
                compStr = self.chewingContext.buffer_String().decode("UTF-8")
            # 根據 libchewing 緩衝區的狀態，更新組字區內容與游標位置
            self.setCompositionString(compStr)
            self.setCompositionCursor(self.chewingContext.cursor_Current())
            return
        # 其餘的按鍵，使用模擬的方式，會跟 GUI 顯示同步
        for key in keys:
            keyEvent.keyCode = ord(key.upper())  # 英文數字的 virtual keyCode 正好 = 大寫 ASCII code
            keyEvent.charCode = ord(key)  # charCode 為字元內碼
            # 讓新酷音引擎處理按鍵，模擬按下再放開
            super().filterKeyDown(keyEvent)
            super().onKeyDown(keyEvent)
            super().filterKeyUp(keyEvent)
            super().onKeyUp(keyEvent)

    def get_chewing_cand_totalPage(self):
        # access the chewingContext created by ChewingTextService
        return self.chewingContext.cand_TotalPage() if self.chewingContext else 0

    # 將點字 8 點轉換成注音按鍵，送給新酷音處理
    def handle_braille_keys(self, keyEvent):
        if keyEvent.keyCode == VK_BACK:
            current_braille = "\b"
        else:
            # 將點字鍵盤狀態轉成用數字表示，例如 [False, True, True, True, True, False, True, False] 轉成 "23457"
            current_braille = "".join([str(i) for i, pressed in enumerate(self.dots_pressed_states) if pressed])
        bopomofo_seq = ""
        # 點字鍵入轉換成 ASCII 字元、熱鍵或者注音
        if current_braille == "\b":
            key = self.state.append_brl("\b")
            if key:
                bopomofo_seq = "\b" * key["VK_BACK"] + key["bopomofo"]
            else:
                return False
        elif current_braille == "0245":
            # 熱鍵 245+space 能夠在點字狀態失去控制時將它重設，不遺失已經存在組字區的中文
            # 正在輸入注音，就把注音去掉
            if self.chewingContext and self.chewingContext.bopomofo_Check():
                # 清除打到一半的注音狀態
                self.chewingContext.clean_bopomofo_buf()
                compStr = ""
                if self.chewingContext.buffer_Check():
                    compStr = self.chewingContext.buffer_String().decode("UTF-8")
                # 恢復原本組字區內蟲跟游標位置
                self.setCompositionString(compStr)
                self.setCompositionCursor(self.chewingContext.cursor_Current())
            self.state.reset()
        elif current_braille == "0456":
            # 熱鍵 456+space 與 Shift 一樣能切換中打、英打模式
            self.toggleLanguageMode()
        elif current_braille.startswith("0") and len(current_braille) > 1:
            # 未定義的熱鍵，發出警告聲，空白 "0" 不屬此類
            winsound.MessageBeep()
        elif self.langMode == ENGLISH_MODE:
            bopomofo_seq = brl_ascii_dic.get(current_braille, "")
            if keyEvent.isKeyToggled(VK_CAPITAL):  # capslock
                bopomofo_seq = bopomofo_seq.upper()  # convert to upper case
        else:
            # 如果正在選字，允許使用點字數字
            if self.get_chewing_cand_totalPage():
                bopomofo_seq = brl_ascii_dic.get(current_braille, "")
                if bopomofo_seq not in "0123456789":
                    winsound.MessageBeep()
            # 否則，將點字送給內部進行組字
            else:
                key = self.state.append_brl(current_braille)
                if key:
                    bopomofo_seq = "\b" * key["VK_BACK"] + key["bopomofo"]
                else:
                    winsound.MessageBeep()

        print(current_braille.replace("\b", r"\b"), "=>", bopomofo_seq.replace("\b", r"\b"))
        if bopomofo_seq:
            bopomofo_seq = "".join(self.bopomofo_to_keys.get(c, c) for c in bopomofo_seq)
            # 把注音送給新酷音
            self.send_keys_to_chewing(bopomofo_seq, keyEvent)

        # 清除點字 buffer，準備打下一個字
        self.reset_braille_mode(False)
        return True # braille input processed

    # 切換中英文模式
    def toggleLanguageMode(self):
        super().toggleLanguageMode()
        if self.chewingContext:
            # 播放語音檔，說明目前是中文/英文
            mode = self.chewingContext.get_ChiEngMode()
            snd_file = os.path.join(self.sounds_dir, "chi.wav" if mode == CHINESE_MODE else "eng.wav")
            winsound.PlaySound(snd_file, winsound.SND_FILENAME|winsound.SND_ASYNC|winsound.SND_NODEFAULT)
            if mode == ENGLISH_MODE:
                self.state.reset()

    # 切換全形/半形
    def toggleShapeMode(self):
        super().toggleShapeMode()
        if self.chewingContext:
            # 播放語音檔，說明目前是全形/半形
            mode = self.chewingContext.get_ShapeMode()
            snd_file = os.path.join(self.sounds_dir, "full.wav" if mode == FULLSHAPE_MODE else "half.wav")
            winsound.PlaySound(snd_file, winsound.SND_FILENAME|winsound.SND_ASYNC|winsound.SND_NODEFAULT)
