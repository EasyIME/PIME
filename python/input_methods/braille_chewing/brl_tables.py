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
    def __init__(self, name, mapping, next_state):
        super().__init__(mapping)
        self.name = name
        self.next_state = next_state

    def __repr__(self):
        return self.name

# 點字與聲調對應，沒有下一個可接受狀態
TONAL_MARK_DICT = Braille_Bopomofo_Dict("TONAL_MARK", {
    "1": "˙",
    "2": "ˊ",
    "3": " ",
    "4": "ˇ",
    "5": "ˋ",
}, tuple())

# 點字與介母、韻母對應，下一個可接受聲調輸入
RHYME_DICT = Braille_Bopomofo_Dict("RHYME", {
    # 介母、韻母
    "16"    : ("ㄧ",),
    "34"    : ("ㄨ",),
    "1256"  : ("ㄩ",),
    "345"   : ("ㄚ",),
    "126"   : ("ㄛ",),
    "2346"  : ("ㄜ",),
    "26"    : ("ㄧㄞ", (replace, "5", "ㄝ")), # ㄝ 跟 ㄧㄞ 同，預設顯示 ㄧㄞ 但遇第四聲改成 ㄝ
    "2456"  : ("ㄞ",),
    "356"   : ("ㄟ", (the_first, "ㄧㄛ"), (replace, "5", "ㄟ")), # 跟 ㄧㄛ 同，預設顯示 ㄟ 但前面無聲母則顯示 ㄧㄛ
    "146"   : ("ㄠ",),
    "12356" : ("ㄡ",),
    "1236"  : ("ㄢ",),
    "136"   : ("ㄣ",),
    "1346"  : ("ㄤ",),
    "1356"  : ("ㄥ",),
    "156"   : ("", (the_first, "ㄦ")), # 預設無顯示，如果前面沒有聲母則顯示 ㄦ
    # 疊韻 ㄧ 系列
    "23456" : ("ㄧㄚ",),
    "346"   : ("ㄧㄝ",),
    "246"   : ("ㄧㄠ",),
    "234"   : ("ㄧㄡ",),
    "2345"  : ("ㄧㄢ",),
    "1456"  : ("ㄧㄣ",),
    "46"    : ("ㄧㄤ",),
    "13456" : ("ㄧㄥ",),
    # 疊韻 ㄨ 系列
    "35"    : ("ㄨㄚ",),
    "25"    : ("ㄨㄛ",),
    "2356"  : ("ㄨㄞ",),
    "1246"  : ("ㄨㄟ",),
    "12456" : ("ㄨㄢ",),
    "123456": ("ㄨㄣ",),
    "456"   : ("ㄨㄤ",),
    "12346" : ("ㄨㄥ",),
    # 疊韻 ㄩ 系列
    "236"   : ("ㄩㄝ",),
    "45"    : ("ㄩㄢ",),
    "256"   : ("ㄩㄣ",),
    "235"   : ("ㄩㄥ",),
}, (TONAL_MARK_DICT,))

# ㄧㄩ 力外：
# 針對 ㄍㄘㄙ 如果接下來 new_char 是 ㄧㄩ 或其開始的疊韻，就要變成 replacement
def yi_yu(current_state, new_char, replacement):
    try:
        if RHYME_DICT[new_char][0][0] in "ㄧㄩ":
            current_state._bop_buf[-1] = replacement
            return True
    except:
        pass
    return False
yi_yu.__category__ = "CHECK_NEXT"

# 點字與聲母對應，下一個可接受介、韻母輸入
CONSONANT_DICT = Braille_Bopomofo_Dict("CONSONANT", {
    # 聲母
    "135"  : ("ㄅ",),
    "1234" : ("ㄆ",),
    "134"  : ("ㄇ",),
    "12345": ("ㄈ",),
    "145"  : ("ㄉ",),
    "124"  : ("ㄊ",),
    "1345" : ("ㄋ",),
    "14"   : ("ㄌ",),
    "13"   : ("ㄍ", (yi_yu, "ㄐ")),
    "123"  : ("ㄎ",),
    "1235" : ("ㄏ",),
    "1"    : ("ㄓ",),
    "12"   : ("ㄔ",),
    "24"   : ("ㄕ",),
    "1245" : ("ㄖ",),
    "125"  : ("ㄗ",),
    "245"  : ("ㄘ", (yi_yu, "ㄑ")),
    "15"   : ("ㄙ", (yi_yu, "ㄒ")),
}, (RHYME_DICT,))

# 點字與服泡對應，可以在此隨意新增符號定義
# 注意︰點字序列之間不可以有 prefix 的關係
SYMBOL_DICT = Braille_Bopomofo_Dict("SYMBOL", {
    "0": " ",
    "23-0": "，",
    "6-0": "、",
    "36-0": "。",
    "56-0": "；",
    "25-25": "：",
    "1456-0": "？",
    "123-0": "！",
    "5-5-5": "…",
    "5-2": "—",
    "246-0": "（",
    "135-0": "）",
    "126-126": "《",
    "345-345": "》",
    "12346-0": "〔",
    "13456-0": "〕",
    "126-0": "〈",
    "345-0": "〉",
    "56-36": "「",
    "36-23": "」",
    "236-236": "『",
    "356-356": "』",
    "456-12346": "＆",
    "4-3456": "＊",
    "4-16": "×",
    "46-34": "÷",
    "346-36": "±",
    "34-46-13": "≠",
    "6-123456": "∞",
    "5-46-13-126-156-12456": "≒",
    "126-123456": "≦",
    "345-123456": "≧",
    "46-146": "∩",
    "46-346": "∪",
    "1246-1234": "⊥",
    "1246-246-0": "∠",
    "4-34": "∵",
    "6-16": "∴",
    "4-156-46-13": "≡",
    "1246-123": "∥",
    "1246-126-25-25-135": "↑",
    "1246-146-25-25-135": "↓",
    "1246-246-25-25": "←",
    "1246-25-25-135": "→",
    "1246-2345": "△",
    "12346-13456": "□",
    # 希臘字母大寫 24 個
    "46-17": "Α",
    "46-127": "Β",
    "46-12457": "Γ",
    "46-1457": "Δ",
    "46-157": "Ε",
    "46-13567": "Ζ",
    "46-1567": "Η",
    "46-14567": "Θ",
    "46-247": "Ι",
    "46-137": "Κ",
    "46-1237": "Λ",
    "46-1347": "Μ",
    "46-13457": "Ν",
    "46-13467": "Ξ",
    "46-1357": "Ο",
    "46-12347": "Π",
    "46-12357": "Ρ",
    "46-2347": "Σ",
    "46-23457": "Τ",
    "46-1367": "Υ",
    "46-1247": "Φ",
    "46-123467": "Χ",
    "46-134567": "Ψ",
    "46-24567": "Ω",
    # 希臘字母小寫 24 個
    "46-1": "α",
    "46-12": "β",
    "46-1245": "γ",
    "46-145": "δ",
    "46-15": "ε",
    "46-1356": "ζ",
    "46-156": "η",
    "46-1456": "θ",
    "46-24": "ι",
    "46-13": "κ",
    "46-123": "λ",
    "46-134": "μ",
    "46-1345": "ν",
    "46-1346": "ξ",
    "46-135": "ο",
    "46-1234": "π",
    "46-1235": "ρ",
    "46-234": "σ",
    "46-2345": "τ",
    "46-136": "υ",
    "46-124": "φ",
    "46-12346": "χ",
    "46-13456": "ψ",
    "46-2456": "ω",
}, tuple())

# 點字緩衝區的狀態
# Members:
# _brl_buf: 記錄目前點字輸入的狀態
# _bop_buf: 記錄目前應有的注音輸出字串
# _stack: 記錄每個點字輸入的類型
class brl_buf_state:

    def __init__(self):
        self.reset()

    # 取得下一個點字輸入，產生狀態變化與輸出回饋
    # 輸出 dict 包含二個 keys: VK_BACK 為 backspace 的數量；bopomofo 為注音或符號序列
    def append_brl(self, brl_char):
        if brl_char == "\b":
            if not self._brl_buf: # no previous state
                return {}
            import os
            # 刪除目前「下一個可接受狀態」資訊
            del self._stack[-1]
            # 取出目前與狀態回復後的注音序列，以求出 difference
            current_bopomofo = "".join(self._bop_buf)
            self._bop_buf = self._stack[-1]["bopomofo"]
            past_bopomofo = "".join(self._bop_buf)
            p = os.path.commonprefix([current_bopomofo, past_bopomofo])
            # 回復之前的 next_state
            self._stack[-1] = self._stack[-1]["next_state"]
            # 刪除點字緩衝區一個字元
            del self._brl_buf[-1]
            # 用鋼材的 difference 寫成指令，使 libchewing 狀態同步
            return {"VK_BACK": len(current_bopomofo) - len(p), "bopomofo": past_bopomofo[len(p):]}
        from copy import copy
        # 即將被推入堆疊的舊狀態，包含三個 keys:
        # - class_info 為點字緩衝區對應 index 地方的點字內容屬於哪個分類 (CONSONANT, RHYME, TONAL_MARK, SYMBOL)
        # - bopomofo 為目前注音緩衝區的狀態，因為是 list 所以需要 copy 備份
        # - next_state 為當時打字之前堆疊頂端的值，列出接下來可接受點字組合
        # class_info 供 CHECK_NEXT 檢查用，其他資料做為 \b 的狀態回復用
        old_state = {"class_info": SYMBOL_DICT, "bopomofo": copy(self._bop_buf), "next_state": self._stack[-1]}
        try:
            # 找找看，這個輸入是否在允許的下一個類別裡
            ph_tabs = [d for d in self._stack[-1] if brl_char in d]
            # 目前我們只處理恰好一個類別的狀況
            if len(ph_tabs) != 1:
                raise KeyError
            res = {"VK_BACK": 0, "bopomofo": ""}
            # 考慮先前的注音輸入可能被現在的輸入影響
            if self._brl_buf:
                for t in self._stack[-2]["class_info"][self._brl_buf[-1]][1:]:
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
                old_state["class_info"] = ph_tabs[0]
                self._stack[-1] = old_state
                self._stack.append(ph_tabs[0].next_state)
            # 如果沒有下一個可接受輸入表示輸入完成一個中文字了，立即回到初始狀態
            if not self._stack[-1]:
                self.reset()
            return res
        except KeyError:
            pass
        # 注音輸入錯誤，但可能是輸入符號
        # 先把新輸入放進 buffer, 看看現有點字序列是否為某些符號的 prefix
        self._brl_buf.append(brl_char)
        key = "-".join(self._brl_buf)
        cands = [k for k in SYMBOL_DICT.keys() if k.startswith(key + "-") or k == key]
        if cands:
            self._stack[-1] = old_state
            self._stack.append(SYMBOL_DICT.next_state)
            symbol = SYMBOL_DICT.get(key, "")
            if symbol:
                # Exact match, 符號輸入完畢
                self.reset()
            return {"VK_BACK": 0, "bopomofo": symbol}
        # 也不是 prefix, 這次輸入屬於錯誤，應被拒絕
        del self._brl_buf[-1]
        return {} # input rejected

    def brl_check(self):
        return bool(self._brl_buf)

    def reset(self):
        self._brl_buf = []
        self._bop_buf = []
        # 初始狀態，下一個可接受聲母或介、韻母輸入
        self._stack = [(CONSONANT_DICT, RHYME_DICT)]

# Testcases here.
if __name__ == "__main__":
    key_seq = "356-356".split("-")
    state = brl_buf_state()
    for k in key_seq:
        print(state.append_brl(k))
