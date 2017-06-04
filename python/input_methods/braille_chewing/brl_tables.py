#! python3
# Copyright (C) 2017 Logo-Kuo <logo@forblind.org.tw>
# Copyright (C) 2017 Hong Jen-Yee (PCMan) <pcman.tw@gmail.com>
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


brl_ascii_dic = { # 包函英數模式下的字母、數字及鍵盤上的符號
    # 空白
    "0": " ",
    # 小寫字母
    "1": "a",
    "12": "b",
    "14": "c",
    "145": "d",
    "15": "e",
    "124": "f",
    "1245": "g",
    "125": "h",
    "24": "i",
    "245": "j",
    "13": "k",
    "123": "l",
    "134": "m",
    "1345": "n",
    "135": "o",
    "1234": "p",
    "12345": "q",
    "1235": "r",
    "234": "s",
    "2345": "t",
    "136": "u",
    "1236": "v",
    "2456": "w",
    "1346": "x",
    "13456": "y",
    "1356": "z",
    # 大寫字母
    "17": "A",
    "127": "B",
    "147": "C",
    "1457": "D",
    "157": "E",
    "1247": "F",
    "12457": "G",
    "1257": "H",
    "247": "I",
    "2457": "J",
    "137": "K",
    "1237": "L",
    "1347": "M",
    "13457": "N",
    "1357": "O",
    "12347": "P",
    "123457": "Q",
    "12357": "R",
    "2347": "S",
    "23457": "T",
    "1367": "U",
    "12367": "V",
    "24567": "W",
    "13467": "X",
    "134567": "Y",
    "13567": "Z",
    # 數字
    "2": "1",
    "23": "2",
    "25": "3",
    "256": "4",
    "26": "5",
    "235": "6",
    "2356": "7",
    "236": "8",
    "35": "9",
    "356": "0",
    # 英數鍵盤上的符號
    "4": "`",
    "45": "~",
    "2346": "!",
    "47": "@",
    "3456": "#",
    "1246": "$",
    "146": "%",
    "457": "^",
    "12346": "&",
    "16": "*",
    "12356": "(",
    "23456": ")",
    "36": "-",
    "123456": "=",
    "456": "_",
    "346": "+",
    "2467": "[",
    "124567": "]",
    "246": "{",
    "12456": "}",
    "56": ";",
    "3": "'",
    "156": ":",
    "5": "\"",
    "6": ",",
    "46": ".",
    "34": "/",
    "126": "<",
    "345": ">",
    "1456": "?",
    "12567": "\\",
    "1256": "|"
}

# 替代型例外：
# 如果下一個輸入 new_char 是 ex_char 就把現在的注音取代成 replacement
# 例： ㄝ 與 ㄧㄞ 都可以在無聲母時使用，需要用聲調區別 ㄝˋ 與 ㄧㄞˊ
def replace(current_state, new_char, ex_char, replacement):
    if new_char == ex_char and current_state._bop_buf[-1] != replacement:
        current_state._bop_buf[-1] = replacement
        return True # handled
    return False
replace.__category__ = "CHECK_NEXT"

# 無聲母例外：
# 針對介母、韻母，如果目前輸入是點字緩衝區的第一個輸入，就要把輸入的內容替換成 replacement
def the_first(current_state, replacement):
    if current_state._brl_buf: return False
    current_state._bop_buf[-1] = replacement
    return True
the_first.__category__ = "CHECK_PREVIOUS"

# 把 dict 與一個 tuple 榜在一起
# 其中 next_state 表示下一個可接受的內部狀態
class Braille_Bopomofo_Dict(dict):
    def __init__(self, mapping, next_state):
        super().__init__(mapping)
        self.next_state = next_state

# 點字與聲調對應，沒有下一個可接受狀態
TONAL_MARK_DICT = Braille_Bopomofo_Dict({
    "1": u"˙",
    "2": u"ˊ",
    "3": u" ",
    "4": u"ˇ",
    "5": u"ˋ",
}, tuple())

# 點字與介母、韻母對應，下一個可接受聲調輸入
RHYME_DICT = Braille_Bopomofo_Dict({
    # 介母、韻母
    "16"    : (u"ㄧ",),
    "34"    : (u"ㄨ",),
    "1256"  : (u"ㄩ",),
    "345"   : (u"ㄚ",),
    "126"   : (u"ㄛ",),
    "2346"  : (u"ㄜ",),
    "26"    : (u"ㄧㄞ", (replace, "5", u"ㄝ")), # ㄝ 跟 ㄧㄞ 同，預設顯示 ㄧㄞ 但遇第四聲改成 ㄝ
    "2456"  : (u"ㄞ",),
    "356"   : (u"ㄟ", (the_first, u"ㄧㄛ"), (replace, "5", u"ㄟ")), # 跟 ㄧㄛ 同，預設顯示 ㄟ 但前面無聲母則顯示 ㄧㄛ
    "146"   : (u"ㄠ",),
    "12356" : (u"ㄡ",),
    "1236"  : (u"ㄢ",),
    "136"   : (u"ㄣ",),
    "1346"  : (u"ㄤ",),
    "1356"  : (u"ㄥ",),
    "156"   : (u"", (the_first, u"ㄦ")), # 預設無顯示，如果前面沒有聲母則顯示 ㄦ
    # 疊韻 ㄧ 系列
    "23456" : (u"ㄧㄚ",),
    "346"   : (u"ㄧㄝ",),
    "246"   : (u"ㄧㄠ",),
    "234"   : (u"ㄧㄡ",),
    "2345"  : (u"ㄧㄢ",),
    "1456"  : (u"ㄧㄣ",),
    "46"    : (u"ㄧㄤ",),
    "13456" : (u"ㄧㄥ",),
    # 疊韻 ㄨ 系列
    "35"    : (u"ㄨㄚ",),
    "25"    : (u"ㄨㄛ",),
    "2356"  : (u"ㄨㄞ",),
    "1246"  : (u"ㄨㄟ",),
    "12456" : (u"ㄨㄢ",),
    "123456": (u"ㄨㄣ",),
    "456"   : (u"ㄨㄤ",),
    "12346" : (u"ㄨㄥ",),
    # 疊韻 ㄩ 系列
    "236"   : (u"ㄩㄝ",),
    "45"    : (u"ㄩㄢ",),
    "256"   : (u"ㄩㄣ",),
    "235"   : (u"ㄩㄥ",),
}, (TONAL_MARK_DICT,))

# ㄧㄩ 力外：
# 針對 ㄍㄘㄙ 如果接下來 new_char 是 ㄧㄩ 或其開始的疊韻，就要變成 replacement
def yi_yu(current_state, new_char, replacement):
    try:
        if RHYME_DICT[new_char][0][0] in u"ㄧㄩ":
            current_state._bop_buf[-1] = replacement
            return True
    except:
        pass
    return False
yi_yu.__category__ = "CHECK_NEXT"

# 點字與聲母對應，下一個可接受介、韻母輸入
CONSONANT_DICT = Braille_Bopomofo_Dict({
    # 聲母
    "135"  : (u"ㄅ",),
    "1234" : (u"ㄆ",),
    "134"  : (u"ㄇ",),
    "12345": (u"ㄈ",),
    "145"  : (u"ㄉ",),
    "124"  : (u"ㄊ",),
    "1345" : (u"ㄋ",),
    "14"   : (u"ㄌ",),
    "13"   : (u"ㄍ", (yi_yu, u"ㄐ")),
    "123"  : (u"ㄎ",),
    "1235" : (u"ㄏ",),
    "1"    : (u"ㄓ",),
    "12"   : (u"ㄔ",),
    "24"   : (u"ㄕ",),
    "1245" : (u"ㄖ",),
    "125"  : (u"ㄗ",),
    "245"  : (u"ㄘ", (yi_yu, u"ㄑ")),
    "15"   : (u"ㄙ", (yi_yu, u"ㄒ")),
}, (RHYME_DICT,))

# 點字與服泡對應，可以在此隨意新增符號定義
# 注意︰點字序列之間不可以有 prefix 的關係
SYMBOL_DICT = Braille_Bopomofo_Dict({
    "0": " ",
    "23-0": u"，",
    "6-0": u"、",
    "36-0": u"。",
    "56-0": u"；",
    "25-25": u"：",
    "1345-0": u"？",
    "123-0": u"！",
    "5-5-5": u"…",
    "246-0": u"（",
    "135-0": u"）",
    "56-36": u"「",
    "36-23": u"」",
    "236-236": u"『",
    "356-356": u"』",
    "4-16": u"×",
    "46-34": u"÷",
    "346-36": u"±",
    "46-13": u"＝",
    "34-46-13": u"≠",
    "6-123456": u"∞",
    "1246-246-25-25": u"←",
    "1246-25-25-135": u"→",
    "46-1": u"α",
    "46-12": u"β",
}, tuple())

# 點字緩衝區的狀態
# Members:
# _brl_buf: 記錄目前點字輸入的狀態
# _bop_buf: 記錄目前應有的注音輸出字串
# _stack: 記錄每個點字輸入的類型
class brl_buf_state:

    def __init__(self):
        self._brl_buf = []
        self._bop_buf = []
        # 初始狀態，下一個可接受聲母或介、韻母輸入
        self._stack = [(CONSONANT_DICT, RHYME_DICT)]

    # 取得下一個點字輸入，產生狀態變化與輸出回饋
    # 輸出 dict 包含二個 keys: VK_BACK 為 backspace 的數量；bopomofo 為注音或符號序列
    def append_brl(self, brl_char):
        try:
            # 找找看，這個輸入是否在允許的下一個類別裡
            ph_tabs = [d for d in self._stack[-1] if brl_char in d]
            # 目前我們只處理恰好一個類別的狀況
            if len(ph_tabs) != 1:
                raise KeyError
            res = {"VK_BACK": 0, "bopomofo": ""}
            # 考慮先前的注音輸入可能被現在的輸入影響
            if self._brl_buf:
                for t in self._stack[-2][self._brl_buf[-1]][1:]:
                    if t[0].__category__ != "CHECK_NEXT": continue
                    res["VK_BACK"] = len(self._bop_buf[-1])
                    if t[0](*((self, brl_char) + t[1:])):
                        res["bopomofo"] = self._bop_buf[-1]
                        break
                    res["VK_BACK"] = 0
            # 把目前點字的輸入先登記為預設值
            self._bop_buf.append(ph_tabs[0][brl_char][0])
            # 然後逐一檢查是否因為例外狀況要變換
            for t in ph_tabs[0][brl_char][1:]:
                if t[0].__category__ != "CHECK_PREVIOUS": continue
                if t[0](*((self,) + t[1:])): break
            # 處理完畢，把此次點字輸入堆進 buffer
            self._brl_buf.append(brl_char)
            key = "-".join(self._brl_buf)
            # 特例︰檢查是否注音序列恰好被符號定義走
            if key in SYMBOL_DICT:
                # 是，強迫內部狀態歸位，並以符號做為回傳
                res["bopomofo"] += SYMBOL_DICT[key]
                self._stack[-1] = tuple()
            else:
                # 否，內部狀態進行轉換，並以注音做為回傳
                res["bopomofo"] += self._bop_buf[-1]
                self._stack[-1] = ph_tabs[0]
                self._stack.append(ph_tabs[0].next_state)
            # 如果沒有下一個可接受輸入表示輸入完成一個中文字了，立即回到初始狀態
            if not self._stack[-1]:
                self.__init__()
            return res
        except KeyError:
            pass
        # 注音輸入錯誤，但可能是輸入符號
        # 先把新輸入放進 buffer, 看看現有點字序列是否為某些符號的 prefix
        self._brl_buf.append(brl_char)
        key = "-".join(self._brl_buf)
        cands = [k for k in SYMBOL_DICT.keys() if k.startswith(key)]
        if cands:
            self._stack[-1] = SYMBOL_DICT
            self._stack.append(SYMBOL_DICT.next_state)
            if key == cands[0]:
                # Exact match, 符號輸入完畢
                self.__init__()
            return {"VK_BACK": 0, "bopomofo": SYMBOL_DICT[key] if key == cands[0] else ""}
        # 也不是 prefix, 這次輸入屬於錯誤，應被拒絕
        del self._brl_buf[-1]
        return {} # input rejected

# Testcases here.
if __name__ == "__main__":
    key_seq = "356-356".split("-")
    state = brl_buf_state()
    for k in key_seq:
        print(state.append_brl(k))
