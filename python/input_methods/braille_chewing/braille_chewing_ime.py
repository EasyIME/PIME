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
from .brl_tables import brl_ascii_dic, brl_phonic_dic, brl_space_dic, bopomofo_is_category


class BrailleChewingTextService(ChewingTextService):

    # 鍵盤按鍵轉成點字 1 - 8 點
    # A-Z 的 Windows virtual key codes = 大寫的 ASCII code
    braille_keys = [
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
    bopomofo_chars = "ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙㄧㄨㄩㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦ˙ˊˇˋ"
    bopomofo_to_keys = "1qaz2wsxedcrfv5tgbyhnujm8ik,9ol.0p;/-7634"        # standard kb

    current_dir = os.path.dirname(__file__)
    sounds_dir = os.path.join(current_dir, "sounds")

    def __init__(self, client):
        super().__init__(client)
        self.braille_keys_pressed = False
        self.dots_pressed_states = [False] * 8
        self.last_braille = ""

    def applyConfig(self):
        # 攔截 ChewingTextService 的 applyConfig，以便強制關閉某些設定選項
        super().applyConfig()

        # 強制使用預設 keyboard layout
        self.chewingContext.set_KBType(0);

        # TODO: 強制關閉新酷音某些和點字輸入相衝的功能

    def reset_braille_mode(self, clear_pending=True):
        # 清除點字 buffer，準備打下一個字
        for i in range(8):
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
            # 點字模式，檢查 8 個點字鍵是否被按下，忽略其餘按鍵
            for i, key in enumerate(self.braille_keys):
                if keyEvent.isKeyDown(key):
                    self.dots_pressed_states[i] = 1
                    self.braille_keys_pressed = True
            return True
        elif keyEvent.charCode == ord(' '):  # space key
            # 須檢查上一個注音輸入狀態
            last_bopomofo = self.get_chewing_bopomofo_buffer()
            if last_bopomofo:  # 剛輸入過注音符號，檢查是否代換成標點符號
                for n in range(len(last_bopomofo), 0, -1):
                    # 取得目前注音的最後 n 個字，檢查是否能對到標點
                    symbol_keys = brl_space_dic.get(last_bopomofo[-n:])
                    if symbol_keys:
                        # 新酷音在注音打到一半的時候，改輸入標點，注音會自動消去換成標點
                        self.send_keys_to_chewing(symbol_keys, keyEvent)
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

    # 將注音符號轉換成實體鍵盤的英數按鍵
    def get_keys_for_bopomofo(self, bopomofo_seq):
        keys = []
        for bopomofo in bopomofo_seq:
            idx = self.bopomofo_chars.find(bopomofo)
            if idx >= 0:
                key = self.bopomofo_to_keys[idx]
            else:
                key = bopomofo
            keys.append(key)
        return keys

    def send_keys_to_chewing(self, keys, keyEvent):
        for key in keys:
            keyEvent.keyCode = ord(key.upper())  # 英文數字的 virtual keyCode 正好 = 大寫 ASCII code
            keyEvent.charCode = ord(key)  # charCode 為字元內碼
            # 讓新酷音引擎處理按鍵，模擬按下再放開
            super().filterKeyDown(keyEvent)
            super().onKeyDown(keyEvent)
            super().filterKeyUp(keyEvent)
            super().onKeyUp(keyEvent)

    def send_bopomofo_to_chewing(self, bopomofo_seq, keyEvent):
        # 依目前鍵盤對應，把注音符號轉回英數鍵盤按鍵，並且逐一送給新酷音
        keys = self.get_keys_for_bopomofo(bopomofo_seq)
        self.send_keys_to_chewing(keys, keyEvent)

    def get_chewing_bopomofo_buffer(self):
        # access the chewingContext created by ChewingTextService
        if self.chewingContext and self.chewingContext.bopomofo_Check():
            return self.chewingContext.bopomofo_String(None).decode("UTF-8")
        return ""

    # 將點字 8 點轉換成注音按鍵，送給新酷音處理
    def handle_braille_keys(self, keyEvent):
        # 將 8 點狀態轉成用數字表示，例如 [False, True, True, True, True, False, True, False] 轉成 "23457"
        current_braille = "".join([str(i + 1) for i, pressed in enumerate(self.dots_pressed_states) if pressed])

        # FIXME: 區分英數和注音模式
        # 8 點轉注音
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
                # 還需要檢查特例，上一個點字是 13 時，注音尚未確定，此時 last_bopomofo = None
                # 但有可能是ㄍ，可以接ㄟ，所以檢查上一個點字是否為 "13"
                if (last_bopomofo and bopomofo_is_category(last_bopomofo[-1], "聲母")) or self.last_braille == "13":
                    bopomofo_seq = 'ㄟ'
                else:
                    # 實際上也有可能是要打 ㄟ 接注聲 目前還沒有處理這個部分
                    bopomofo_seq = 'ㄧㄛ'
            elif current_braille == '1':  # ['ㄓ', '˙']
                # 前一個注音是韻母，或前一個是舌尖音加 156 點 => ˙
                if (last_bopomofo and bopomofo_is_category(last_bopomofo[-1], "韻母")) or (last_bopomofo and bopomofo_is_category(last_bopomofo[-1], "舌尖音")):
                    bopomofo_seq = '˙'
                else:
                    bopomofo_seq = 'ㄓ'
            elif current_braille == '156':  # 'ㄦ'
                # 如果 ㄦ 前面是舌尖音則呼略 ㄦ
                if last_bopomofo and bopomofo_is_category(last_bopomofo[-1], "舌尖音"): 
                    bopomofo_seq = last_bopomofo
                else:
                    # 此時若聲母為 ㄘ 或 ㄙ 先暫時讓 156 變成 ㄦ 
                    bopomofo_seq = 'ㄦ'
            else:
                bopomofo_seq = None

        if self.last_braille and bopomofo_seq:  # 如果有剛剛無法判斷注音的六點輸入，和現在的輸入接在一起判斷
            if bopomofo_is_category(bopomofo_seq, "韻母") or (bopomofo_is_category(bopomofo_seq, "疊韻") and bopomofo_seq[0] == 'ㄨ') or bopomofo_seq == 'ㄨ':
                # 韻母 或 ㄨ疊韻 或ㄨ直接當韻母
                last_bopomofo = {'13': 'ㄍ', '15': 'ㄙ', '245': 'ㄘ'}.get(self.last_braille)
                # 因為 ㄦ 也是韻母 所以在這邊還必須處理 ㄘ 或 ㄙ + 156 接注聲的狀況                
                if current_braille == "156":
                    # 需把 ㄦ 去除 實際上沒有 ㄍㄦ 可以不用手動排除
                    bopomofo_seq = last_bopomofo
                else:
                    # 一般情況需要把聲母跟韻母或疊韻全部加起來
                    bopomofo_seq = last_bopomofo + bopomofo_seq
            elif bopomofo_seq in ('ㄧ', 'ㄩ') or (bopomofo_is_category(bopomofo_seq, "疊韻") and bopomofo_seq[0] in ('ㄧ', 'ㄩ')):
                # ㄧ,ㄩ疊韻 或 ㄧ、ㄩ直接當韻母
                last_bopomofo = {'13': 'ㄐ', '15': 'ㄒ', '245': 'ㄑ'}.get(self.last_braille)
                bopomofo_seq = last_bopomofo + bopomofo_seq
            else:
                bopomofo_seq = None

        print(current_braille, "=>", bopomofo_seq)
        if bopomofo_seq:
            # 把注音送給新酷音
            self.send_bopomofo_to_chewing(bopomofo_seq, keyEvent)

        # 清除點字 buffer，準備打下一個字
        self.reset_braille_mode(clear_pending=clear_pending)

    # 切換中英文模式
    def toggleLanguageMode(self):
        super().toggleLanguageMode()
        if self.chewingContext:
            # 播放語音檔，說明目前是中文/英文
            mode = self.chewingContext.get_ChiEngMode()
            snd_file = os.path.join(self.sounds_dir, "chi.wav" if mode == CHINESE_MODE else "eng.wav")
            winsound.PlaySound(snd_file, winsound.SND_FILENAME|winsound.SND_ASYNC)

    # 切換全形/半形
    def toggleShapeMode(self):
        super().toggleShapeMode()
        if self.chewingContext:
            # 播放語音檔，說明目前是全形/半形
            mode = self.chewingContext.get_ShapeMode()
            snd_file = os.path.join(self.sounds_dir, "full.wav" if mode == FULLSHAPE_MODE else "half.wav")
            winsound.PlaySound(snd_file, winsound.SND_FILENAME|winsound.SND_ASYNC)
