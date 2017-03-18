#! python3
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

from keycodes import *  # for VK_XXX constants
import os.path
import time
import opencc  # OpenCC 繁體簡體中文轉換

import io
import sys
import math
import copy
import ctypes
import winsound
import threading
from ctypes import windll
from .cin import Cin
from .rcin import RCin
from .hcin import HCin
from .swkb import swkb
from .symbols import symbols
from .dsymbols import dsymbols
from .fsymbols import fsymbols
from .msymbols import msymbols
from .flangs import flangs
from .phrase import phrase
from .userphrase import userphrase
from .emoji import emoji
from .extendtable import extendtable

from .debug import Debug

CHINESE_MODE = 1
ENGLISH_MODE = 0
FULLSHAPE_MODE = 1
HALFSHAPE_MODE = 0
DEBUG_MODE = False

# shift + space 熱鍵的 GUID
SHIFT_SPACE_GUID = "{f1dae0fb-8091-44a7-8a0c-3082a1515447}"
TF_MOD_SHIFT = 0x0004

# 選單項目和語言列按鈕的 command ID
ID_SWITCH_LANG = 1
ID_SWITCH_SHAPE = 2
ID_SETTINGS = 3
ID_MODE_ICON = 4
ID_WEBSITE = 5
ID_BUGREPORT = 6
ID_FORUM = 7
ID_MOEDICT = 8
ID_DICT = 9
ID_SIMPDICT = 10
ID_LITTLEDICT = 11
ID_PROVERBDICT = 12
ID_OUTPUT_SIMP_CHINESE = 13


class CinBase:
    def __init__(self):
        self.cinbasecurdir = os.path.abspath(os.path.dirname(__file__))
        self.icondir = os.path.join(os.path.dirname(__file__), "icons")
        self.candselKeys = "1234567890"

        with io.open(os.path.join(os.path.dirname(__file__), "data", "emoji.json"), 'r', encoding='utf8') as fs:
            self.emoji = emoji(fs)

        self.emojimenulist = ["表情符號", "圖形符號", "其它符號", "雜錦符號", "交通運輸", "調色盤"]
        self.imeNameList = ["checj", "chephonetic", "chearray", "chedayi", "cheez", "chepinyin", "chesimplex", "cheliu"]
        self.ReverseCinDict = {}
        self.ReverseCinDict["checj"] = ["checj.json", "mscj3.json", "mscj3-ext.json", "cj-ext.json", "cnscj.json", "thcj.json", "newcj3.json", "cj5.json", "newcj.json", "scj6.json"]
        self.ReverseCinDict["chephonetic"] = ["thphonetic.json", "CnsPhonetic.json", "bpmf.json"]
        self.ReverseCinDict["chearray"] = ["tharray.json", "array30.json", "ar30-big.json", "array40.json"]
        self.ReverseCinDict["chedayi"] = ["thdayi.json", "dayi4.json", "dayi3.json"]
        self.ReverseCinDict["cheez"] = ["ez.json", "ezsmall.json", "ezmid.json", "ezbig.json"]
        self.ReverseCinDict["chepinyin"] = ["thpinyin.json", "pinyin.json", "roman.json"]
        self.ReverseCinDict["chesimplex"] = ["simplecj.json", "simplex.json", "simplex5.json"]
        self.ReverseCinDict["cheliu"] = ["liu.json"]
        self.hcinFileList = ["thphonetic.json", "CnsPhonetic.json", "bpmf.json"]

    # 初始化輸入行為設定
    def initTextService(self, cbTS, TextService):
        cbTS.TextService = TextService
        cbTS.TextService.setSelKeys(cbTS, self.candselKeys)
        # 使用 OpenCC 繁體中文轉簡體
        cbTS.opencc = None

        cbTS.keyboardLayout = 0
        cbTS.selKeys = "1234567890"
        cbTS.langMode = -1
        cbTS.shapeMode = -1
        cbTS.switchPageWithSpace = False
        cbTS.outputSimpChinese = False
        cbTS.hidePromptMessages = True
        cbTS.autoClearCompositionChar = False
        cbTS.playSoundWhenNonCand = False
        cbTS.directShowCand = False
        cbTS.directCommitString = False
        cbTS.directCommitSymbol = False
        cbTS.directCommitSymbolList = ["，", "。", "、", "；", "？", "！"]
        cbTS.bracketSymbolList = ["「」", "『』", "［］", "【】", "〖〗", "〔〕", "﹝﹞", "（）", "﹙﹚", "〈〉", "《》", "＜＞", "﹤﹥", "｛｝", "﹛﹜"]
        cbTS.ignorePrivateUseArea = True
        cbTS.directOutMSymbols = True
        cbTS.fullShapeSymbols = False
        cbTS.directOutFSymbols = False
        cbTS.easySymbolsWithShift = False
        cbTS.showPhrase = False
        cbTS.sortByPhrase = False
        cbTS.compositionBufferMode = False
        cbTS.autoMoveCursorInBrackets = False
        cbTS.imeReverseLookup = False
        cbTS.homophoneQuery = False
        cbTS.userExtendTable = False
        cbTS.reLoadTable = False
        cbTS.priorityExtendTable = False
        cbTS.rcinFileList = []
        cbTS.messageDurationTime = 3

        cbTS.selDayiSymbolCharType = 0
        cbTS.lastKeyDownCode = 0
        cbTS.lastKeyDownTime = 0.0

        cbTS.menucandidates = []
        cbTS.smenucandidates = []
        cbTS.wildcardcandidates = []
        cbTS.wildcardpagecandidates = []
        cbTS.wildcardcompositionChar = ""
        cbTS.currentCandPage = 0

        cbTS.emojitype = 0
        cbTS.prevmenutypelist = []
        cbTS.prevmenucandlist = []

        cbTS.compositionBufferString = ""
        cbTS.compositionBufferCursor = 0
        cbTS.compositionBufferType = "default"
        cbTS.compositionBufferChar = {}
        cbTS.compositionBufferMenuItem = ""
        cbTS.tempengcandidates = []
        cbTS.keyUsedState = False
        cbTS.selcandmode = False

        cbTS.initCinBaseState = False
        cbTS.showmenu = False
        cbTS.switchmenu = False
        cbTS.closemenu = True
        cbTS.tempEnglishMode = False
        cbTS.multifunctionmode = False
        cbTS.menumode = False
        cbTS.emojimenumode = False
        cbTS.menusymbolsmode = False
        cbTS.ctrlsymbolsmode = False
        cbTS.fullsymbolsmode = False
        cbTS.phrasemode = False
        cbTS.isSelKeysChanged = False
        cbTS.isWildcardChardefs = False
        cbTS.isLangModeChanged = False
        cbTS.isShapeModeChanged = False
        cbTS.isShowCandidates = False
        cbTS.isShowPhraseCandidates = False
        cbTS.isShowMessage = False
        cbTS.canSetCommitString = True
        cbTS.canSetPhraseCommitString = False
        cbTS.canUseSelKey = True
        cbTS.canUseSpaceAsPageKey = True
        cbTS.endKeyList = []
        cbTS.useEndKey = False
        cbTS.useDayiSymbols = False
        cbTS.dayisymbolsmode = False
        cbTS.autoShowCandWhenMaxChar = False
        cbTS.lastCommitString = ""
        cbTS.lastCompositionCharLength = 0
        cbTS.menutype = 0
        cbTS.resetMenuCand = False
        cbTS.keepComposition = False
        cbTS.keepType = ""

        cbTS.homophonemode = False
        cbTS.homophoneselpinyinmode = False
        cbTS.homophoneChar = ""
        cbTS.homophoneStr = ""
        cbTS.isHomophoneChardefs = False
        cbTS.homophonecandidates = []

        cbTS.showMessageOnKeyUp = False
        cbTS.hideMessageOnKeyUp = False
        cbTS.onKeyUpMessage = ""
        cbTS.reLoadCinTable = False
        cbTS.capsStates = True if self.getKeyState(VK_CAPITAL) else False

        cbTS.bopomofolist = []
        for i in range(0x3105,0x311A):
            cbTS.bopomofolist.append(chr(i))
        for i in range(0x3127,0x312A):
            cbTS.bopomofolist.append(chr(i))
        for i in range(0x311A,0x3127):
            cbTS.bopomofolist.append(chr(i))
        cbTS.bopomofolist.append(chr(0x02D9))
        cbTS.bopomofolist.append(chr(0x02CA))
        cbTS.bopomofolist.append(chr(0x02C7))
        cbTS.bopomofolist.append(chr(0x02CB))

        if DEBUG_MODE:
            cbTS.debug = Debug(cbTS.imeDirName)
            cbTS.debugLog = cbTS.debug.loadDebugLog()


    # 輸入法被使用者啟用
    def onActivate(self, cbTS):
        # 向系統宣告 Shift + Space 這個組合為特殊用途 (全半形切換)
        # 當 Shift + Space 被按下的時候，onPreservedKey() 會被呼叫
        cbTS.addPreservedKey(VK_SPACE, TF_MOD_SHIFT, SHIFT_SPACE_GUID); # shift + space

        # 切換中英文
        icon_name = "chi.ico" if cbTS.langMode == CHINESE_MODE else "eng.ico"
        cbTS.addButton("switch-lang",
            icon=os.path.join(self.icondir, icon_name),
            tooltip="中英文切換",
            commandId=ID_SWITCH_LANG
        )

        # Windows 8 以上已取消語言列功能，改用 systray IME mode icon
        if cbTS.client.isWindows8Above:
            if cbTS.langMode == CHINESE_MODE:
                if cbTS.shapeMode == FULLSHAPE_MODE:
                    icon_name = "chi_full_capson.ico" if cbTS.capsStates else "chi_full_capsoff.ico"
                else:
                    icon_name = "chi_half_capson.ico" if cbTS.capsStates else "chi_half_capsoff.ico"
            else:
                if cbTS.shapeMode == FULLSHAPE_MODE:
                    icon_name = "eng_full_capson.ico" if cbTS.capsStates else "eng_full_capsoff.ico"
                else:
                    icon_name = "eng_half_capson.ico" if cbTS.capsStates else "eng_half_capsoff.ico"

            cbTS.addButton("windows-mode-icon",
                icon=os.path.join(self.icondir, icon_name),
                tooltip="中英文切換",
                commandId=ID_MODE_ICON
            )
            
            if not cbTS.KeyboardOpen:
                cbTS.changeButton("windows-mode-icon", enable=cbTS.KeyboardOpen)

        # 切換全半形
        icon_name = "full.ico" if cbTS.shapeMode == FULLSHAPE_MODE else "half.ico"
        cbTS.addButton("switch-shape",
            icon = os.path.join(self.icondir, icon_name),
            tooltip = "全形/半形切換",
            commandId = ID_SWITCH_SHAPE
        )

        # 設定
        cbTS.addButton("settings",
            icon = os.path.join(self.icondir, "config.ico"),
            tooltip = "設定",
            type = "menu"
        )


    # 使用者離開輸入法
    def onDeactivate(self, cbTS):
        cbTS.lastKeyDownCode = 0
        # 向系統宣告移除 Shift + Space 這個組合鍵用途 (全半形切換)
        cbTS.removePreservedKey(SHIFT_SPACE_GUID); # shift + space

        cbTS.removeButton("switch-lang")
        cbTS.removeButton("switch-shape")
        cbTS.removeButton("settings")
        if cbTS.client.isWindows8Above:
            cbTS.removeButton("windows-mode-icon")

        if hasattr(cbTS, 'swkb'):
            del cbTS.swkb
        if hasattr(cbTS, 'symbols'):
            del cbTS.symbols
        if hasattr(cbTS, 'fsymbols'):
            del cbTS.fsymbols
        if hasattr(cbTS, 'flangs'):
            del cbTS.flangs
        if hasattr(cbTS, 'userphrase'):
            del cbTS.userphrase
        if hasattr(cbTS, 'msymbols'):
            del cbTS.msymbols
        if hasattr(cbTS, 'extendtable'):
            del cbTS.extendtable
        if hasattr(cbTS, 'dsymbols'):
            del cbTS.dsymbols


    # 使用者按下按鍵，在 app 收到前先過濾那些鍵是輸入法需要的。
    # return True，系統會呼叫 onKeyDown() 進一步處理這個按鍵
    # return False，表示我們不需要這個鍵，系統會原封不動把按鍵傳給應用程式
    def filterKeyDown(self, cbTS, keyEvent, CinTable, RCinTable, HCinTable):
        # 紀錄最後一次按下的鍵和按下的時間，在 filterKeyUp() 中要用
        cbTS.lastKeyDownCode = keyEvent.keyCode
        if cbTS.lastKeyDownTime == 0.0:
            cbTS.lastKeyDownTime = time.time()

        if CinTable.loading:
            return True

        # 使用者開始輸入，還沒送出前的編輯區內容稱 composition string
        # isComposing() 是 False，表示目前編輯區是空的
        # 若正在編輯中文，則任何按鍵我們都需要送給輸入法處理，直接 return True
        # 另外，若使用 "`" key 輸入特殊符號，可能會有編輯區是空的
        # 但選字清單開啟，輸入法需要處理的情況
        if cbTS.isComposing() or cbTS.showCandidates:
            return True

        if cbTS.showPhrase and cbTS.phrasemode and cbTS.isShowPhraseCandidates:
            return True

        # --------------   以下都是「沒有」正在輸入中文的狀況   --------------

        # 如果按下 Alt，可能是應用程式熱鍵，輸入法不做處理
        if keyEvent.isKeyDown(VK_MENU):
            if cbTS.isShowMessage:
                cbTS.hideMessageOnKeyUp = True
            return False

        # 如果按下 Ctrl 鍵
        if keyEvent.isKeyDown(VK_CONTROL):
            # 若按下的是指定的符號鍵，輸入法需要處理此按鍵
            if self.isCtrlSymbolsChar(keyEvent.keyCode) and cbTS.langMode == CHINESE_MODE:
                return True
            else:
                if cbTS.isShowMessage:
                    cbTS.hideMessageOnKeyUp = True
                return False

        # 若按下 Shift 鍵
        if keyEvent.isKeyDown(VK_SHIFT):
            if cbTS.langMode == CHINESE_MODE and not keyEvent.isKeyDown(VK_CONTROL):
                # 若開啟 Shift 快速輸入符號，輸入法需要處理此按鍵
                if cbTS.easySymbolsWithShift and self.isLetterChar(keyEvent.keyCode):
                    return True
                # 若開啟 Shift 輸入全形標點，輸入法需要處理此按鍵
                if cbTS.fullShapeSymbols and (self.isSymbolsChar(keyEvent.keyCode) or self.isNumberChar(keyEvent.keyCode)):
                    return True
                # 若萬用字元使用*，輸入法需要處理*按鍵
                if cbTS.selWildcardChar == '*' and keyEvent.keyCode == 0x38:
                    return True
                if not cbTS.isComposing() and cbTS.compositionBufferMode and not cbTS.directShowCand and cbTS.shapeMode == HALFSHAPE_MODE:
                    return False

        # 不論中英文模式，NumPad 都允許直接輸入數字，輸入法不處理
        if keyEvent.isKeyToggled(VK_NUMLOCK): # NumLock is on
            # if this key is Num pad 0-9, +, -, *, /, pass it back to the system
            if keyEvent.keyCode >= VK_NUMPAD0 and keyEvent.keyCode <= VK_DIVIDE:
                if cbTS.isShowMessage:
                    cbTS.hideMessageOnKeyUp = True
                return False # bypass IME

        # 不管中英文模式，只要是全形可見字元或空白，輸入法都需要進一步處理(半形轉為全形)
        if cbTS.shapeMode == FULLSHAPE_MODE:
            if keyEvent.isPrintableChar() or keyEvent.keyCode == VK_SPACE:
                return True
            else:
                if cbTS.isShowMessage and not keyEvent.isKeyDown(VK_SHIFT):
                    cbTS.hideMessageOnKeyUp = True
                return False

        # --------------   以下皆為半形模式   --------------

        # 如果是英文半形模式，輸入法不做任何處理
        if cbTS.langMode == ENGLISH_MODE:
            if cbTS.isShowMessage and not keyEvent.isKeyDown(VK_SHIFT):
                cbTS.hideMessageOnKeyUp = True
            return False
        # --------------   以下皆為中文模式   --------------

        # 中文模式下，當中文編輯區是空的，輸入法只需處理倉頡字根
        # 檢查按下的鍵是否為倉頡字根
        if cbTS.cin.isInKeyName(chr(keyEvent.charCode).lower()):
            return True

        # 中文模式下，當中文編輯區是空的，且不是預設鍵盤,輸入法需處理其它鍵盤所定義的字根
        # 檢查按下的鍵是否為其它鍵盤定義的字根
        if not cbTS.keyboardLayout == 0:
            if chr(keyEvent.charCode).lower() in cbTS.kbtypelist[cbTS.keyboardLayout]:
                return True

        # 中文模式下，若按下 ` 鍵，讓輸入法進行處理
        if keyEvent.isKeyDown(VK_OEM_3):
            return True


        if cbTS.useDayiSymbols:
            if cbTS.selDayiSymbolCharType == 0:
                if keyEvent.isKeyDown(VK_OEM_PLUS):
                    return True
            else:
                if keyEvent.isKeyDown(VK_OEM_7):
                    return True

        # 其餘狀況一律不處理，原按鍵輸入直接送還給應用程式
        if cbTS.isShowMessage and not keyEvent.isKeyDown(VK_SHIFT):
            cbTS.hideMessageOnKeyUp = True
        return False

    def onKeyDown(self, cbTS, keyEvent, CinTable, RCinTable, HCinTable):
        charCode = keyEvent.charCode
        keyCode = keyEvent.keyCode
        charStr = chr(charCode)
        charStrLow = charStr.lower()

        if CinTable.loading:
            messagestr = '正在載入輸入法碼表，請稍後...'
            cbTS.isShowMessage = True
            cbTS.showMessage(messagestr, cbTS.messageDurationTime)
            return True

        # NumPad 某些狀況允許輸入法處理
        if keyEvent.isKeyToggled(VK_NUMLOCK): # NumLock is on
            # if this key is Num pad 0-9, +, -, *, /, pass it back to the system
            if keyEvent.keyCode >= VK_NUMPAD0 and keyEvent.keyCode <= VK_DIVIDE:
                if not cbTS.compositionBufferMode or cbTS.showCandidates:
                    return True # bypass IME

        if cbTS.compositionBufferMode and not cbTS.isComposing():
            cbTS.compositionBufferType = "default"
            cbTS.compositionBufferChar = {}

        if cbTS.langMode == ENGLISH_MODE:
            if cbTS.isComposing() or cbTS.showCandidates:
                cbTS.tempEnglishMode = True
        else:
            cbTS.tempEnglishMode = False

        if cbTS.tempEnglishMode:
            if not cbTS.showCandidates and keyEvent.isPrintableChar() and not keyEvent.isKeyDown(VK_CONTROL):
                if cbTS.shapeMode == HALFSHAPE_MODE:
                    cbTS.compositionBufferType = "english"
                    self.setCompositionBufferString(cbTS, charStr, 0)
                else:
                    if self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode):
                        cStr = self.SymbolscharCodeToFullshape(charCode)
                    else:
                        cStr = self.charCodeToFullshape(cbTS, charCode, keyCode)
                    cbTS.compositionBufferType = "fullshape"
                    self.setCompositionBufferString(cbTS, cStr, 0)
                self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, charStr, cbTS.compositionBufferCursor)

        # 鍵盤對映 (注音)
        if not cbTS.keyboardLayout == 0 and charStr.lower() in cbTS.kbtypelist[cbTS.keyboardLayout] and not cbTS.tempEnglishMode:
            if not keyEvent.isKeyDown(VK_SHIFT) and not keyEvent.isKeyDown(VK_CONTROL):
                charIndex = cbTS.kbtypelist[cbTS.keyboardLayout].index(charStr.lower())
                charStr = cbTS.kbtypelist[0][charIndex]
                charStrLow = charStr.lower()

        # 檢查選字鍵
        if not cbTS.imeDirName == "chedayi":
            cbTS.selKeys = "1234567890"
            if not self.candselKeys == "1234567890":
                self.candselKeys = "1234567890"
                cbTS.TextService.setSelKeys(cbTS, self.candselKeys)
                cbTS.isSelKeysChanged = True

        if cbTS.autoMoveCursorInBrackets:
            if cbTS.compositionBufferMode and keyEvent.isPrintableChar() and not keyEvent.isKeyDown(VK_SPACE):
                if len(cbTS.compositionBufferString) >= 2 and cbTS.compositionBufferCursor >= 2:
                    self.moveCursorInBrackets(cbTS)

        candidates = []
        cbTS.isWildcardChardefs = False
        cbTS.canSetCommitString = True
        cbTS.keyUsedState = False

        if cbTS.isShowMessage:
            cbTS.isShowMessage = False
            cbTS.showMessage("", 0)

        # 多功能前導字元 ---------------------------------------------------------
        if cbTS.multifunctionmode:
            cbTS.canUseSelKey = True

        if cbTS.langMode == CHINESE_MODE and not cbTS.showmenu:
            if len(cbTS.compositionChar) == 0 and charStr == '`' and not cbTS.imeDirName == "cheez":
                cbTS.compositionChar += charStr
                if cbTS.compositionBufferMode:
                    self.setCompositionBufferString(cbTS, cbTS.compositionChar, 0)
                else:
                    cbTS.setCompositionString(cbTS.compositionChar)
                if not cbTS.hidePromptMessages:
                    cbTS.isShowMessage = True
                    cbTS.showMessageOnKeyUp = True
                    cbTS.onKeyUpMessage = '多功能前導字元'
                cbTS.multifunctionmode = True
            elif len(cbTS.compositionChar) == 1 and cbTS.multifunctionmode:
                if charStrLow == 'm' or charStrLow == 'u' or charStrLow == 'e':
                    cbTS.compositionChar += charStr.upper()
                    if cbTS.compositionBufferMode:
                        self.setCompositionBufferString(cbTS, charStr.upper(), 0)
                    else:
                        cbTS.setCompositionString(cbTS.compositionChar)
                    if charStrLow == 'm':
                        cbTS.multifunctionmode = False
                        cbTS.closemenu = False
                    elif charStrLow == 'e':
                        cbTS.multifunctionmode = False
                        cbTS.closemenu = False
                        cbTS.emojimenumode = True
                elif self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode):
                    if cbTS.imeDirName == "chedayi":
                        if charStr in "'[]-\\":
                            cbTS.canUseSelKey = False
                    else:
                        if self.isNumberChar(keyCode):
                            cbTS.canUseSelKey = False
                    cbTS.compositionChar += charStr
            elif len(cbTS.compositionChar) > 1 and cbTS.multifunctionmode:
                if cbTS.msymbols.isInCharDef(cbTS.compositionChar[1:] + charStr):
                    if cbTS.imeDirName == "chedayi":
                        if charStr in "'[]-\\":
                            cbTS.canUseSelKey = False
                    cbTS.menusymbolsmode = False
                    cbTS.compositionChar += charStr
                elif cbTS.compositionChar[:2] == '`U':
                    if keyCode >= 0x30 and keyCode <= 0x46:
                        cbTS.compositionChar += charStr.upper()
                        if cbTS.compositionBufferMode:
                            self.setCompositionBufferString(cbTS, charStr.upper(), 0)
                        else:
                            cbTS.setCompositionString(cbTS.compositionChar)
                elif cbTS.compositionChar[:2] == '``':
                    if keyCode == VK_OEM_3:
                        cbTS.compositionChar += charStr

            if len(cbTS.compositionChar) == 3 and cbTS.multifunctionmode:
                if cbTS.compositionChar == '```':
                    cbTS.compositionChar = '`M'
                    if cbTS.compositionBufferMode:
                        self.setCompositionBufferString(cbTS, cbTS.compositionChar, 1)
                    else:
                        cbTS.setCompositionString(cbTS.compositionChar)
                    cbTS.multifunctionmode = False
                    cbTS.closemenu = False

        if cbTS.multifunctionmode:
            # 按下 ESC 鍵
            if keyCode == VK_ESCAPE and (cbTS.showCandidates or len(cbTS.compositionChar) > 0):
                if cbTS.compositionBufferMode:
                    removeStringLength = len(cbTS.compositionChar) - 1 if cbTS.menusymbolsmode else len(cbTS.compositionChar)
                    self.removeCompositionBufferString(cbTS, removeStringLength, True)
                self.resetComposition(cbTS)
                return True
            # 刪掉一個字根
            elif keyCode == VK_BACK:
                if cbTS.compositionString != '':
                    if cbTS.compositionBufferMode:
                        removeStringLength = len(cbTS.compositionChar) - 1 if cbTS.menusymbolsmode else 1
                        self.removeCompositionBufferString(cbTS, removeStringLength, True)
                        cbTS.compositionChar = cbTS.compositionChar[:-len(cbTS.compositionChar)] if cbTS.menusymbolsmode else cbTS.compositionChar[:-1]
                    else:
                        cbTS.setCompositionString(cbTS.compositionString[:-1])
                        cbTS.compositionChar = cbTS.compositionChar[:-1]
                    cbTS.setCandidateCursor(0)
                    cbTS.setCandidatePage(0)
                    if cbTS.compositionChar == '':
                        self.resetComposition(cbTS)
                        return True
            elif keyCode == VK_RETURN and cbTS.menusymbolsmode and cbTS.isComposing() and not cbTS.showCandidates:
                cbTS.setCommitString(cbTS.compositionString)
                self.resetComposition(cbTS)
                self.resetCompositionBuffer(cbTS)

            # Unicode 編碼字元超過 5 + 2 個
            if cbTS.compositionChar[:2] == '`U' and len(cbTS.compositionChar) > 7:
                if cbTS.compositionBufferMode:
                    self.removeCompositionBufferString(cbTS, 1, True)
                else:
                    cbTS.setCompositionString(cbTS.compositionString[:-1])
                cbTS.compositionChar = cbTS.compositionChar[:-1]

            if cbTS.msymbols.isInCharDef(cbTS.compositionChar[1:]) and cbTS.closemenu and len(cbTS.compositionChar) >= 2:
                candidates = cbTS.msymbols.getCharDef(cbTS.compositionChar[1:])
                if cbTS.compositionBufferMode:
                    if charStr == '`' and cbTS.menusymbolsmode == True:
                        cbTS.compositionBufferType = "msymbols"
                        commitStr = ""
                        if cbTS.compositionBufferString[cbTS.compositionBufferCursor - 1] in candidates:
                            commitStr = cbTS.compositionBufferString[cbTS.compositionBufferCursor - 1]
                        elif cbTS.compositionBufferString[cbTS.compositionBufferCursor - 2] + cbTS.compositionBufferString[cbTS.compositionBufferCursor - 1] in candidates:
                            commitStr = cbTS.compositionBufferString[cbTS.compositionBufferCursor - 2] + cbTS.compositionBufferString[cbTS.compositionBufferCursor - 1]
                        strLength = len(commitStr)
                        if strLength >= 1:
                            for cStr in commitStr:
                                strLength -= 1
                                cChar = cbTS.compositionChar[commitStr.index(cStr)] if cbTS.compositionChar[0] != "`" else cbTS.compositionChar[commitStr.index(cStr) + 1]
                                self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, cChar, cbTS.compositionBufferCursor - strLength)
                        self.resetComposition(cbTS)
                        cbTS.menusymbolsmode = False
                        cbTS.multifunctionmode = True
                        cbTS.compositionChar = "`"
                        self.setCompositionBufferString(cbTS, charStr, 1 if cbTS.directShowCand and not cbTS.directOutMSymbols else 0)
                    else:
                        if len(cbTS.compositionBufferString) >= 2:
                            prevStr = cbTS.compositionBufferString[cbTS.compositionBufferCursor - 2] + cbTS.compositionBufferString[cbTS.compositionBufferCursor - 1]
                            if prevStr == candidates[0]:
                                self.removeCompositionBufferString(cbTS, 1, True)
                        cbTS.compositionBufferType = "msymbols"
                        self.setCompositionBufferString(cbTS, candidates[0], 1)
                else:
                    if charStr == '`' and cbTS.menusymbolsmode == True:
                        commitStr = cbTS.compositionString
                        self.resetComposition(cbTS)

                        if cbTS.directOutMSymbols:
                            cbTS.setCommitString(commitStr)
                            cbTS.keepComposition = True
                            cbTS.keepType = "menusymbols"

                        cbTS.menusymbolsmode = False
                        cbTS.multifunctionmode = True
                        cbTS.compositionChar = "`"
                        cbTS.setCompositionString("`")
                        if cbTS.directOutMSymbols:
                            return True
                    else:
                        cbTS.setCompositionString(candidates[0])
                    cbTS.setCompositionCursor(len(cbTS.compositionString))

        if cbTS.multifunctionmode and not cbTS.menusymbolsmode and cbTS.directCommitSymbol:
            if cbTS.msymbols.isInCharDef(cbTS.compositionChar[1:]):
                cbTS.menusymbolsmode = True
        elif cbTS.multifunctionmode and cbTS.menusymbolsmode and cbTS.directCommitSymbol and keyEvent.isPrintableChar():
            if not cbTS.msymbols.isInCharDef(cbTS.compositionChar[1:] + charStr) and cbTS.cin.isInKeyName(charStrLow):
                if not cbTS.compositionBufferMode:
                    cbTS.setCommitString(cbTS.compositionString)
                    self.resetComposition(cbTS)
                    cbTS.keepComposition = True
                else:
                    cbTS.compositionBufferType = "msymbols"
                    commitStrList = cbTS.msymbols.getCharDef(cbTS.compositionChar[1:])
                    commitStr = ""
                    if cbTS.compositionBufferString[cbTS.compositionBufferCursor - 1] in commitStrList:
                        commitStr = cbTS.compositionBufferString[cbTS.compositionBufferCursor - 1]
                    elif cbTS.compositionBufferString[cbTS.compositionBufferCursor - 2] + cbTS.compositionBufferString[cbTS.compositionBufferCursor - 1] in commitStrList:
                        commitStr = cbTS.compositionBufferString[cbTS.compositionBufferCursor - 2] + cbTS.compositionBufferString[cbTS.compositionBufferCursor - 1]
                    strLength = len(commitStr)
                    if strLength >= 1:
                        for cStr in commitStr:
                            strLength -= 1
                            cChar = cbTS.compositionChar[commitStr.index(cStr)] if cbTS.compositionChar[0] != "`" else cbTS.compositionChar[commitStr.index(cStr) + 1]
                            self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, cChar, cbTS.compositionBufferCursor - strLength)
                    self.resetComposition(cbTS)
                    cbTS.menusymbolsmode = False
        elif cbTS.multifunctionmode and not cbTS.menusymbolsmode and not cbTS.directCommitSymbol:
            if cbTS.msymbols.isInCharDef(cbTS.compositionChar[1:]):
                cbTS.menusymbolsmode = True

        # 輕鬆輸入法進入選單模式
        if cbTS.langMode == CHINESE_MODE and cbTS.imeDirName == "cheez" and cbTS.compositionChar + charStrLow == 'menu':
            cbTS.compositionChar = '`M'
            if cbTS.compositionBufferMode:
                self.setCompositionBufferString(cbTS, cbTS.compositionChar, 3)
            else:
                cbTS.setCompositionString(cbTS.compositionChar)
            cbTS.multifunctionmode = False
            cbTS.closemenu = False


        # 功能選單 ----------------------------------------------------------------
        if cbTS.langMode == CHINESE_MODE and (cbTS.compositionChar == "`M" or cbTS.compositionChar == "`E"):
            menu_OutputSimpChinese = "輸出繁體" if cbTS.outputSimpChinese else "輸出簡體"
            menu_fullShapeSymbols = "☑ Shift 輸入全形標點" if cbTS.fullShapeSymbols else "☐ Shift 輸入全形標點"
            menu_easySymbolsWithShift = "☑ Shift 快速輸入符號" if cbTS.easySymbolsWithShift else "☐ Shift 快速輸入符號"
            menu_autoClearCompositionChar = "☑ 拆錯字碼時自動清除輸入字串" if cbTS.autoClearCompositionChar else "☐ 拆錯字碼時自動清除輸入字串"
            menu_playSoundWhenNonCand = "☑ 拆錯字碼時發出警告嗶聲提示" if cbTS.playSoundWhenNonCand else "☐ 拆錯字碼時發出警告嗶聲提示"
            menu_showPhrase = "☑ 輸出字串後顯示聯想字詞" if cbTS.showPhrase else "☐ 輸出字串後顯示聯想字詞"
            menu_sortByPhrase = "☑ 優先以聯想字詞排序候選清單" if cbTS.sortByPhrase else "☐ 優先以聯想字詞排序候選清單"
            menu_supportWildcard = "☑ 萬用字元查詢" if cbTS.supportWildcard else "☐ 萬用字元查詢"
            menu_imeReverseLookup = "☑ 反查輸入字根" if cbTS.imeReverseLookup else "☐ 反查輸入字根"
            menu_homophoneQuery = "☑ 同音字查詢" if cbTS.homophoneQuery else "☐ 同音字查詢"

            if cbTS.imeDirName == "chephonetic":
                cbTS.smenucandidates = [menu_fullShapeSymbols, menu_easySymbolsWithShift, menu_autoClearCompositionChar, menu_playSoundWhenNonCand, menu_showPhrase, menu_sortByPhrase, menu_imeReverseLookup, menu_homophoneQuery]
                cbTS.smenuitems =  ["fullShapeSymbols", "easySymbolsWithShift", "autoClearCompositionChar", "playSoundWhenNonCand", "showPhrase", "sortByPhrase", "imeReverseLookup", "homophoneQuery"]
            elif cbTS.imeDirName == "cheez":
                cbTS.smenucandidates = [menu_autoClearCompositionChar, menu_playSoundWhenNonCand, menu_showPhrase, menu_sortByPhrase, menu_supportWildcard, menu_imeReverseLookup]
                cbTS.smenuitems = ["autoClearCompositionChar", "playSoundWhenNonCand", "showPhrase", "sortByPhrase", "supportWildcard", "imeReverseLookup"]
            elif cbTS.imeDirName == "chearray" or cbTS.imeDirName == "chedayi":
                cbTS.smenucandidates = [menu_fullShapeSymbols, menu_easySymbolsWithShift, menu_autoClearCompositionChar, menu_playSoundWhenNonCand, menu_showPhrase, menu_sortByPhrase, menu_supportWildcard, menu_imeReverseLookup, menu_homophoneQuery]
                cbTS.smenuitems = ["fullShapeSymbols", "easySymbolsWithShift", "autoClearCompositionChar", "playSoundWhenNonCand", "showPhrase", "sortByPhrase", "supportWildcard", "imeReverseLookup", "homophoneQuery"]
            else:
                cbTS.smenucandidates = [menu_fullShapeSymbols, menu_easySymbolsWithShift, menu_autoClearCompositionChar, menu_playSoundWhenNonCand, menu_showPhrase, menu_sortByPhrase, menu_supportWildcard, menu_imeReverseLookup, menu_homophoneQuery]
                cbTS.smenuitems = ["fullShapeSymbols", "easySymbolsWithShift", "autoClearCompositionChar", "playSoundWhenNonCand", "showPhrase", "sortByPhrase", "supportWildcard", "imeReverseLookup", "homophoneQuery"]

            if not cbTS.closemenu:
                cbTS.setCandidateCursor(0)
                cbTS.setCandidatePage(0)

                # 大易須更換選字鍵
                if cbTS.imeDirName == "chedayi":
                    cbTS.selKeys = "1234567890"
                    if not self.candselKeys == "1234567890":
                        self.candselKeys = "1234567890"
                        cbTS.TextService.setSelKeys(cbTS, self.candselKeys)
                        cbTS.isShowCandidates = True
                        cbTS.isSelKeysChanged = True

                if not cbTS.emojimenumode:
                    cbTS.menutype = 0
                    menu = ["功能設定", menu_OutputSimpChinese, "功能開關", "特殊符號", "注音符號", "外語文字", "表情符號"]
                    cbTS.setCandidateList(menu)
                else:
                    cbTS.menutype = 7
                    cbTS.setCandidateList(self.emojimenulist)

                cbTS.menucandidates = cbTS.candidateList
                cbTS.prevmenutypelist = []
                cbTS.prevmenucandlist = []
                cbTS.showmenu = True

            if cbTS.showmenu:
                cbTS.menumode = True
                cbTS.closemenu = False
                candidates = cbTS.menucandidates
                candCursor = cbTS.candidateCursor  # 目前的游標位置
                candCount = len(cbTS.candidateList)  # 目前選字清單項目數
                currentCandPageCount = math.ceil(len(candidates) / cbTS.candPerPage) # 目前的選字清單總頁數
                currentCandPage = cbTS.currentCandPage # 目前的選字清單頁數

                # 候選清單分頁
                pagecandidates = list(self.chunks(candidates, cbTS.candPerPage))
                cbTS.setCandidateList(pagecandidates[currentCandPage])
                if not cbTS.isSelKeysChanged:
                    cbTS.setShowCandidates(True)
                cbTS.resetMenuCand = False
                itemName = ""

                # 選單按鍵處理
                if keyCode == VK_UP:  # 游標上移
                    if (candCursor - cbTS.candPerRow) < 0:
                        if currentCandPage > 0:
                            currentCandPage -= 1
                            candCursor = 0
                    else:
                        if (candCursor - cbTS.candPerRow) >= 0:
                            candCursor = candCursor - cbTS.candPerRow
                elif keyCode == VK_DOWN:  # 游標下移
                    if (candCursor + cbTS.candPerRow) >= cbTS.candPerPage:
                        if (currentCandPage + 1) < currentCandPageCount:
                            currentCandPage += 1
                            candCursor = 0
                    else:
                        if (candCursor + cbTS.candPerRow) < len(pagecandidates[currentCandPage]):
                            candCursor = candCursor + cbTS.candPerRow
                elif keyCode == VK_LEFT:  # 游標左移
                    if candCursor > 0:
                        candCursor -= 1
                    else:
                        if currentCandPage > 0:
                            currentCandPage -= 1
                            candCursor = 0
                elif keyCode == VK_RIGHT:  # 游標右移
                    if (candCursor + 1) < candCount:
                        candCursor += 1
                    else:
                        if (currentCandPage + 1) < currentCandPageCount:
                            currentCandPage += 1
                            candCursor = 0
                elif keyCode == VK_HOME:  # Home 鍵
                    candCursor = 0
                elif keyCode == VK_END:  # End 鍵
                    candCursor = len(pagecandidates[currentCandPage]) - 1
                elif keyCode == VK_PRIOR:  # Page UP 鍵
                    if currentCandPage > 0:
                        currentCandPage -= 1
                        candCursor = 0
                elif keyCode == VK_NEXT:  # Page Down 鍵
                    if (currentCandPage + 1) < currentCandPageCount:
                        currentCandPage += 1
                        candCursor = 0
                elif keyCode == VK_ESCAPE: # ESC 鍵
                    candCursor = 0
                    currentCandPage = 0
                    cbTS.showmenu = False
                    cbTS.emojimenumode = False
                    cbTS.menutype = 0
                    cbTS.prevmenutypelist = []
                    cbTS.prevmenucandlist = []
                    if cbTS.compositionBufferMode:
                        self.removeCompositionBufferString(cbTS, len(cbTS.compositionChar), True)
                    self.resetComposition(cbTS)
                elif self.isInSelKeys(cbTS, charCode) and not keyEvent.isKeyDown(VK_SHIFT): # 使用選字鍵執行項目或輸出候選字
                    if cbTS.selKeys.index(charStr) < cbTS.candPerPage and cbTS.selKeys.index(charStr) < len(cbTS.candidateList):
                        candCursor = cbTS.selKeys.index(charStr)
                        itemName = cbTS.candidateList[candCursor]
                        cbTS.switchmenu = True
                elif keyCode == VK_RETURN:  # 按下 Enter 鍵
                    itemName = cbTS.candidateList[candCursor]
                    cbTS.switchmenu = True
                elif keyCode == VK_SPACE: # 按下空白鍵
                    if cbTS.switchPageWithSpace:
                        if (currentCandPage + 1) < currentCandPageCount:
                            currentCandPage += 1
                            candCursor = 0
                        else:
                            currentCandPage = 0
                            candCursor = 0
                    else:
                        itemName = cbTS.candidateList[candCursor]
                        cbTS.switchmenu = True
                elif keyCode == VK_BACK:
                    if cbTS.prevmenutypelist:
                        prevmenulist =[]
                        prevmenutype = len(cbTS.prevmenutypelist) - 1
                        prevmenulist = cbTS.prevmenutypelist[prevmenutype].split(',', 2)
                        cbTS.menutype = int(prevmenulist[0], 10)
                        cbTS.prevmenucandlist = []
                        cbTS.prevmenucandlist.append(int(prevmenulist[1], 10))
                        cbTS.prevmenucandlist.append(int(prevmenulist[2], 10))
                        cbTS.prevmenutypelist.remove(cbTS.prevmenutypelist[prevmenutype])
                        pagecandidates = self.switchMenuCand(cbTS, cbTS.menutype)

                # 選單切換及執行
                if cbTS.switchmenu and not itemName == "":
                    cbTS.switchmenu = False
                    if cbTS.menutype == 0 and itemName == "功能開關": # 切至功能開關頁面
                        cbTS.menucandidates = cbTS.smenucandidates
                        pagecandidates = list(self.chunks(cbTS.menucandidates, cbTS.candPerPage))
                        cbTS.resetMenuCand = self.switchMenuType(cbTS, 1, ["0," + str(candCursor) + "," + str(currentCandPage)])
                    elif cbTS.menutype == 0 and itemName == "特殊符號": # 切至特殊符號頁面
                        cbTS.menucandidates = cbTS.symbols.getKeyNames()
                        pagecandidates = list(self.chunks(cbTS.menucandidates, cbTS.candPerPage))
                        cbTS.resetMenuCand = self.switchMenuType(cbTS, 2, ["0," + str(candCursor) + "," + str(currentCandPage)])
                    elif cbTS.menutype == 0 and itemName == "注音符號": # 切至注音符號頁面
                        cbTS.menucandidates = cbTS.bopomofolist
                        pagecandidates = list(self.chunks(cbTS.menucandidates, cbTS.candPerPage))
                        cbTS.resetMenuCand = self.switchMenuType(cbTS, 4, ["0," + str(candCursor) + "," + str(currentCandPage)])
                    elif cbTS.menutype == 0 and itemName == "外語文字": # 切至外語文字頁面
                        cbTS.menucandidates = cbTS.flangs.getKeyNames()
                        pagecandidates = list(self.chunks(cbTS.menucandidates, cbTS.candPerPage))
                        cbTS.resetMenuCand = self.switchMenuType(cbTS, 5, ["0," + str(candCursor) + "," + str(currentCandPage)])
                    elif cbTS.menutype == 0 and itemName == "表情符號": # 切至表情符號頁面
                        cbTS.menucandidates = self.emojimenulist
                        pagecandidates = list(self.chunks(cbTS.menucandidates, cbTS.candPerPage))
                        if not cbTS.emojimenumode:
                            cbTS.resetMenuCand = self.switchMenuType(cbTS, 7, ["0," + str(candCursor) + "," + str(currentCandPage)])
                        else:
                            cbTS.resetMenuCand = self.switchMenuType(cbTS, 7, [])
                    elif cbTS.menutype == 0: # 執行主頁面其它項目
                        menu = ["功能設定", menu_OutputSimpChinese, "功能開關", "特殊符號", "注音符號", "外語文字", "表情符號"]
                        i = menu.index(itemName)
                        self.onMenuCommand(cbTS, i, 0)
                        if cbTS.compositionBufferMode:
                            self.removeCompositionBufferString(cbTS, len(cbTS.compositionChar), True)
                        cbTS.resetMenuCand = self.closeMenuCand(cbTS)
                    elif cbTS.menutype == 1: # 執行功能開關頁面項目
                        i = cbTS.smenucandidates.index(itemName)
                        self.onMenuCommand(cbTS, i, 1)
                        if cbTS.compositionBufferMode:
                            self.removeCompositionBufferString(cbTS, len(cbTS.compositionChar), True)
                        cbTS.resetMenuCand = self.closeMenuCand(cbTS)
                    elif cbTS.menutype == 2: # 切至特殊符號子頁面
                        if cbTS.compositionBufferMode:
                            cbTS.compositionBufferMenuItem = cbTS.candidateList[candCursor]
                        cbTS.menucandidates = cbTS.symbols.getCharDef(cbTS.candidateList[candCursor])
                        pagecandidates = list(self.chunks(cbTS.menucandidates, cbTS.candPerPage))
                        cbTS.resetMenuCand = self.switchMenuType(cbTS, 3, ["2," + str(candCursor) + "," + str(currentCandPage)])
                    elif cbTS.menutype == 3: # 執行特殊符號子頁面項目
                        if cbTS.compositionBufferMode:
                            self.removeCompositionBufferString(cbTS, len(cbTS.compositionChar), True)
                            self.setCompositionBufferString(cbTS, cbTS.candidateList[candCursor], 0)
                            cbTS.compositionBufferType = "menusymbols"
                            self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, cbTS.compositionBufferMenuItem, cbTS.compositionBufferCursor)
                        else:
                            cbTS.setCommitString(cbTS.candidateList[candCursor])
                        cbTS.resetMenuCand = self.closeMenuCand(cbTS)
                    elif cbTS.menutype == 4: # 執行注音符號頁面項目
                        if cbTS.compositionBufferMode:
                            self.removeCompositionBufferString(cbTS, len(cbTS.compositionChar), True)
                            self.setCompositionBufferString(cbTS, cbTS.candidateList[candCursor], 0)
                            cbTS.compositionBufferType = "menubopomofo"
                            self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, 'none', cbTS.compositionBufferCursor)
                        else:
                            cbTS.setCommitString(cbTS.candidateList[candCursor])
                        cbTS.resetMenuCand = self.closeMenuCand(cbTS)
                    elif cbTS.menutype == 5: # 切至外語文字子頁面
                        if cbTS.compositionBufferMode:
                            cbTS.compositionBufferMenuItem = cbTS.candidateList[candCursor]
                        cbTS.menucandidates = cbTS.flangs.getCharDef(cbTS.candidateList[candCursor])
                        pagecandidates = list(self.chunks(cbTS.menucandidates, cbTS.candPerPage))
                        cbTS.resetMenuCand = self.switchMenuType(cbTS, 6, ["5," + str(candCursor) + "," + str(currentCandPage)])
                    elif cbTS.menutype == 6: # 執行外語文字子頁面項目
                        if cbTS.compositionBufferMode:
                            self.removeCompositionBufferString(cbTS, len(cbTS.compositionChar), True)
                            self.setCompositionBufferString(cbTS, cbTS.candidateList[candCursor], 0)
                            cbTS.compositionBufferType = "menuflangs"
                            self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, cbTS.compositionBufferMenuItem, cbTS.compositionBufferCursor)
                        else:
                            cbTS.setCommitString(cbTS.candidateList[candCursor])
                        cbTS.resetMenuCand = self.closeMenuCand(cbTS)
                    elif cbTS.menutype == 7: # 切換至表情符號分類頁面
                        menutype = 8
                        i = self.emojimenulist.index(cbTS.candidateList[candCursor])
                        if i == 0:
                            cbTS.emojitype = 0
                            cbTS.menucandidates = self.emoji.emoticons_keynames
                        elif i == 1:
                            cbTS.emojitype = 1
                            cbTS.menucandidates = self.emoji.pictographs_keynames
                        elif i == 2:
                            cbTS.emojitype = 2
                            cbTS.menucandidates = self.emoji.miscellaneous_keynames
                        elif i == 3:
                            cbTS.emojitype = 3
                            cbTS.menucandidates = self.emoji.dingbats_keynames
                        elif i == 4:
                            cbTS.emojitype = 4
                            cbTS.menucandidates = self.emoji.transport_keynames
                        elif i == 5:
                            cbTS.emojitype = 5
                            cbTS.menucandidates = self.emoji.modifiercolor
                            menutype = 9
                        pagecandidates = list(self.chunks(cbTS.menucandidates, cbTS.candPerPage))
                        cbTS.resetMenuCand = self.switchMenuType(cbTS, menutype, ["7," + str(candCursor) + "," + str(currentCandPage)])
                    elif cbTS.menutype == 8: # 切換至表情符號分類子頁面
                        if cbTS.emojitype == 0:
                            if cbTS.compositionBufferMode:
                                cbTS.compositionBufferMenuItem = "emoticons," + cbTS.candidateList[candCursor]
                            cbTS.menucandidates = self.emoji.getCharDef("emoticons", cbTS.candidateList[candCursor])
                        elif cbTS.emojitype == 1:
                            if cbTS.compositionBufferMode:
                                cbTS.compositionBufferMenuItem = "pictographs," + cbTS.candidateList[candCursor]
                            cbTS.menucandidates = self.emoji.getCharDef("pictographs", cbTS.candidateList[candCursor])
                        elif cbTS.emojitype == 2:
                            if cbTS.compositionBufferMode:
                                cbTS.compositionBufferMenuItem = "miscellaneous," + cbTS.candidateList[candCursor]
                            cbTS.menucandidates = self.emoji.getCharDef("miscellaneous", cbTS.candidateList[candCursor])
                        elif cbTS.emojitype == 3:
                            if cbTS.compositionBufferMode:
                                cbTS.compositionBufferMenuItem = "dingbats," + cbTS.candidateList[candCursor]
                            cbTS.menucandidates = self.emoji.getCharDef("dingbats", cbTS.candidateList[candCursor])
                        elif cbTS.emojitype == 4:
                            if cbTS.compositionBufferMode:
                                cbTS.compositionBufferMenuItem = "transport," + cbTS.candidateList[candCursor]
                            cbTS.menucandidates = self.emoji.getCharDef("transport", cbTS.candidateList[candCursor])
                        pagecandidates = list(self.chunks(cbTS.menucandidates, cbTS.candPerPage))
                        cbTS.resetMenuCand = self.switchMenuType(cbTS, 9, ["8," + str(candCursor) + "," + str(currentCandPage)])
                    elif cbTS.menutype == 9: # 執行表情符號分類子頁面項目
                        if cbTS.compositionBufferMode:
                            self.removeCompositionBufferString(cbTS, len(cbTS.compositionChar), True)
                            self.setCompositionBufferString(cbTS, cbTS.candidateList[candCursor], 0)
                            cbTS.compositionBufferType = "menuemoji"
                            self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, cbTS.compositionBufferMenuItem, cbTS.compositionBufferCursor)
                        else:
                            cbTS.setCommitString(cbTS.candidateList[candCursor])
                        cbTS.resetMenuCand = self.closeMenuCand(cbTS)

                if cbTS.prevmenucandlist:
                    candCursor = cbTS.prevmenucandlist[0]
                    currentCandPage = cbTS.prevmenucandlist[1]
                    cbTS.prevmenucandlist = []

                if cbTS.resetMenuCand:
                    candCursor = 0
                    currentCandPage = 0

                # 更新選字視窗游標位置
                cbTS.setCandidateCursor(candCursor)
                cbTS.setCandidatePage(currentCandPage)
                cbTS.setCandidateList(pagecandidates[currentCandPage])

        # 按鍵處理 ----------------------------------------------------------------
        # 某些狀況須要特別處理或忽略
        # 如果輸入編輯區為空且選單未開啟過，不處理 Enter 及 Backspace 鍵
        if not cbTS.isComposing() and cbTS.closemenu and not cbTS.multifunctionmode:
            if keyCode == VK_RETURN or keyCode == VK_BACK:
                return False

        # 若按下 Shift 鍵,且沒有按下其它的按鍵
        if keyEvent.isKeyDown(VK_SHIFT) and not keyEvent.isPrintableChar():
            return False

        # 若按下 Ctrl 鍵
        if cbTS.langMode == CHINESE_MODE and keyEvent.isKeyDown(VK_CONTROL):
            # 若按下的是指定的符號鍵，輸入法需要處理此按鍵
            if self.isCtrlSymbolsChar(keyCode):
                if cbTS.msymbols.isInCharDef(charStr) and cbTS.closemenu and not cbTS.multifunctionmode:
                    if cbTS.homophoneQuery and cbTS.homophonemode:
                        self.resetHomophoneMode(cbTS)

                    if not cbTS.compositionBufferMode:
                        if not cbTS.ctrlsymbolsmode:
                            cbTS.ctrlsymbolsmode = True
                            cbTS.compositionChar = charStr
                        elif cbTS.msymbols.isInCharDef(cbTS.compositionChar + charStr):
                            cbTS.compositionChar += charStr
                        elif cbTS.ctrlsymbolsmode and cbTS.compositionChar != '':
                            commitStr = cbTS.compositionString
                            self.resetComposition(cbTS)

                            if cbTS.directOutMSymbols:
                                cbTS.setCommitString(commitStr)
                                cbTS.keepComposition = True
                                cbTS.keepType = "ctrlsymbols"
                                cbTS.ctrlsymbolsmode = True

                            cbTS.compositionChar = charStr
                        candidates = cbTS.msymbols.getCharDef(cbTS.compositionChar)
                        cbTS.setCompositionString(candidates[0])
                    else:
                        if not cbTS.ctrlsymbolsmode and cbTS.compositionChar == '':
                            cbTS.ctrlsymbolsmode = True
                            cbTS.compositionChar = charStr
                            candidates = cbTS.msymbols.getCharDef(cbTS.compositionChar)
                            self.setCompositionBufferString(cbTS, candidates[0], 0)
                        elif cbTS.msymbols.isInCharDef(cbTS.compositionChar + charStr):
                            candidates = cbTS.msymbols.getCharDef(cbTS.compositionChar)
                            self.removeCompositionBufferString(cbTS, len(candidates[0]), True)
                            cbTS.compositionChar += charStr
                            candidates = cbTS.msymbols.getCharDef(cbTS.compositionChar)
                            self.setCompositionBufferString(cbTS, candidates[0], 0)
                        elif cbTS.ctrlsymbolsmode and cbTS.compositionChar != '':
                            RemoveStringLength = self.calcRemoveStringLength(cbTS) if cbTS.directShowCand and not cbTS.directOutMSymbols else 0
                            cbTS.compositionBufferType = "msymbols"
                            commitStrList = cbTS.msymbols.getCharDef(cbTS.compositionChar)
                            commitStr = ""
                            if cbTS.compositionBufferString[cbTS.compositionBufferCursor - 1] in commitStrList:
                                commitStr = cbTS.compositionBufferString[cbTS.compositionBufferCursor - 1]
                            elif cbTS.compositionBufferString[cbTS.compositionBufferCursor - 2] + cbTS.compositionBufferString[cbTS.compositionBufferCursor - 1] in commitStrList:
                                commitStr = cbTS.compositionBufferString[cbTS.compositionBufferCursor - 2] + cbTS.compositionBufferString[cbTS.compositionBufferCursor - 1]
                            strLength = len(commitStr)
                            if strLength >= 1:
                                for cStr in commitStr:
                                    strLength -= 1
                                    cChar = cbTS.compositionChar[commitStr.index(cStr)]
                                    self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, cChar, cbTS.compositionBufferCursor - strLength)
                            cbTS.compositionChar = charStr
                            candidates = cbTS.msymbols.getCharDef(cbTS.compositionChar)
                            self.setCompositionBufferString(cbTS, candidates[0], RemoveStringLength)
                    if cbTS.imeDirName == "chedayi":
                        if charStr in "'[]-\\":
                            cbTS.canUseSelKey = False

        if cbTS.ctrlsymbolsmode and keyCode == VK_RETURN and cbTS.isComposing() and not cbTS.showCandidates:
            cbTS.setCommitString(cbTS.compositionString)
            self.resetComposition(cbTS)
            self.resetCompositionBuffer(cbTS)

        if cbTS.ctrlsymbolsmode and cbTS.directCommitSymbol and not keyEvent.isKeyDown(VK_CONTROL) and keyEvent.isPrintableChar():
            if not cbTS.msymbols.isInCharDef(cbTS.compositionChar + charStr) and cbTS.cin.isInKeyName(charStrLow):
                if not cbTS.compositionBufferMode:
                    cbTS.setCommitString(cbTS.compositionString)
                    self.resetComposition(cbTS)
                    cbTS.keepComposition = True
                else:
                    cbTS.compositionBufferType = "msymbols"
                    commitStrList = cbTS.msymbols.getCharDef(cbTS.compositionChar)
                    commitStr = ""
                    if cbTS.compositionBufferString[cbTS.compositionBufferCursor - 1] in commitStrList:
                        commitStr = cbTS.compositionBufferString[cbTS.compositionBufferCursor - 1]
                    elif cbTS.compositionBufferString[cbTS.compositionBufferCursor - 2] + cbTS.compositionBufferString[cbTS.compositionBufferCursor - 1] in commitStrList:
                        commitStr = cbTS.compositionBufferString[cbTS.compositionBufferCursor - 2] + cbTS.compositionBufferString[cbTS.compositionBufferCursor - 1]
                    strLength = len(commitStr)
                    if strLength >= 1:
                        for cStr in commitStr:
                            strLength -= 1
                            cChar = cbTS.compositionChar[commitStr.index(cStr)]
                            self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, cChar, cbTS.compositionBufferCursor - strLength)
                    self.resetComposition(cbTS)
                cbTS.ctrlsymbolsmode = False

        # 大易須換回選字鍵
        if not cbTS.showmenu:
            if cbTS.imeDirName == "chedayi":
                cbTS.selKeys = "'[]-\\"
                if not self.candselKeys == "0123456789":
                    self.candselKeys = "0123456789"
                    cbTS.TextService.setSelKeys(cbTS, self.candselKeys)
                    cbTS.isSelKeysChanged = True

        # 按下的鍵為 CIN 內有定義的字根
        if cbTS.cin.isInKeyName(charStrLow) and cbTS.closemenu and not cbTS.multifunctionmode and not keyEvent.isKeyDown(VK_CONTROL) and not cbTS.ctrlsymbolsmode and not cbTS.dayisymbolsmode and not cbTS.selcandmode and not cbTS.tempEnglishMode and not cbTS.phrasemode:
            # 若按下 Shift 鍵
            if keyEvent.isKeyDown(VK_SHIFT) and cbTS.langMode == CHINESE_MODE and not cbTS.imeDirName == "cheez":
                CommitStr = charStr
                # 如果按鍵及萬用字元為*
                if charStr == '*' and cbTS.supportWildcard and cbTS.selWildcardChar == charStr: 
                    keyname = '＊'
                    if cbTS.compositionBufferMode:
                        if (len(cbTS.compositionChar) < cbTS.maxCharLength):
                            cbTS.compositionChar += '*'
                            self.setCompositionBufferString(cbTS, keyname, 0)
                    else:
                        cbTS.compositionChar += '*'
                        cbTS.setCompositionString(cbTS.compositionString + keyname)
                # 使用 Shift 鍵做全形輸入 (easy symbol input)
                # 這裡的 easy symbol input，是定義在 swkb.dat 設定檔中的符號
                elif cbTS.easySymbolsWithShift and self.isLetterChar(keyCode):
                    if cbTS.swkb.isInCharDef(charStr.upper()):
                        candidates = cbTS.swkb.getCharDef(charStr.upper())
                        CommitStr = candidates[0]
                        candidates = []
                    else: # 不在快速符號表裡
                        if cbTS.shapeMode == FULLSHAPE_MODE: # 全形模式
                            CommitStr = self.charCodeToFullshape(cbTS, charCode, keyCode)
                        else:
                            if cbTS.outputSmallLetterWithShift:
                                CommitStr = charStr.upper() if cbTS.capsStates else charStr.lower()
                    if cbTS.compositionBufferMode:
                        RemoveStringLength = 0
                        if not cbTS.compositionChar == '':
                            RemoveStringLength = self.calcRemoveStringLength(cbTS)
                        self.setCompositionBufferString(cbTS, CommitStr, RemoveStringLength)

                        if cbTS.swkb.isInCharDef(charStr.upper()):
                            cbTS.compositionBufferType = "swkb"
                            for char in CommitStr:
                                self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, charStr, cbTS.compositionBufferCursor - CommitStr.index(char))
                        else:
                            cbTS.compositionBufferType = "fullshape" if cbTS.shapeMode == FULLSHAPE_MODE else "english"
                            self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, charStr, cbTS.compositionBufferCursor)
                    else:
                        cbTS.setCommitString(CommitStr)
                    self.resetComposition(cbTS)
                # 如果啟用 Shift 輸入全形標點
                elif cbTS.fullShapeSymbols:
                    # 如果是符號或數字，將字串轉為全形再輸出
                    if self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode):
                        if cbTS.fsymbols.isInCharDef(charStr):
                            self.setOutputFSymbols(cbTS, charStr)
                        else:
                            if cbTS.cin.isInKeyName(charStrLow): # 如果是 CIN 所定義的字根
                                RemoveStringLength = 0
                                if cbTS.compositionBufferMode:
                                    if not cbTS.compositionChar == '':
                                        RemoveStringLength = self.calcRemoveStringLength(cbTS)

                                cbTS.compositionChar = charStrLow
                                keyname = cbTS.cin.getKeyName(charStrLow)

                                if cbTS.compositionBufferMode:
                                    self.setCompositionBufferString(cbTS, keyname, RemoveStringLength)
                                    if not cbTS.directShowCand:
                                        self.resetComposition(cbTS)
                                else:
                                    cbTS.setCompositionString(keyname)
                                    cbTS.setCompositionCursor(len(cbTS.compositionString))
                            else:
                                if cbTS.shapeMode == FULLSHAPE_MODE: # 全形模式
                                    CommitStr = self.SymbolscharCodeToFullshape(charCode)
                                if cbTS.compositionBufferMode:
                                    RemoveStringLength = 0
                                    if not cbTS.compositionChar == '':
                                        RemoveStringLength = self.calcRemoveStringLength(cbTS)
                                    self.setCompositionBufferString(cbTS, CommitStr, RemoveStringLength)
                                    cbTS.compositionBufferType = "fullshape"
                                    self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, charStr, cbTS.compositionBufferCursor)
                                else:
                                    cbTS.setCommitString(CommitStr)
                                self.resetComposition(cbTS)
                    else: #如果是字母
                        if cbTS.shapeMode == FULLSHAPE_MODE: # 全形模式
                            CommitStr = self.charCodeToFullshape(cbTS, charCode, keyCode)
                        else:
                            if cbTS.outputSmallLetterWithShift:
                                CommitStr = charStr.upper() if cbTS.capsStates else charStr.lower()
                        if cbTS.compositionBufferMode:
                            RemoveStringLength = 0
                            if not cbTS.compositionChar == '':
                                RemoveStringLength = self.calcRemoveStringLength(cbTS)
                            self.setCompositionBufferString(cbTS, CommitStr, RemoveStringLength)
                            cbTS.compositionBufferType = "fullshape" if cbTS.shapeMode == FULLSHAPE_MODE else "english"
                            self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, charStr, cbTS.compositionBufferCursor)
                        else:
                            cbTS.setCommitString(CommitStr)
                        self.resetComposition(cbTS)
                else: # 如果未使用 SHIFT 輸入快速符號或全形標點
                    if cbTS.cin.isInKeyName(charStrLow) and (self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode)): # 如果是 CIN 所定義的字根
                        cbTS.compositionChar = charStrLow
                        keyname = cbTS.cin.getKeyName(charStrLow)
                        if cbTS.compositionBufferMode:
                            self.setCompositionBufferString(cbTS, keyname, 0)
                        else:
                            cbTS.setCompositionString(keyname)
                            cbTS.setCompositionCursor(len(cbTS.compositionString))
                    else:
                        if cbTS.shapeMode == FULLSHAPE_MODE: # 全形模式
                            # 如果是符號或數字，將字串轉為全形再輸出
                            if self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode):
                                CommitStr = self.SymbolscharCodeToFullshape(charCode)
                            else:
                                CommitStr = self.charCodeToFullshape(cbTS, charCode, keyCode)
                        else:
                            if self.isLetterChar(keyCode) and cbTS.outputSmallLetterWithShift:
                                CommitStr = charStr.upper() if cbTS.capsStates else charStr.lower()
                        if cbTS.compositionBufferMode and cbTS.isComposing():
                            RemoveStringLength = 0
                            if not cbTS.compositionChar == '':
                                RemoveStringLength = self.calcRemoveStringLength(cbTS)
                            self.setCompositionBufferString(cbTS, CommitStr, RemoveStringLength)
                            cbTS.compositionBufferType = "fullshape" if cbTS.shapeMode == FULLSHAPE_MODE else "english"
                            self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, charStr, cbTS.compositionBufferCursor)
                        else:
                            cbTS.setCommitString(CommitStr)
                        self.resetComposition(cbTS)
            else: # 若沒按下 Shift 鍵
                # 如果是英文全形模式，將字串轉為全形再輸出
                if cbTS.shapeMode == FULLSHAPE_MODE and cbTS.langMode == ENGLISH_MODE:
                    # 如果是符號或數字，將字串轉為全形再輸出
                    if self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode):
                        CommitStr = self.SymbolscharCodeToFullshape(charCode)
                    else:
                        CommitStr = self.charCodeToFullshape(cbTS, charCode, keyCode)
                    cbTS.setCommitString(CommitStr)
                    if cbTS.compositionBufferMode:
                        self.resetCompositionBuffer(cbTS)
                    self.resetComposition(cbTS)
                else: # 送出 CIN 所定義的字根
                    if not cbTS.directShowCand and cbTS.showCandidates and self.isInSelKeys(cbTS, charCode):
                        # 不送出 CIN 所定義的字根
                        cbTS.compositionChar = cbTS.compositionChar
                    elif cbTS.imeDirName == "chedayi" and cbTS.showCandidates and self.isInSelKeys(cbTS, charCode):
                        # 不送出 CIN 所定義的字根
                        cbTS.compositionChar = cbTS.compositionChar
                    else:
                        # 如果是注音輸入法
                        if cbTS.imeDirName == "chephonetic":
                            if not cbTS.keyboardLayout == 0 and not chr(charCode).lower() in cbTS.kbtypelist[cbTS.keyboardLayout]:
                                cbTS.compositionChar = cbTS.compositionChar
                            else:
                                if len(cbTS.compositionChar) > 0:
                                    cbTS.updateCompositionChar(charStrLow)
                                else:
                                    cbTS.compositionChar += charStrLow
                                    keyname = cbTS.cin.getKeyName(charStrLow)
                                    if cbTS.compositionBufferMode:
                                        self.setCompositionBufferString(cbTS, keyname, 0)
                                    else:
                                        cbTS.setCompositionString(cbTS.compositionString + keyname)
                                        cbTS.setCompositionCursor(len(cbTS.compositionString))
                        else:
                            if not cbTS.menusymbolsmode:
                                cbTS.compositionChar += charStrLow
                                keyname = cbTS.cin.getKeyName(charStrLow)
                                if cbTS.compositionBufferMode:
                                    if (len(cbTS.compositionChar) <= cbTS.maxCharLength):
                                        self.setCompositionBufferString(cbTS, keyname, 0)
                                    else:
                                        cbTS.compositionChar = cbTS.compositionChar[:-1]
                                else:
                                    cbTS.setCompositionString(cbTS.compositionString + keyname)
                                    cbTS.setCompositionCursor(len(cbTS.compositionString))
                            else:
                                cbTS.menusymbolsmode = False
        # 按下的鍵不存在於 CIN 所定義的字根
        elif not cbTS.cin.isInKeyName(charStrLow) and cbTS.closemenu and not cbTS.multifunctionmode and not keyEvent.isKeyDown(VK_CONTROL) and not cbTS.ctrlsymbolsmode and not cbTS.dayisymbolsmode and not cbTS.selcandmode and not cbTS.tempEnglishMode and not cbTS.phrasemode:
            # 若按下 Shift 鍵
            if keyEvent.isKeyDown(VK_SHIFT) and cbTS.langMode == CHINESE_MODE:
                # 如果按鍵及萬用字元為*
                if charStr == '*' and cbTS.supportWildcard and cbTS.selWildcardChar == charStr: 
                    keyname = '＊'
                    if cbTS.compositionBufferMode:
                        if (len(cbTS.compositionChar) < cbTS.maxCharLength):
                            cbTS.compositionChar += '*'
                            self.setCompositionBufferString(cbTS, keyname, 0)
                    else:
                        cbTS.compositionChar += '*'
                        cbTS.setCompositionString(cbTS.compositionString + keyname)
                # 如果停用 Shift 輸入全形標點
                elif not cbTS.fullShapeSymbols:
                    # 如果是全形模式，將字串轉為全形再輸出
                    if cbTS.shapeMode == FULLSHAPE_MODE:
                        # 如果是符號或數字，將字串轉為全形再輸出
                        if self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode):
                            CommitStr = self.SymbolscharCodeToFullshape(charCode)
                        else:
                            CommitStr = self.charCodeToFullshape(cbTS, charCode, keyCode)
                        if cbTS.compositionBufferMode:
                            RemoveStringLength = 0
                            if not cbTS.compositionChar == '':
                                RemoveStringLength = self.calcRemoveStringLength(cbTS)
                            self.setCompositionBufferString(cbTS, CommitStr, RemoveStringLength)
                            cbTS.compositionBufferType = "fullshape"
                            self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, charStr, cbTS.compositionBufferCursor)
                        else:
                            cbTS.setCommitString(CommitStr)
                        self.resetComposition(cbTS)
                    else: # 半形模式直接輸出不作處理
                        CommitStr = charStr
                        if self.isLetterChar(keyCode) and cbTS.outputSmallLetterWithShift:
                            CommitStr = charStr.upper() if cbTS.capsStates else charStr.lower()
                        if cbTS.compositionBufferMode:
                            RemoveStringLength = 0
                            if not cbTS.compositionChar == '':
                                RemoveStringLength = self.calcRemoveStringLength(cbTS)
                            self.setCompositionBufferString(cbTS, CommitStr, RemoveStringLength)
                            cbTS.compositionBufferType = "english"
                            self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, charStr, cbTS.compositionBufferCursor)
                        else:
                            cbTS.setCommitString(CommitStr)
                        self.resetComposition(cbTS)
                else: # 如果啟用 Shift 輸入全形標點
                    # 如果是符號或數字鍵，將字串轉為全形再輸出
                    if self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode):
                        # 如果該鍵有定義在 fsymbols
                        if cbTS.fsymbols.isInCharDef(charStr):
                            self.setOutputFSymbols(cbTS, charStr)
                        else: # 沒有定義在 fsymbols 裡
                            if self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode):
                                CommitStr = self.SymbolscharCodeToFullshape(charCode)
                            else:
                                CommitStr = self.charCodeToFullshape(cbTS, charCode, keyCode)
                            if cbTS.compositionBufferMode:
                                RemoveStringLength = 0
                                if not cbTS.compositionChar == '':
                                    RemoveStringLength = self.calcRemoveStringLength(cbTS)
                                self.setCompositionBufferString(cbTS, CommitStr, RemoveStringLength)
                                cbTS.compositionBufferType = "fullshape"
                                self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, charStr, cbTS.compositionBufferCursor)
                            else:
                                cbTS.setCommitString(CommitStr)
                            self.resetComposition(cbTS)
            else: # 若沒按下 Shift 鍵
                # 如果是全形模式，將字串轉為全形再輸出
                if cbTS.shapeMode == FULLSHAPE_MODE and len(cbTS.compositionChar) == 0:
                    if keyEvent.isPrintableChar():
                        if not(cbTS.phrasemode and (self.isNumberChar(keyCode) or keyCode == VK_SPACE)):
                            if self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode):
                                CommitStr = self.SymbolscharCodeToFullshape(charCode)
                            else:
                                CommitStr = self.charCodeToFullshape(cbTS, charCode, keyCode)

                            if not cbTS.compositionBufferMode:
                                cbTS.setCommitString(CommitStr)
                                self.resetComposition(cbTS)
                            else:
                                # 如果是英文全形模式，將字串轉為全形再輸出
                                if cbTS.langMode == ENGLISH_MODE:
                                    cbTS.setCommitString(CommitStr)
                                    self.resetCompositionBuffer(cbTS)
                                else:
                                    self.setCompositionBufferString(cbTS, CommitStr, 0)
                                    cbTS.compositionBufferType = "fullshape"
                                    self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, charStr, cbTS.compositionBufferCursor)
                                self.resetComposition(cbTS)
                else: # 半形模式
                    if cbTS.compositionBufferMode:
                        if cbTS.isComposing() and keyEvent.isPrintableChar() and not cbTS.showCandidates and cbTS.compositionChar == '':
                            self.setCompositionBufferString(cbTS, charStr, 0)
                            cbTS.compositionBufferType = "english"
                            self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, charStr, cbTS.compositionBufferCursor)
                            self.resetComposition(cbTS)

        if cbTS.langMode == CHINESE_MODE and len(cbTS.compositionChar) >= 1 and not cbTS.menumode and not cbTS.multifunctionmode:
            cbTS.showmenu = False
            if not cbTS.directShowCand and not cbTS.selcandmode:
                if not cbTS.lastCompositionCharLength == len(cbTS.compositionChar):
                    cbTS.lastCompositionCharLength = len(cbTS.compositionChar)
                    cbTS.isShowCandidates = False
                    cbTS.setShowCandidates(False)

            # 按下 ESC 鍵
            if keyCode == VK_ESCAPE and (cbTS.showCandidates or len(cbTS.compositionChar) > 0):
                cbTS.lastCompositionCharLength = 0
                if not cbTS.directShowCand:
                    cbTS.isShowCandidates = False
                if cbTS.compositionBufferMode:
                    if cbTS.compositionChar != "":
                        if not cbTS.selcandmode:
                            keyLength = self.calcRemoveStringLength(cbTS)
                            self.removeCompositionBufferString(cbTS, keyLength, True)
                        self.resetComposition(cbTS)
                        cbTS.keyUsedState = True
                else:
                    self.resetComposition(cbTS)

            # 刪掉一個字根
            if keyCode == VK_BACK:
                if cbTS.homophoneQuery and cbTS.homophonemode:
                    self.resetHomophoneMode(cbTS)

                if not cbTS.compositionBufferMode:
                    if cbTS.compositionString != "":
                        if cbTS.cin.isInKeyName(cbTS.compositionChar[len(cbTS.compositionChar)-1:]):
                            keyLength = len(cbTS.cin.getKeyName(cbTS.compositionChar[len(cbTS.compositionChar)-1:]))
                        else:
                            keyLength = 1
                        cbTS.setCompositionString(cbTS.compositionString[:-keyLength])
                        cbTS.keyUsedState = True
                else:
                    if cbTS.compositionBufferString != "" and cbTS.compositionChar != "":
                        if not cbTS.selcandmode:
                            if cbTS.cin.isInKeyName(cbTS.compositionChar[len(cbTS.compositionChar)-1:]):
                                keyLength = len(cbTS.cin.getKeyName(cbTS.compositionChar[len(cbTS.compositionChar)-1:]))
                            else:
                                keyLength = 1
                            self.removeCompositionBufferString(cbTS, keyLength, True)
                            cbTS.keyUsedState = True

                if cbTS.keyUsedState:
                    cbTS.compositionChar = cbTS.compositionChar[:-1]
                    cbTS.lastCompositionCharLength = cbTS.lastCompositionCharLength - 1
                    cbTS.setCandidateCursor(0)
                    cbTS.setCandidatePage(0)
                    cbTS.wildcardcandidates = []
                    cbTS.wildcardpagecandidates = []
                    if not cbTS.directShowCand:
                        cbTS.isShowCandidates = False
                        cbTS.setShowCandidates(False)
                    if cbTS.compositionChar == '':
                        self.resetComposition(cbTS)

            # 組字字根超過最大值
            if len(cbTS.compositionChar) > cbTS.maxCharLength:
                if cbTS.cin.isInKeyName(cbTS.compositionChar[len(cbTS.compositionChar)-1:]):
                    keyLength = len(cbTS.cin.getKeyName(cbTS.compositionChar[len(cbTS.compositionChar)-1:]))
                else:
                    keyLength = 1
                if cbTS.compositionBufferMode:
                    self.removeCompositionBufferString(cbTS, keyLength, False)
                else:
                    cbTS.setCompositionString(cbTS.compositionString[:-keyLength])
                cbTS.compositionChar = cbTS.compositionChar[:-1]

            if cbTS.homophoneQuery and cbTS.homophonemode and cbTS.homophoneChar == cbTS.compositionChar:
                candidates = cbTS.homophonecandidates
            elif cbTS.cin.isInCharDef(cbTS.compositionChar) and cbTS.closemenu and not cbTS.ctrlsymbolsmode and not cbTS.dayisymbolsmode:
                candidates = cbTS.cin.getCharDef(cbTS.compositionChar)
                if cbTS.sortByPhrase and candidates:
                    candidates = self.sortByPhrase(cbTS, copy.deepcopy(candidates))
                if cbTS.compositionBufferMode and not cbTS.selcandmode:
                    cbTS.compositionBufferType = "default"
            elif cbTS.imeDirName == "chepinyin" and cbTS.cinFileList[cbTS.cfg.selCinType] == "thpinyin.cin" and not cbTS.ctrlsymbolsmode:
                if cbTS.cin.isInCharDef(cbTS.compositionChar + "1") and cbTS.closemenu and not cbTS.ctrlsymbolsmode:
                    candidates = cbTS.cin.getCharDef(cbTS.compositionChar + '1')
                    if cbTS.sortByPhrase and candidates:
                        candidates = self.sortByPhrase(cbTS, copy.deepcopy(candidates))
                    if cbTS.compositionBufferMode and not cbTS.selcandmode:
                        cbTS.compositionBufferType = "default"
            elif cbTS.fullShapeSymbols and cbTS.fsymbols.isInCharDef(cbTS.compositionChar) and cbTS.closemenu:
                candidates = cbTS.fsymbols.getCharDef(cbTS.compositionChar)
                if cbTS.compositionBufferMode and not cbTS.selcandmode:
                    cbTS.compositionBufferType = "fsymbols"
            elif cbTS.msymbols.isInCharDef(cbTS.compositionChar) and cbTS.closemenu and cbTS.ctrlsymbolsmode:
                candidates = cbTS.msymbols.getCharDef(cbTS.compositionChar)
                if cbTS.compositionBufferMode and not cbTS.selcandmode:
                    cbTS.compositionBufferType = "msymbols"
            elif cbTS.dayisymbolsmode and cbTS.closemenu:
                if cbTS.dsymbols.isInCharDef(cbTS.compositionChar[1:]):
                    candidates = cbTS.dsymbols.getCharDef(cbTS.compositionChar[1:])
                    if cbTS.compositionBufferMode and not cbTS.selcandmode:
                        self.setCompositionBufferString(cbTS, candidates[0], 1)
                        cbTS.compositionBufferType = "dayisymbols"
                    else:
                        cbTS.setCompositionString(candidates[0])
            elif cbTS.supportWildcard and cbTS.selWildcardChar in cbTS.compositionChar and cbTS.closemenu:
                if cbTS.wildcardcandidates and cbTS.wildcardcompositionChar == cbTS.compositionChar:
                    candidates = cbTS.wildcardcandidates
                else:
                    cbTS.setCandidateCursor(0)
                    cbTS.setCandidatePage(0)
                    cbTS.wildcardcandidates = cbTS.cin.getWildcardCharDefs(cbTS.compositionChar, cbTS.selWildcardChar, cbTS.candMaxItems)
                    if cbTS.imeDirName == "chepinyin" and cbTS.cinFileList[cbTS.cfg.selCinType] == "thpinyin.cin":
                        if not cbTS.wildcardcandidates:
                            cbTS.wildcardcandidates = cbTS.cin.getWildcardCharDefs(cbTS.compositionChar + "1", cbTS.selWildcardChar, cbTS.candMaxItems)
                    cbTS.wildcardpagecandidates = []
                    cbTS.wildcardcompositionChar = cbTS.compositionChar
                    candidates = cbTS.wildcardcandidates
                    if cbTS.compositionBufferMode and not cbTS.selcandmode:
                        cbTS.compositionBufferType = "default"
                cbTS.isWildcardChardefs = True
                if cbTS.sortByPhrase and candidates:
                    candidates = self.sortByPhrase(cbTS, copy.deepcopy(candidates))

        # 組字編輯模式
        if cbTS.compositionBufferMode and cbTS.isComposing() and cbTS.compositionChar == "" and cbTS.closemenu and not cbTS.multifunctionmode and not cbTS.phrasemode and not cbTS.selcandmode:
            changelastCommitString = False
            if keyCode == VK_LEFT:
                if cbTS.compositionBufferCursor > 0:
                    cbTS.compositionBufferCursor -= 1
                    cbTS.setCompositionCursor(cbTS.compositionBufferCursor)
                    changelastCommitString = True
            elif keyCode == VK_RIGHT:
                if cbTS.compositionBufferCursor < len(cbTS.compositionBufferString):
                    cbTS.compositionBufferCursor += 1
                    cbTS.setCompositionCursor(cbTS.compositionBufferCursor)
                    changelastCommitString = True
            elif keyCode == VK_HOME:
                cbTS.compositionBufferCursor = 0
                cbTS.setCompositionCursor(cbTS.compositionBufferCursor)
                changelastCommitString = True
            elif keyCode == VK_END:
                cbTS.compositionBufferCursor = len(cbTS.compositionBufferString)
                cbTS.setCompositionCursor(cbTS.compositionBufferCursor)
                changelastCommitString = True
            elif keyCode == VK_BACK:
                if cbTS.compositionBufferCursor != 0 and cbTS.compositionBufferString != "" and not cbTS.keyUsedState:
                    if cbTS.compositionBufferCursor - 1 in cbTS.compositionBufferChar:
                        del cbTS.compositionBufferChar[cbTS.compositionBufferCursor - 1]
                    for key in cbTS.compositionBufferChar:
                        if key > cbTS.compositionBufferCursor - 1:
                            cbTS.compositionBufferChar[key - 1] = cbTS.compositionBufferChar.pop(key)
                    self.removeCompositionBufferString(cbTS, 1, True)
                    changelastCommitString = True
                if cbTS.compositionBufferString == '':
                    cbTS.compositionBufferChar = {}
                    self.resetComposition(cbTS)
                    self.resetCompositionBuffer(cbTS)
                    cbTS.tempEnglishMode = False
            elif keyCode == VK_DELETE:
                if cbTS.compositionBufferCursor != len(cbTS.compositionBufferString) and cbTS.compositionBufferString != "":
                    if cbTS.compositionBufferCursor in cbTS.compositionBufferChar:
                        del cbTS.compositionBufferChar[cbTS.compositionBufferCursor]
                    for key in cbTS.compositionBufferChar:
                        if key > cbTS.compositionBufferCursor:
                            cbTS.compositionBufferChar[key - 1] = cbTS.compositionBufferChar.pop(key)
                    self.removeCompositionBufferString(cbTS, 1, False)
                    changelastCommitString = True
                if cbTS.compositionBufferString == '':
                    cbTS.compositionBufferChar = {}
                    self.resetComposition(cbTS)
                    self.resetCompositionBuffer(cbTS)
                    cbTS.tempEnglishMode = False
            elif keyCode == VK_ESCAPE and not cbTS.keyUsedState:
                self.resetComposition(cbTS)
                self.resetCompositionBuffer(cbTS)
                cbTS.compositionBufferChar = {}
                cbTS.tempEnglishMode = False
            elif keyCode == VK_RETURN:
                cbTS.setCommitString(cbTS.compositionBufferString)
                self.resetComposition(cbTS)
                self.resetCompositionBuffer(cbTS)
                cbTS.compositionBufferChar = {}
                cbTS.tempEnglishMode = False
            elif keyCode == VK_DOWN:
                cbTS.tempengcandidates = []
                selStringPos = cbTS.compositionBufferCursor if cbTS.compositionBufferCursor <= len(cbTS.compositionBufferString) - 1 else cbTS.compositionBufferCursor - 1

                if selStringPos in cbTS.compositionBufferChar:
                    sellist = cbTS.compositionBufferChar[selStringPos]
                    if sellist[0] == 'msymbols':
                        cbTS.compositionChar = sellist[1] if sellist[1][0] != "`" else sellist[1][1:]
                        candidates = cbTS.msymbols.getCharDef(cbTS.compositionChar)
                        cbTS.selcandmode = True
                    elif sellist[0] == 'dayisymbols':
                        cbTS.compositionChar = sellist[1]
                        candidates = cbTS.dsymbols.getCharDef(sellist[1][1:])
                        cbTS.selcandmode = True
                    elif sellist[0] == 'fsymbols':
                        cbTS.compositionChar = 'none'
                        candidates = cbTS.fsymbols.getCharDef(sellist[1])
                        cbTS.selcandmode = True
                    elif sellist[0] == 'menusymbols':
                        cbTS.compositionChar = 'none'
                        candidates = cbTS.symbols.getCharDef(sellist[1])
                        cbTS.selcandmode = True
                    elif sellist[0] == 'menubopomofo':
                        cbTS.compositionChar = 'none'
                        candidates = cbTS.bopomofolist
                        cbTS.selcandmode = True
                    elif sellist[0] == 'menuflangs':
                        cbTS.compositionChar = 'none'
                        candidates = cbTS.flangs.getCharDef(sellist[1])
                        cbTS.selcandmode = True
                    elif sellist[0] == 'menuemoji':
                        cbTS.compositionChar = 'none'
                        elist = sellist[1].split(',', 2)
                        candidates = self.emoji.getCharDef(elist[0], elist[1])
                        cbTS.selcandmode = True
                    elif sellist[0] == 'default':
                        if cbTS.cin.isInCharDef(sellist[1]):
                            cbTS.compositionChar = sellist[1]
                            candidates = cbTS.cin.getCharDef(sellist[1])
                            if cbTS.sortByPhrase and candidates:
                                candidates = self.sortByPhrase(cbTS, copy.deepcopy(candidates))
                            cbTS.selcandmode = True
                    else:
                        if cbTS.cin.isHaveKey(cbTS.compositionBufferString[cbTS.compositionBufferCursor]):
                            cbTS.compositionChar = cbTS.cin.getKey(cbTS.compositionBufferString[cbTS.compositionBufferCursor])
                            candidates = cbTS.cin.getCharDef(cbTS.compositionChar)
                            if cbTS.sortByPhrase and candidates:
                                candidates = self.sortByPhrase(cbTS, copy.deepcopy(candidates))
                            cbTS.selcandmode = True
                        else:
                            cbTS.selcandmode = False
                            cbTS.isShowMessage = True
                            cbTS.showMessage("沒有候選字...", cbTS.messageDurationTime)

                    if cbTS.selcandmode:
                        cbTS.isShowCandidates = True
                        cbTS.canSetCommitString = False
                        cbTS.tempengcandidates = copy.deepcopy(candidates)

            if changelastCommitString and cbTS.compositionBufferString != '':
                if cbTS.compositionBufferCursor > 0:
                    cbTS.lastCommitString = cbTS.compositionBufferString[cbTS.compositionBufferCursor - 1]

        if cbTS.selcandmode and cbTS.compositionChar != '':
            candidates = cbTS.tempengcandidates

        # 候選清單處理
        if (cbTS.langMode == CHINESE_MODE and len(cbTS.compositionChar) >= 1 and not cbTS.menumode) or (cbTS.tempEnglishMode and cbTS.isComposing()):
            # 如果字根首字是符號就直接輸出
            if cbTS.directCommitSymbol and not cbTS.tempEnglishMode and not cbTS.phrasemode and not cbTS.selcandmode:
                # 如果是全形標點
                if cbTS.fullShapeSymbols and cbTS.fullsymbolsmode:
                    if len(cbTS.compositionChar) >= 2 and cbTS.fsymbols.isInCharDef(cbTS.compositionChar[0]):
                        cbTS.fullsymbolsmode = False
                        if not cbTS.cin.isInCharDef(cbTS.compositionChar):
                            if cbTS.compositionBufferMode:
                                self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, cbTS.compositionChar[0], cbTS.compositionBufferCursor - 1)
                                cbTS.compositionChar = cbTS.compositionChar[1:]
                            else:
                                cbTS.keepComposition = True
                                commitStr = cbTS.compositionString[:1]
                                compositionStr = cbTS.compositionString[1:]
                                compositionChar = cbTS.compositionChar[1:]
                                cbTS.setCommitString(commitStr)
                                cbTS.compositionChar = compositionChar
                                cbTS.setCompositionString(compositionStr)
                                cbTS.setCompositionCursor(len(cbTS.compositionString))
                            if cbTS.cin.isInCharDef(cbTS.compositionChar):
                                candidates = cbTS.cin.getCharDef(cbTS.compositionChar)
                                if cbTS.sortByPhrase and candidates:
                                    candidates = self.sortByPhrase(cbTS, copy.deepcopy(candidates))
                # 如果是碼表標點
                if cbTS.cin.isInKeyName(cbTS.compositionChar[0]):
                    if cbTS.cin.getKeyName(cbTS.compositionChar[0]) in cbTS.directCommitSymbolList:
                        if not cbTS.cin.isInCharDef(cbTS.compositionChar):
                            if cbTS.compositionBufferMode:
                                cursorPos = cbTS.compositionBufferCursor
                                if cbTS.cin.isInCharDef(cbTS.compositionChar[:-1]):
                                    cursorPos = cbTS.compositionBufferCursor - len(cbTS.compositionChar[:-1])
                                cbTS.compositionBufferType = "default"
                                self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, cbTS.compositionChar[0], cursorPos)
                                cbTS.compositionChar = cbTS.compositionChar[1:]
                            else:
                                if len(cbTS.compositionChar) >= 2 and not cbTS.cin.getKeyName(cbTS.compositionChar[1]) in cbTS.directCommitSymbolList:
                                    cbTS.keepComposition = True
                                    commitStr = cbTS.cin.getKeyName(cbTS.compositionChar[:1])
                                    compositionStr = cbTS.compositionString[1:]
                                    compositionChar = cbTS.compositionChar[1:]
                                    cbTS.setCommitString(commitStr)
                                    cbTS.compositionChar = compositionChar
                                    cbTS.setCompositionString(compositionStr)
                                    cbTS.setCompositionCursor(len(cbTS.compositionString))
                            if cbTS.cin.isInCharDef(cbTS.compositionChar):
                                candidates = cbTS.cin.getCharDef(cbTS.compositionChar)
                                if cbTS.sortByPhrase and candidates:
                                    candidates = self.sortByPhrase(cbTS, copy.deepcopy(candidates))

            if cbTS.langMode == CHINESE_MODE and cbTS.dayisymbolsmode and len(cbTS.compositionChar) == 1 and (keyCode == VK_SPACE or keyCode == VK_RETURN):
                candidates = cbTS.cin.getCharDef(cbTS.compositionChar)
                if cbTS.compositionBufferMode and cbTS.directShowCand:
                    self.removeCompositionBufferString(cbTS, 1, True)

            if candidates and not cbTS.phrasemode:
                if not cbTS.selcandmode:
                    if not cbTS.directShowCand:
                        # EndKey 處理 (拼音、注音)
                        if cbTS.useEndKey:
                            if charStr in cbTS.endKeyList:
                                if not cbTS.isShowCandidates:
                                    if cbTS.compositionBufferMode:
                                        commitStr = candidates[0]
                                        cbTS.lastCommitString = commitStr
                                        self.setOutputString(cbTS, RCinTable, commitStr)
                                        if cbTS.showPhrase and not cbTS.selcandmode:
                                            cbTS.phrasemode = True
                                        self.resetComposition(cbTS)
                                        candCursor = 0
                                        currentCandPage = 0
                                        cbTS.canSetCommitString = True
                                        cbTS.isShowCandidates = False
                                    else:
                                        cbTS.isShowCandidates = True
                                        cbTS.canUseSelKey = False
                                else:
                                    cbTS.canUseSelKey = True
                            else:
                                if cbTS.isShowCandidates:
                                    cbTS.canUseSelKey = True

                        # 字滿及符號處理 (大易、注音、輕鬆)
                        if cbTS.autoShowCandWhenMaxChar or cbTS.dayisymbolsmode:
                            if len(cbTS.compositionChar) == cbTS.maxCharLength or cbTS.dayisymbolsmode:
                                if len(candidates) == 1 and cbTS.directCommitString:
                                    commitStr = candidates[0]
                                    cbTS.lastCommitString = commitStr

                                    # 如果使用萬用字元解碼
                                    if cbTS.isWildcardChardefs:
                                        cbTS.isShowMessage = True
                                        cbTS.showMessageOnKeyUp = True
                                        cbTS.onKeyUpMessage = cbTS.cin.getCharEncode(commitStr)
                                        cbTS.wildcardcandidates = []
                                        cbTS.wildcardpagecandidates = []
                                        cbTS.isWildcardChardefs = False

                                    if cbTS.imeReverseLookup:
                                        if RCinTable.cin is not None:
                                            if not RCinTable.cin.getCharEncode(commitStr) == "":
                                                cbTS.isShowMessage = True
                                                cbTS.showMessageOnKeyUp = True
                                                cbTS.onKeyUpMessage = RCinTable.cin.getCharEncode(commitStr)
                                        else:
                                            cbTS.isShowMessage = True
                                            cbTS.showMessageOnKeyUp = True
                                            cbTS.onKeyUpMessage = "反查字根碼表尚在載入中！"

                                    # 如果使用打繁出簡，就轉成簡體中文
                                    if cbTS.outputSimpChinese:
                                        commitStr = cbTS.opencc.convert(commitStr)

                                    if cbTS.compositionBufferMode:
                                        self.setCompositionBufferString(cbTS, commitStr, 0)
                                    else:
                                        cbTS.setCommitString(commitStr)

                                    if cbTS.showPhrase:
                                        cbTS.phrasemode = True

                                    self.resetComposition(cbTS)
                                    candCursor = 0
                                    currentCandPage = 0
                                    cbTS.isShowCandidates = False
                                    cbTS.canSetCommitString = True
                                else:
                                    if not cbTS.isShowCandidates:
                                        if cbTS.compositionBufferMode:
                                            if cbTS.dayisymbolsmode and not len(cbTS.compositionChar) == 1:
                                                commitStr = candidates[0]
                                                cbTS.lastCommitString = commitStr

                                                self.setOutputString(cbTS, RCinTable, commitStr)
                                                if cbTS.showPhrase and not cbTS.selcandmode:
                                                    cbTS.phrasemode = True
                                                self.resetComposition(cbTS)
                                                candCursor = 0
                                                currentCandPage = 0
                                                cbTS.canSetCommitString = True
                                                cbTS.isShowCandidates = False
                                        else:
                                            cbTS.isShowCandidates = True
                                            cbTS.canUseSelKey = False
                                    else:
                                        if not cbTS.imeDirName == "chephonetic":
                                            cbTS.canUseSelKey = True
                            else:
                                if cbTS.isShowCandidates:
                                    if not cbTS.imeDirName == "chephonetic":
                                        cbTS.canUseSelKey = True

                        if (keyCode == VK_SPACE or keyCode == VK_DOWN) and not cbTS.isShowCandidates:  # 按下空白鍵和向下鍵
                            # 如果只有一個候選字就直接出字或組字編輯模式未啟用直接顯示候選清單
                            if (len(candidates) == 1 and cbTS.directCommitString) or (cbTS.compositionBufferMode and not cbTS.directShowCand):
                                if keyCode == VK_SPACE:
                                    commitStr = candidates[0]
                                    cbTS.lastCommitString = commitStr
                                    cbTS.canUseSpaceAsPageKey = False

                                    # 如果使用萬用字元解碼
                                    if cbTS.isWildcardChardefs:
                                        cbTS.isShowMessage = True
                                        cbTS.showMessageOnKeyUp = True
                                        cbTS.onKeyUpMessage = cbTS.cin.getCharEncode(commitStr)
                                        cbTS.wildcardcandidates = []
                                        cbTS.wildcardpagecandidates = []
                                        cbTS.isWildcardChardefs = False

                                    if cbTS.imeReverseLookup:
                                        if RCinTable.cin is not None:
                                            if not RCinTable.cin.getCharEncode(commitStr) == "":
                                                cbTS.isShowMessage = True
                                                cbTS.showMessageOnKeyUp = True
                                                cbTS.onKeyUpMessage = RCinTable.cin.getCharEncode(commitStr)
                                        else:
                                            cbTS.isShowMessage = True
                                            cbTS.showMessageOnKeyUp = True
                                            cbTS.onKeyUpMessage = "反查字根碼表尚在載入中！"

                                    # 如果使用打繁出簡，就轉成簡體中文
                                    if cbTS.outputSimpChinese:
                                        commitStr = cbTS.opencc.convert(commitStr)

                                    if cbTS.compositionBufferMode:
                                        RemoveStringLength = 0
                                        if not cbTS.menusymbolsmode:
                                            for char in cbTS.compositionChar:
                                                if cbTS.cin.isInKeyName(char):
                                                    RemoveStringLength += len(cbTS.cin.getKeyName(char))
                                                else:
                                                    RemoveStringLength += 1
                                        else:
                                            RemoveStringLength = len(cbTS.compositionChar) - 1
                                            cbTS.menusymbolsmode = False
                                        self.setCompositionBufferString(cbTS, commitStr, RemoveStringLength)
                                        self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, cbTS.compositionChar, cbTS.compositionBufferCursor)
                                    else:
                                        cbTS.setCommitString(commitStr)

                                    if cbTS.showPhrase:
                                        cbTS.phrasemode = True
                                    self.resetComposition(cbTS)
                                    candCursor = 0
                                    currentCandPage = 0
                                    cbTS.isShowCandidates = False
                                    cbTS.canSetCommitString = True
                                else:
                                    cbTS.isShowCandidates = True
                                    cbTS.canSetCommitString = False
                            else:
                                cbTS.isShowCandidates = True
                                cbTS.canSetCommitString = False
                                if keyCode == VK_SPACE:
                                    cbTS.canUseSpaceAsPageKey = False
                    else:
                        cbTS.isShowCandidates = True
                        cbTS.canSetCommitString = True

                if cbTS.isShowCandidates:
                    candCursor = cbTS.candidateCursor  # 目前的游標位置
                    candCount = len(cbTS.candidateList)  # 目前選字清單項目數
                    currentCandPageCount = math.ceil(len(candidates) / cbTS.candPerPage) # 目前的選字清單總頁數
                    currentCandPage = cbTS.currentCandPage # 目前的選字清單頁數

                    # 候選清單分頁
                    if cbTS.isWildcardChardefs:
                        if cbTS.wildcardpagecandidates:
                            pagecandidates = cbTS.wildcardpagecandidates
                        else:
                            cbTS.wildcardpagecandidates = list(self.chunks(candidates, cbTS.candPerPage))
                            pagecandidates = cbTS.wildcardpagecandidates
                    else:
                        pagecandidates = list(self.chunks(candidates, cbTS.candPerPage))
                    cbTS.setCandidateList(pagecandidates[currentCandPage])
                    if not cbTS.isSelKeysChanged:
                        cbTS.setShowCandidates(True)

                # 多功能前導字元
                if cbTS.multifunctionmode and cbTS.directCommitSymbol and not cbTS.selcandmode:
                    if len(candidates) == 1:
                        cand = candidates[0]
                        if cbTS.compositionBufferMode:
                            self.setCompositionBufferString(cbTS, cand, 0)
                        else:
                            cbTS.setCommitString(cand)
                        self.resetComposition(cbTS)
                        candCursor = 0
                        currentCandPage = 0

                if cbTS.isShowCandidates:
                    # 使用選字鍵執行項目或輸出候選字
                    if self.isInSelKeys(cbTS, charCode) and not keyEvent.isKeyDown(VK_SHIFT) and cbTS.canUseSelKey:
                        if not cbTS.homophoneselpinyinmode:
                            if cbTS.imeDirName == "chedayi":
                                i = cbTS.selKeys.index(charStr) + 1
                            else:
                                i = cbTS.selKeys.index(charStr)
                            if i < cbTS.candPerPage and i < len(cbTS.candidateList):
                                commitStr = cbTS.candidateList[i]
                                cbTS.lastCommitString = commitStr
                                self.setOutputString(cbTS, RCinTable, commitStr)
                                if cbTS.showPhrase and not cbTS.selcandmode:
                                    cbTS.phrasemode = True
                                self.resetComposition(cbTS)
                                candCursor = 0
                                currentCandPage = 0

                                if not cbTS.directShowCand:
                                    cbTS.canSetCommitString = True
                                    cbTS.isShowCandidates = False
                        else:
                            candCursor = 0
                            currentCandPage = 0
                            i = cbTS.selKeys.index(charStr)
                            cbTS.homophoneselpinyinmode = False
                            cbTS.homophonemode = True
                            cbTS.homophoneChar = cbTS.compositionChar
                            cbTS.isHomophoneChardefs = True
                            cbTS.homophonecandidates = HCinTable.cin.getCharDef(HCinTable.cin.getKeyList(cbTS.homophoneStr)[i])
                            pagecandidates = list(self.chunks(cbTS.homophonecandidates, cbTS.candPerPage))
                            cbTS.setCandidateList(pagecandidates[currentCandPage])
                    elif keyCode == VK_UP:  # 游標上移
                        if (candCursor - cbTS.candPerRow) < 0:
                            if currentCandPage > 0:
                                currentCandPage -= 1
                                candCursor = 0
                        else:
                            if (candCursor - cbTS.candPerRow) >= 0:
                                candCursor = candCursor - cbTS.candPerRow
                    elif keyCode == VK_DOWN and cbTS.canSetCommitString:  # 游標下移
                        if (candCursor + cbTS.candPerRow) >= cbTS.candPerPage:
                            if (currentCandPage + 1) < currentCandPageCount:
                                currentCandPage += 1
                                candCursor = 0
                        else:
                            if (candCursor + cbTS.candPerRow) < len(pagecandidates[currentCandPage]):
                                candCursor = candCursor + cbTS.candPerRow
                    elif keyCode == VK_LEFT:  # 游標左移
                        if candCursor > 0:
                            candCursor -= 1
                        else:
                            if currentCandPage > 0:
                                currentCandPage -= 1
                                candCursor = 0
                    elif keyCode == VK_RIGHT:  # 游標右移
                        if (candCursor + 1) < candCount:
                            candCursor += 1
                        else:
                            if (currentCandPage + 1) < currentCandPageCount:
                                currentCandPage += 1
                                candCursor = 0
                    elif keyCode == VK_HOME:  # Home 鍵
                        candCursor = 0
                    elif keyCode == VK_END:  # End 鍵
                        candCursor = len(pagecandidates[currentCandPage]) - 1
                    elif keyCode == VK_PRIOR:  # Page UP 鍵
                        if currentCandPage > 0:
                            currentCandPage -= 1
                            candCursor = 0
                    elif keyCode == VK_NEXT:  # Page Down 鍵
                        if (currentCandPage + 1) < currentCandPageCount:
                            currentCandPage += 1
                            candCursor = 0
                    elif cbTS.homophoneQuery and not cbTS.homophonemode and not cbTS.multifunctionmode and not cbTS.fullsymbolsmode and keyCode == VK_OEM_3: # 同音字查詢啟用下按下`鍵
                        if HCinTable.cin is not None:
                            commitStr = cbTS.candidateList[candCursor]
                            if HCinTable.cin.isHaveKey(commitStr):
                                candCursor = 0
                                currentCandPage = 0
                                if len(HCinTable.cin.getKeyList(commitStr)) > 1:
                                    cbTS.homophonemode = True
                                    cbTS.homophoneselpinyinmode = True
                                    cbTS.homophoneChar = cbTS.compositionChar
                                    cbTS.homophoneStr = commitStr
                                    cbTS.homophonecandidates = HCinTable.cin.getKeyNameList(HCinTable.cin.getKeyList(commitStr))
                                    pagecandidates = list(self.chunks(cbTS.homophonecandidates, cbTS.candPerPage))
                                    cbTS.setCandidateList(pagecandidates[currentCandPage])
                                else:
                                    cbTS.homophonemode = True
                                    cbTS.homophoneChar = cbTS.compositionChar
                                    cbTS.isHomophoneChardefs = True
                                    cbTS.homophonecandidates = HCinTable.cin.getCharDef(HCinTable.cin.getKey(commitStr))
                                    pagecandidates = list(self.chunks(cbTS.homophonecandidates, cbTS.candPerPage))
                                    cbTS.setCandidateList(pagecandidates[currentCandPage])
                    elif (keyCode == VK_RETURN or (keyCode == VK_SPACE and not cbTS.switchPageWithSpace)) and cbTS.canSetCommitString:  # 按下 Enter 鍵或空白鍵
                        if not cbTS.homophoneselpinyinmode:
                            # 找出目前游標位置的選字鍵 (1234..., asdf...等等)
                            commitStr = cbTS.candidateList[candCursor]
                            cbTS.lastCommitString = commitStr
                            self.setOutputString(cbTS, RCinTable, commitStr)
                            if cbTS.showPhrase and not cbTS.selcandmode:
                                cbTS.phrasemode = True
                                if keyCode == VK_SPACE:
                                    cbTS.canUseSpaceAsPageKey = False
                            self.resetComposition(cbTS)
                            candCursor = 0
                            currentCandPage = 0

                            if not cbTS.directShowCand:
                                cbTS.isShowCandidates = False
                        else:
                            cbTS.homophoneselpinyinmode = False
                            cbTS.homophonemode = True
                            cbTS.homophoneChar = cbTS.compositionChar
                            cbTS.isHomophoneChardefs = True
                            cbTS.homophonecandidates = HCinTable.cin.getCharDef(HCinTable.cin.getKeyList(cbTS.homophoneStr)[candCursor])
                            candCursor = 0
                            currentCandPage = 0
                            pagecandidates = list(self.chunks(cbTS.homophonecandidates, cbTS.candPerPage))
                            cbTS.setCandidateList(pagecandidates[currentCandPage])
                    elif keyCode == VK_SPACE and cbTS.switchPageWithSpace: # 按下空白鍵
                        if cbTS.canUseSpaceAsPageKey:
                            if (currentCandPage + 1) < currentCandPageCount:
                                currentCandPage += 1
                                candCursor = 0
                            else:
                                currentCandPage = 0
                                candCursor = 0
                    else: # 按下其它鍵，先將候選字游標位址及目前頁數歸零
                        if not cbTS.ctrlsymbolsmode:
                            candCursor = 0
                            currentCandPage = 0
                    # 更新選字視窗游標位置及頁數
                    cbTS.setCandidateCursor(candCursor)
                    cbTS.setCandidatePage(currentCandPage)
                    cbTS.setCandidateList(pagecandidates[currentCandPage])
            else: # 沒有候選字
                # 按下空白鍵或 Enter 鍵
                if (keyCode == VK_SPACE or keyCode == VK_RETURN) and not cbTS.tempEnglishMode:
                    if len(candidates) == 0:
                        if cbTS.multifunctionmode:
                            if cbTS.compositionChar == '`':
                                if cbTS.compositionBufferMode:
                                    cbTS.compositionBufferType = "english"
                                    self.setCompositionBufferString(cbTS, cbTS.compositionChar, 1)
                                    self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, cbTS.compositionChar, cbTS.compositionBufferCursor)
                                else:
                                    cbTS.setCommitString(cbTS.compositionChar)
                                self.resetComposition(cbTS)
                            else:
                                if cbTS.compositionChar[:2] == '`U':
                                    if len(cbTS.compositionChar) > 2:
                                        commitStr = chr(int(cbTS.compositionChar[2:], 16))
                                        cbTS.lastCommitString = commitStr
                                        cbTS.isShowMessage = True
                                        cbTS.showMessageOnKeyUp = True
                                        cbTS.onKeyUpMessage = cbTS.cin.getCharEncode(commitStr)

                                        if cbTS.compositionBufferMode:
                                            cbTS.compositionBufferType = "menuunicode"
                                            self.setCompositionBufferString(cbTS, commitStr, len(cbTS.compositionChar))
                                            self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, cbTS.compositionChar[2:], cbTS.compositionBufferCursor)
                                        else:
                                            cbTS.setCommitString(commitStr)

                                        if cbTS.showPhrase:
                                            cbTS.phrasemode = True
                                        self.resetComposition(cbTS)
                                    else:
                                        cbTS.isShowMessage = True
                                        cbTS.showMessage("請輸入 Unicode 編碼...", cbTS.messageDurationTime)
                        else:
                            cbTS.isShowMessage = True
                            cbTS.showMessage("查無組字...", cbTS.messageDurationTime)
                            if cbTS.autoClearCompositionChar:
                                if cbTS.compositionBufferMode:
                                    RemoveStringLength = 0
                                    if not cbTS.compositionChar == '':
                                        RemoveStringLength = self.calcRemoveStringLength(cbTS)
                                    self.removeCompositionBufferString(cbTS, RemoveStringLength, True)
                                self.resetComposition(cbTS)
                            if cbTS.playSoundWhenNonCand:
                                winsound.PlaySound('alert', winsound.SND_ASYNC)
                elif cbTS.useEndKey and charStr in cbTS.endKeyList:
                    if len(candidates) == 0:
                        if not len(cbTS.compositionChar) == 1 and not cbTS.compositionChar == charStrLow:
                            cbTS.isShowMessage = True
                            cbTS.showMessage("查無組字...", cbTS.messageDurationTime)
                            if cbTS.autoClearCompositionChar:
                                if cbTS.compositionBufferMode:
                                    RemoveStringLength = 0
                                    if not cbTS.compositionChar == '':
                                        RemoveStringLength = self.calcRemoveStringLength(cbTS)
                                    self.removeCompositionBufferString(cbTS, RemoveStringLength, True)
                                self.resetComposition(cbTS)
                            if cbTS.playSoundWhenNonCand:
                                winsound.PlaySound('alert', winsound.SND_ASYNC)

                cbTS.setShowCandidates(False)
                cbTS.isShowCandidates = False

        # 聯想字模式
        if PhraseData.phrase is None:
            cbTS.phrasemode = False

        if cbTS.showPhrase and cbTS.phrasemode:
            if self.isNumberChar(keyCode) and keyEvent.isKeyDown(VK_SHIFT) and not cbTS.imeDirName == "chedayi":
                charCode = keyCode
                charStr = chr(charCode)
            phrasecandidates = []
            if cbTS.userphrase.isInCharDef(cbTS.lastCommitString):
                phrasecandidates = cbTS.userphrase.getCharDef(cbTS.lastCommitString)
            if PhraseData.phrase.isInCharDef(cbTS.lastCommitString):
                if len(phrasecandidates) == 0:
                    phrasecandidates = PhraseData.phrase.getCharDef(cbTS.lastCommitString)
                else:
                    if not cbTS.isShowPhraseCandidates:
                        plist = PhraseData.phrase.getCharDef(cbTS.lastCommitString)
                        for pstr in plist:
                            if not pstr in phrasecandidates:
                                phrasecandidates.append(pstr)

            if phrasecandidates:
                candCursor = cbTS.candidateCursor  # 目前的游標位置
                candCount = len(cbTS.candidateList)  # 目前選字清單項目數
                currentCandPageCount = math.ceil(len(phrasecandidates) / cbTS.candPerPage) # 目前的選字清單總頁數
                currentCandPage = cbTS.currentCandPage # 目前的選字清單頁數

                if cbTS.showCandidates:
                    cbTS.canSetPhraseCommitString = True
                else:
                    cbTS.canSetPhraseCommitString = False

                # 候選清單分頁
                pagecandidates = list(self.chunks(phrasecandidates, cbTS.candPerPage))
                cbTS.setCandidateList(pagecandidates[currentCandPage])
                cbTS.setShowCandidates(True)

                # 使用選字鍵執行項目或輸出候選字
                if (self.isInSelKeys(cbTS, charCode) and keyEvent.isKeyDown(VK_SHIFT) and not cbTS.imeDirName == "chedayi") or (self.isInSelKeys(cbTS, charCode) and not keyEvent.isKeyDown(VK_SHIFT) and cbTS.imeDirName == "chedayi"):
                    if cbTS.isShowPhraseCandidates:
                        if cbTS.imeDirName == "chedayi":
                            i = cbTS.selKeys.index(charStr) + 1
                        else:
                            i = cbTS.selKeys.index(charStr) 
                        if i < cbTS.candPerPage and i < len(cbTS.candidateList):
                            commitStr = cbTS.candidateList[i]
                            cbTS.compositionBufferType = "phrase"
                            self.setOutputString(cbTS, RCinTable, commitStr)

                            cbTS.phrasemode = False
                            cbTS.isShowPhraseCandidates = False

                            self.resetComposition(cbTS)
                            candCursor = 0
                            currentCandPage = 0

                            if not cbTS.directShowCand:
                                cbTS.canSetCommitString = True
                                cbTS.isShowCandidates = False
                    else:
                        cbTS.isShowPhraseCandidates = True
                        cbTS.isShowPhraseCandidates = True
                elif keyCode == VK_UP:  # 游標上移
                    if (candCursor - cbTS.candPerRow) < 0:
                        if currentCandPage > 0:
                            currentCandPage -= 1
                            candCursor = 0
                    else:
                        if (candCursor - cbTS.candPerRow) >= 0:
                            candCursor = candCursor - cbTS.candPerRow
                elif keyCode == VK_DOWN and cbTS.canSetCommitString:  # 游標下移
                    if (candCursor + cbTS.candPerRow) >= cbTS.candPerPage:
                        if (currentCandPage + 1) < currentCandPageCount:
                            currentCandPage += 1
                            candCursor = 0
                    else:
                        if (candCursor + cbTS.candPerRow) < len(pagecandidates[currentCandPage]):
                            candCursor = candCursor + cbTS.candPerRow
                elif keyCode == VK_LEFT:  # 游標左移
                    if candCursor > 0:
                        candCursor -= 1
                    else:
                        if currentCandPage > 0:
                            currentCandPage -= 1
                            candCursor = 0
                elif keyCode == VK_RIGHT:  # 游標右移
                    if (candCursor + 1) < candCount:
                        candCursor += 1
                    else:
                        if (currentCandPage + 1) < currentCandPageCount:
                            currentCandPage += 1
                            candCursor = 0
                elif keyCode == VK_HOME:  # Home 鍵
                    candCursor = 0
                elif keyCode == VK_END:  # End 鍵
                    candCursor = len(pagecandidates[currentCandPage]) - 1
                elif keyCode == VK_PRIOR:  # Page UP 鍵
                    if currentCandPage > 0:
                        currentCandPage -= 1
                        candCursor = 0
                elif keyCode == VK_NEXT:  # Page Down 鍵
                    if (currentCandPage + 1) < currentCandPageCount:
                        currentCandPage += 1
                        candCursor = 0
                elif keyCode == VK_SPACE and not cbTS.switchPageWithSpace:  # 按下 Enter 鍵或空白鍵
                    if cbTS.isShowPhraseCandidates:
                        # 找出目前游標位置的選字鍵 (1234..., asdf...等等)
                        commitStr = cbTS.candidateList[candCursor]
                        cbTS.compositionBufferType = "phrase"
                        self.setOutputString(cbTS, RCinTable, commitStr)

                        cbTS.phrasemode = False
                        cbTS.isShowPhraseCandidates = False

                        self.resetComposition(cbTS)
                        candCursor = 0
                        currentCandPage = 0

                        if not cbTS.directShowCand:
                            cbTS.isShowCandidates = False
                elif keyCode == VK_SPACE and cbTS.switchPageWithSpace: # 按下空白鍵
                    if cbTS.canUseSpaceAsPageKey:
                        if (currentCandPage + 1) < currentCandPageCount:
                            currentCandPage += 1
                            candCursor = 0
                        else:
                            currentCandPage = 0
                            candCursor = 0
                else: # 按下其它鍵，先將候選字游標位址及目前頁數歸零
                    if cbTS.canSetPhraseCommitString or cbTS.multifunctionmode:
                        cbTS.phrasemode = False
                        cbTS.isShowPhraseCandidates = False
                        self.resetComposition(cbTS)
                        candCursor = 0
                        currentCandPage = 0

                        if cbTS.cin.isInKeyName(charStrLow) and not keyEvent.isKeyDown(VK_SHIFT):
                            cbTS.compositionChar = charStrLow
                            keyname = cbTS.cin.getKeyName(charStrLow)

                            if cbTS.imeDirName == "chedayi":
                                if cbTS.selDayiSymbolCharType == 0:
                                    if cbTS.compositionChar == '=':
                                        keyname = cbTS.DayiSymbolString
                                        cbTS.dayisymbolsmode = True
                                else:
                                    if cbTS.compositionChar == "'":
                                        keyname = cbTS.DayiSymbolString
                                        cbTS.dayisymbolsmode = True

                            if not cbTS.compositionBufferMode:
                                cbTS.setCompositionString(keyname)
                                cbTS.setCompositionCursor(len(cbTS.compositionString))

                            if cbTS.directShowCand and candidates and not cbTS.dayisymbolsmode:
                                pagecandidates = list(self.chunks(candidates, cbTS.candPerPage))
                                cbTS.setCandidateList(pagecandidates[currentCandPage])
                                cbTS.setShowCandidates(True)
                        elif len(cbTS.compositionChar) == 0 and charStr == '`':
                            cbTS.compositionChar += charStr
                            cbTS.multifunctionmode = True
                            if not cbTS.compositionBufferMode:
                                cbTS.setCompositionString(cbTS.compositionChar)
                        elif keyEvent.isPrintableChar() and not keyEvent.isKeyDown(VK_SHIFT) and cbTS.shapeMode == HALFSHAPE_MODE:
                            if cbTS.compositionBufferMode:
                                self.setCompositionBufferString(cbTS, charStr, 0)
                            else:
                                cbTS.setCommitString(charStr)

                # 更新選字視窗游標位置及頁數
                cbTS.setCandidateCursor(candCursor)
                cbTS.setCandidatePage(currentCandPage)
                cbTS.setCandidateList(pagecandidates[currentCandPage])

                if cbTS.showPhrase and cbTS.phrasemode:
                    cbTS.isShowPhraseCandidates = True
            else:
                cbTS.phrasemode = False
                cbTS.isShowPhraseCandidates = False

        if cbTS.langMode == CHINESE_MODE and cbTS.isComposing() and not cbTS.showCandidates:
            if cbTS.closemenu and not cbTS.multifunctionmode and not cbTS.phrasemode and not cbTS.selcandmode:
                if keyCode == VK_RETURN:
                    if cbTS.cin.isInKeyName(cbTS.compositionChar) and len(cbTS.compositionChar) == 1 and self.isSymbolsAndNumberChar(cbTS.compositionChar):
                        cbTS.setCommitString(cbTS.compositionString)
                        self.resetComposition(cbTS)
                        self.resetCompositionBuffer(cbTS)

        if cbTS.autoMoveCursorInBrackets:
            if cbTS.compositionBufferMode:
                if keyCode == VK_SPACE or keyCode == VK_RETURN:
                    moveCursor = False
                    if cbTS.lastCommitString in cbTS.bracketSymbolList:
                        moveCursor = True
                    elif len(cbTS.compositionBufferString) >= 2 and cbTS.compositionBufferCursor >= 2:
                        bracketStr = cbTS.compositionBufferString[cbTS.compositionBufferCursor - 2] + cbTS.compositionBufferString[cbTS.compositionBufferCursor - 1]
                        if bracketStr in cbTS.bracketSymbolList:
                            moveCursor = True
                    if moveCursor:
                        cbTS.compositionBufferCursor -= 1
                        cbTS.setCompositionCursor(cbTS.compositionBufferCursor)
                        self.resetComposition(cbTS)
                        cbTS.lastCommitString = ''
                elif len(cbTS.compositionBufferString) >= 2 and cbTS.compositionBufferCursor >= 2 and not cbTS.showCandidates and not keyCode == VK_RIGHT:
                    self.moveCursorInBrackets(cbTS)

        if not cbTS.canUseSpaceAsPageKey:
            cbTS.canUseSpaceAsPageKey = True

        if not cbTS.closemenu:
            cbTS.closemenu = True

        #print('DurationTime: ' + str(time.time() - cbTS.lastKeyDownTime))
        #print('Cursor = ' + str(cbTS.compositionBufferCursor))
        #print('Type = ' + cbTS.compositionBufferType)
        #print(cbTS.compositionBufferChar)

        return True

    # 使用者放開按鍵，在 app 收到前先過濾那些鍵是輸入法需要的。
    # return True，系統會呼叫 onKeyUp() 進一步處理這個按鍵
    # return False，表示我們不需要這個鍵，系統會原封不動把按鍵傳給應用程式
    def filterKeyUp(self, cbTS, keyEvent):
        # 若啟用使用 Shift 鍵切換中英文模式
        if cbTS.cfg.switchLangWithShift:
            # 剛才最後一個按下的鍵，和現在放開的鍵，都是 Shift
            if cbTS.lastKeyDownCode == VK_SHIFT and keyEvent.keyCode == VK_SHIFT:
                pressedDuration = time.time() - cbTS.lastKeyDownTime
                # 按下和放開的時間相隔 < 0.5 秒
                if pressedDuration < 0.5:
                    cbTS.isLangModeChanged = True
                    return True

        # 不管中英文模式，只要放開 CapsLock 鍵，輸入法都須要處理
        if cbTS.lastKeyDownCode == VK_CAPITAL and keyEvent.keyCode == VK_CAPITAL:
            return True

        cbTS.lastKeyDownCode = 0
        cbTS.lastKeyDownTime = 0.0


        # 若切換全形/半形模式
        if cbTS.isShapeModeChanged:
            return True

        if cbTS.isSelKeysChanged:
            return True

        if cbTS.showPhrase and cbTS.phrasemode and cbTS.isShowPhraseCandidates:
            return True

        if cbTS.showMessageOnKeyUp:
            return True

        if cbTS.hideMessageOnKeyUp:
            return True

        return False


    def onKeyUp(self, cbTS, keyEvent):
        charCode = keyEvent.charCode
        keyCode = keyEvent.keyCode

        cbTS.lastKeyDownCode = 0
        cbTS.lastKeyDownTime = 0.0

        # 若放開 Shift 鍵,且觸發中英文切換
        if cbTS.isLangModeChanged and keyCode == VK_SHIFT:
            self.toggleLanguageMode(cbTS)  # 切換中英文模式
            cbTS.isLangModeChanged = False
            cbTS.showmenu = False
            cbTS.multifunctionmode = False
            if not cbTS.hidePromptMessages:
                message = '中文模式' if cbTS.langMode == CHINESE_MODE else '英數模式'
                cbTS.isShowMessage = True
                cbTS.showMessage(message, cbTS.messageDurationTime)
            if cbTS.showCandidates or len(cbTS.compositionChar) > 0 or len(cbTS.compositionBufferString) > 0:
                if cbTS.compositionBufferMode and not cbTS.selcandmode:
                    RemoveStringLength = self.calcRemoveStringLength(cbTS)
                    self.removeCompositionBufferString(cbTS, RemoveStringLength, True)
                self.resetComposition(cbTS)

        # 若放開 CapsLock 鍵
        if keyEvent.keyCode == VK_CAPITAL:
            self.updateLangButtons(cbTS)

        if cbTS.isShapeModeChanged:
            cbTS.isShapeModeChanged = False
            if not cbTS.hidePromptMessages:
                message = '半形模式' if cbTS.shapeMode == HALFSHAPE_MODE else '全形模式'
                cbTS.isShowMessage = True
                cbTS.showMessage(message, cbTS.messageDurationTime)
            if cbTS.showCandidates or len(cbTS.compositionChar) > 0:
                if cbTS.compositionBufferMode and not cbTS.selcandmode:
                    RemoveStringLength = self.calcRemoveStringLength(cbTS)
                    self.removeCompositionBufferString(cbTS, RemoveStringLength, True)
                self.resetComposition(cbTS)

        if cbTS.isSelKeysChanged:
            cbTS.setCandidateList(cbTS.candidateList)
            if cbTS.isShowCandidates:
                cbTS.setShowCandidates(True)
            cbTS.isSelKeysChanged = False

        if cbTS.showPhrase and cbTS.phrasemode and cbTS.isShowPhraseCandidates:
            cbTS.setShowCandidates(True)

        if cbTS.showMessageOnKeyUp:
            if not cbTS.onKeyUpMessage == "":
                cbTS.showMessage(cbTS.onKeyUpMessage, cbTS.messageDurationTime)
            cbTS.showMessageOnKeyUp = False
            cbTS.onKeyUpMessage = ""

        if cbTS.hideMessageOnKeyUp:
            cbTS.showMessage("", 0)
            cbTS.isShowMessage = False
            cbTS.hideMessageOnKeyUp = False


    def onPreservedKey(self, cbTS, guid):
        cbTS.lastKeyDownCode = 0;
        # some preserved keys registered are pressed
        if guid == SHIFT_SPACE_GUID: # 使用者按下 shift + space
            cbTS.isShapeModeChanged = True
            self.toggleShapeMode(cbTS)  # 切換全半形
            return True
        return False


    def onCommand(self, cbTS, commandId, commandType):
        if commandId == ID_SWITCH_LANG and commandType == 0:  # 切換中英文模式
            self.toggleLanguageMode(cbTS)
        elif commandId == ID_SWITCH_SHAPE and commandType == 0:  # 切換全形/半形
            self.toggleShapeMode(cbTS)
        elif commandId == ID_SETTINGS:  # 開啟設定工具
            tool_name = "config"
            config_tool = '"{0}" {1} {2}'.format(os.path.join(self.cinbasecurdir, "configtool.py"), tool_name, cbTS.imeDirName)
            python_exe = sys.executable  # 找到 python 執行檔
            # 使用我們自帶的 python runtime exe 執行 config tool
            # 此處也可以用 subprocess，不過使用 windows API 比較方便
            r = windll.shell32.ShellExecuteW(None, "open", python_exe, config_tool, self.cinbasecurdir, 0)  # SW_HIDE = 0 (hide the window)
        elif commandId == ID_MODE_ICON: # windows 8 mode icon
            self.toggleLanguageMode(cbTS)  # 切換中英文模式
        elif commandId == ID_WEBSITE: # visit chewing website
            os.startfile("https://github.com/EasyIME/PIME")
        elif commandId == ID_BUGREPORT: # visit bug tracker page
            os.startfile("https://github.com/EasyIME/PIME/issues")
        elif commandId == ID_FORUM:
            os.startfile("https://github.com/EasyIME/forum")
        elif commandId == ID_MOEDICT: # a very awesome online Chinese dictionary
            os.startfile("https://www.moedict.tw/")
        elif commandId == ID_DICT: # online Chinese dictonary
            os.startfile("http://dict.revised.moe.edu.tw/cbdic/")
        elif commandId == ID_SIMPDICT: # a simplified version of the online dictonary
            os.startfile("http://dict.concised.moe.edu.tw/jbdic/")
        elif commandId == ID_LITTLEDICT: # a simplified dictionary for little children
            os.startfile("http://dict.mini.moe.edu.tw/cgi-bin/gdic/gsweb.cgi?o=ddictionary")
        elif commandId == ID_PROVERBDICT: # a dictionary for proverbs (seems to be broken at the moment?)
            os.startfile("http://dict.idioms.moe.edu.tw/cydic/")
        elif commandId == ID_OUTPUT_SIMP_CHINESE:  # 切換簡體中文輸出
            self.setOutputSimplifiedChinese(cbTS, not cbTS.outputSimpChinese)


    # 開啟語言列按鈕選單
    def onMenu(self, cbTS, buttonId):
        # 設定按鈕 (windows 8 mode icon 按鈕也使用同一個選單)
        if buttonId == "settings" or buttonId == "windows-mode-icon":
            # 用 json 語法表示選單結構
            return [
                {"text": "參觀 PIME 官方網站(&W)", "id": ID_WEBSITE},
                {},
                {"text": "PIME 錯誤回報(&B)", "id": ID_BUGREPORT},
                {"text": "PIME 討論區 (&F)", "id": ID_FORUM},
                {},
                {"text": "設定輸入法模組(&C)", "id": ID_SETTINGS},
                {},
                {"text": "網路辭典 (&D)", "submenu": [
                    {"text": "萌典 (moedict)", "id": ID_MOEDICT},
                    {},
                    {"text": "教育部國語辭典", "id": ID_DICT},
                    {"text": "教育部國語辭典簡編本", "id": ID_SIMPDICT},
                    {"text": "教育部國語小字典", "id": ID_LITTLEDICT},
                    {"text": "教育部成語典", "id": ID_PROVERBDICT},
                ]},
                {"text": "輸出簡體中文 (&S)", "id": ID_OUTPUT_SIMP_CHINESE, "checked": cbTS.outputSimpChinese}
            ]
        return None


    # 鍵盤開啟/關閉時會被呼叫 (在 Windows 10 Ctrl+Space 時)
    def onKeyboardStatusChanged(self, cbTS, opened):
        if opened: # 鍵盤開啟
            self.resetComposition(cbTS)
            self.resetCompositionBuffer(cbTS)
        else: # 鍵盤關閉，輸入法停用
            self.resetComposition(cbTS)
            self.resetCompositionBuffer(cbTS)

        # Windows 8 systray IME mode icon
        if cbTS.client.isWindows8Above:
            # 若鍵盤關閉，我們需要把 widnows 8 mode icon 設定為 disabled
            cbTS.changeButton("windows-mode-icon", enable=opened)
        # FIXME: 是否需要同時 disable 其他語言列按鈕？


    # 當中文編輯結束時會被呼叫。若中文編輯不是正常結束，而是因為使用者
    # 切換到其他應用程式或其他原因，導致我們的輸入法被強制關閉，此時
    # forced 參數會是 True，在這種狀況下，要清除一些 buffer
    def onCompositionTerminated(self, cbTS, forced):
        if not cbTS.showmenu and not cbTS.keepComposition:
            self.resetComposition(cbTS)

        if cbTS.compositionBufferMode:
            self.resetCompositionBuffer(cbTS)

        if cbTS.keepComposition:
            cbTS.keepComposition = False

            if cbTS.keepType != "":
                if cbTS.keepType == "menusymbols":
                    if cbTS.compositionChar == "`":
                        self.resetComposition(cbTS)
                        cbTS.multifunctionmode = True
                        cbTS.compositionChar = "`"
                        cbTS.setCompositionString("`")
                if cbTS.keepType == "fullShapeSymbols":
                    if cbTS.fsymbols.isInCharDef(cbTS.compositionChar):
                        fullShapeSymbolsList = cbTS.fsymbols.getCharDef(cbTS.compositionChar)
                        cbTS.fullsymbolsmode = True
                        cbTS.setCompositionString(fullShapeSymbolsList[0])
                if cbTS.keepType == "ctrlsymbols":
                    if cbTS.msymbols.isInCharDef(cbTS.compositionChar):
                        ctrlSymbolsList = cbTS.msymbols.getCharDef(cbTS.compositionChar)
                        cbTS.ctrlsymbolsmode = True
                        cbTS.setCompositionString(ctrlSymbolsList[0])
                cbTS.keepType = ""
            else:
                for cStr in cbTS.compositionChar:
                    if cbTS.cin.isInKeyName(cStr):
                        cbTS.compositionString += cbTS.cin.getKeyName(cStr)
                    elif cbTS.supportWildcard and cbTS.selWildcardChar == "*" and cStr == "*":
                        cbTS.compositionString += "＊"
            cbTS.setCompositionCursor(len(cbTS.compositionString))


    # 切換中英文模式
    def toggleLanguageMode(self, cbTS):
        if cbTS.langMode == CHINESE_MODE:
            cbTS.langMode = ENGLISH_MODE
        elif cbTS.langMode == ENGLISH_MODE:
            cbTS.langMode = CHINESE_MODE
        self.updateLangButtons(cbTS)


    # 切換全形/半形
    def toggleShapeMode(self, cbTS):
        if cbTS.shapeMode == HALFSHAPE_MODE:
            cbTS.shapeMode = FULLSHAPE_MODE
        elif cbTS.shapeMode == FULLSHAPE_MODE:
            cbTS.shapeMode = HALFSHAPE_MODE
        self.updateLangButtons(cbTS)


    # 依照目前輸入法狀態，更新語言列顯示
    def updateLangButtons(self, cbTS):
        # 如果中英文模式發生改變
        icon_name = "chi.ico" if cbTS.langMode == CHINESE_MODE else "eng.ico"
        icon_path = os.path.join(self.icondir, icon_name)
        cbTS.changeButton("switch-lang", icon=icon_path)
        cbTS.capsStates = True if self.getKeyState(VK_CAPITAL) else False

        if cbTS.client.isWindows8Above:  # windows 8 mode icon
            if cbTS.langMode == CHINESE_MODE:
                if cbTS.shapeMode == FULLSHAPE_MODE:
                    icon_name = "chi_full_capson.ico" if cbTS.capsStates else "chi_full_capsoff.ico"
                else:
                    icon_name = "chi_half_capson.ico" if cbTS.capsStates else "chi_half_capsoff.ico"
            else:
                if cbTS.shapeMode == FULLSHAPE_MODE:
                    icon_name = "eng_full_capson.ico" if cbTS.capsStates else "eng_full_capsoff.ico"
                else:
                    icon_name = "eng_half_capson.ico" if cbTS.capsStates else "eng_half_capsoff.ico"

            icon_path = os.path.join(self.icondir, icon_name)
            cbTS.changeButton("windows-mode-icon", icon=icon_path)

        # 如果全形半形模式改變
        icon_name = "full.ico" if cbTS.shapeMode == FULLSHAPE_MODE else "half.ico"
        icon_path = os.path.join(self.icondir, icon_name)
        cbTS.changeButton("switch-shape", icon=icon_path)


    # 設定輸出成簡體中文
    def setOutputSimplifiedChinese(self, cbTS, outputSimpChinese):
        cbTS.outputSimpChinese = outputSimpChinese
        # 建立 OpenCC instance 用來做繁簡體中文轉換
        if outputSimpChinese:
            if not cbTS.opencc:
                cbTS.opencc = opencc.OpenCC(opencc.OPENCC_DEFAULT_CONFIG_TRAD_TO_SIMP)
        else:
            cbTS.opencc = None


    # 按下「`」鍵的選單命令
    def onMenuCommand(self, cbTS, commandId, commandType):
        if commandType == 0:
            if commandId == 0:
                tool_name = "config"
                config_tool = '"{0}" {1} {2}'.format(os.path.join(self.cinbasecurdir, "configtool.py"), tool_name, cbTS.imeDirName)
                python_exe = sys.executable  # 找到 python 執行檔
                # 使用我們自帶的 python runtime exe 執行 config tool
                # 此處也可以用 subprocess，不過使用 windows API 比較方便
                r = windll.shell32.ShellExecuteW(None, "open", python_exe, config_tool, self.cinbasecurdir, 0)  # SW_HIDE = 0 (hide the window)
            elif commandId == 1:
                self.setOutputSimplifiedChinese(cbTS, not cbTS.outputSimpChinese)
        elif commandType == 1: # 功能開關
            commandItem = cbTS.smenuitems[commandId]
            if commandItem == "fullShapeSymbols":
                cbTS.fullShapeSymbols = not cbTS.fullShapeSymbols
            elif commandItem == "easySymbolsWithShift":
                cbTS.easySymbolsWithShift = not cbTS.easySymbolsWithShift
            elif commandItem == "supportWildcard":
                cbTS.supportWildcard = not cbTS.supportWildcard
            elif commandItem == "autoClearCompositionChar":
                cbTS.autoClearCompositionChar = not cbTS.autoClearCompositionChar
            elif commandItem == "playSoundWhenNonCand":
                cbTS.playSoundWhenNonCand = not cbTS.playSoundWhenNonCand
            elif commandItem == "showPhrase":
                cbTS.showPhrase = not cbTS.showPhrase
            elif commandItem == "sortByPhrase":
                cbTS.sortByPhrase = not cbTS.sortByPhrase
            elif commandItem == "imeReverseLookup":
                cbTS.imeReverseLookup = not cbTS.imeReverseLookup
            elif commandItem == "homophoneQuery":
                cbTS.homophoneQuery = not cbTS.homophoneQuery


    def switchMenuType(self, cbTS, menutype, prevmenutypelist):
        cbTS.menutype = menutype
        if menutype == 0:
            cbTS.prevmenutypelist = prevmenutypelist
        else:
            if prevmenutypelist:
                cbTS.prevmenutypelist.append(prevmenutypelist[0])
            else:
                cbTS.prevmenutypelist = prevmenutypelist
        return True


    def closeMenuCand(self, cbTS):
        cbTS.showmenu = False
        cbTS.emojimenumode = False
        cbTS.menutype = 0
        cbTS.prevmenutypelist = []
        self.resetComposition(cbTS)
        return True


    def switchMenuCand(self, cbTS, menutype):
        if menutype == 0:
            menu_OutputSimpChinese = "輸出繁體" if cbTS.outputSimpChinese else "輸出簡體"
            cbTS.menucandidates = ["功能設定", menu_OutputSimpChinese, "功能開關", "特殊符號", "注音符號", "外語文字", "表情符號"]
        if menutype == 2:
            cbTS.menucandidates = cbTS.symbols.getKeyNames()
        if menutype == 5:
            cbTS.menucandidates = cbTS.menucandidates = cbTS.flangs.getKeyNames()
        if menutype == 7:
            cbTS.menucandidates = self.emojimenulist
        if menutype == 8:
            if cbTS.emojitype == 0:
                cbTS.menucandidates = self.emoji.emoticons_keynames
            elif cbTS.emojitype == 1:
                cbTS.menucandidates = self.emoji.pictographs_keynames
            elif cbTS.emojitype == 2:
                cbTS.menucandidates = self.emoji.miscellaneous_keynames
            elif cbTS.emojitype == 3:
                cbTS.menucandidates = self.emoji.dingbats_keynames
            elif cbTS.emojitype == 4:
                cbTS.menucandidates = self.emoji.transport_keynames
            elif cbTS.emojitype == 5:
                cbTS.menucandidates = self.emoji.modifiercolor

        pagecandidates = list(self.chunks(cbTS.menucandidates, cbTS.candPerPage))
        return pagecandidates


    # 重置輸入的字根
    def resetComposition(self, cbTS):
        cbTS.compositionChar = ''
        if not cbTS.compositionBufferMode:
            cbTS.setCompositionString('')
        cbTS.isShowCandidates = False
        cbTS.setCandidateCursor(0)
        cbTS.setCandidatePage(0)
        cbTS.setCandidateList([])
        cbTS.setShowCandidates(False)
        cbTS.wildcardcandidates = []
        cbTS.wildcardpagecandidates = []
        cbTS.menumode = False
        cbTS.multifunctionmode = False
        cbTS.menusymbolsmode = False
        cbTS.ctrlsymbolsmode = False
        cbTS.fullsymbolsmode = False
        cbTS.dayisymbolsmode = False
        cbTS.keepComposition = False
        cbTS.homophonemode = False
        cbTS.homophoneselpinyinmode = False
        cbTS.homophoneChar = ''
        cbTS.homophoneStr = ''
        cbTS.isHomophoneChardefs = False
        cbTS.homophonecandidates = []
        cbTS.selcandmode = False
        cbTS.lastCompositionCharLength = 0

    # 重置輸入的字根
    def resetCompositionBuffer(self, cbTS):
        if cbTS.compositionBufferMode:
            cbTS.compositionBufferCursor = 0
            cbTS.compositionBufferString = ''
            cbTS.setCompositionString('')

    # 重置同音字模式
    def resetHomophoneMode(self, cbTS):
        cbTS.homophonemode = False
        cbTS.homophoneselpinyinmode = False
        cbTS.homophoneChar = ''
        cbTS.homophoneStr = ''
        cbTS.isHomophoneChardefs = False
        cbTS.homophonecandidates = []

    # 判斷數字鍵?
    def isNumberChar(self, keyCode):
        return keyCode >= 0x30 and keyCode <= 0x39

    # 判斷符號鍵?
    def isSymbolsChar(self, keyCode):
        return keyCode >= 0xBA and keyCode <= 0xDF

    # 判斷 Ctrl 符號鍵?
    def isCtrlSymbolsChar(self, keyCode):
        return keyCode >= 0xBA and keyCode <= 0xDF and keyCode != 0xBB and keyCode != 0xBD and keyCode != 0xC0

    # 判斷字母鍵?
    def isLetterChar(self, keyCode):
        return keyCode >= 0x41 and keyCode <= 0x5A

    # 判斷符號及數字字元?
    def isSymbolsAndNumberChar(self, char):
        return (ord(char) >= 33 and ord(char) <= 64) or (ord(char) >= 91 and ord(char) <= 96) or (ord(char) >= 123 and ord(char) <= 126)

    # 判斷選字鍵?
    def isInSelKeys(self, cbTS, charCode):
        for key in cbTS.selKeys:
            if ord(key) == charCode:
                return True
        return False

    # 一般字元轉全形
    def charCodeToFullshape(self, cbTS, charCode, keyCode):
        if cbTS.langMode == CHINESE_MODE and cbTS.outputSmallLetterWithShift and self.isLetterChar(keyCode):
            char = chr(charCode).upper() if cbTS.capsStates else chr(charCode).lower()
            charCode = ord(char)

        charStr = ''
        if charCode < 0x0020 or charCode > 0x7e:
            charStr = chr(charCode)
        if charCode == 0x0020: # Spacebar
            charStr = chr(0x3000)
        else:
            charCode += 0xfee0
            charStr = chr(charCode)
        return charStr

    # 符號字元轉全形
    def SymbolscharCodeToFullshape(self, charCode):
        charStr = ''
        if charCode < 0x0020 or charCode > 0x7e:
            charStr = chr(charCode)
        if charCode == 0x0020: # Spacebar
            charStr = chr(0x3000)
        elif charCode == 0x0022: # char(") to char(、)
            charStr = chr(0x3001)
        elif charCode == 0x0027: # char(') to char(、)
            charStr = chr(0x3001)
        elif charCode == 0x002e: # char(.) to char(。)
            charStr = chr(0x3002)
        elif charCode == 0x003c: # char(<) to char(，)
            charStr = chr(0xff0c)
        elif charCode == 0x003e: # char(>) to char(。)
            charStr = chr(0x3002)
        elif charCode == 0x005f: # char(_) to char(－)
            charStr = chr(0xff0d)
        else:
            charCode += 0xfee0
            charStr = chr(charCode)
        return charStr

    def sortByPhrase(self, cbTS, candidates):
        sortbyphraselist = []
        if cbTS.userphrase.isInCharDef(cbTS.lastCommitString):
            sortbyphraselist = cbTS.userphrase.getCharDef(cbTS.lastCommitString)
        if PhraseData.phrase.isInCharDef(cbTS.lastCommitString):
            if len(sortbyphraselist) == 0:
                sortbyphraselist = PhraseData.phrase.getCharDef(cbTS.lastCommitString)
            else:
                plist = PhraseData.phrase.getCharDef(cbTS.lastCommitString)
                for pstr in plist:
                    if not pstr in sortbyphraselist:
                        sortbyphraselist.append(pstr)

        i = 0
        if len(sortbyphraselist) > 0:
            for pStr in sortbyphraselist:
                if pStr in candidates:
                    candidates.remove(pStr)
                    candidates.insert(i, pStr)
                    i += 1
        return candidates

    # List 分段
    def chunks(self, l, n):
        for i in range(0, len(l), n):
            yield l[i:i+n]

    def getKeyState(self, keyCode):
        return ctypes.WinDLL("User32.dll").GetKeyState(keyCode)

    def setCompositionBufferString(self, cbTS, compositionString, removeStringLength):
        compPos1 = cbTS.compositionBufferCursor - removeStringLength
        compPos2 = cbTS.compositionBufferCursor - len(cbTS.compositionBufferString)
        if compPos2 < 0:
            cbTS.compositionBufferString = cbTS.compositionBufferString[:compPos1] + compositionString + cbTS.compositionBufferString[compPos2:]
        else:
            cbTS.compositionBufferString = cbTS.compositionBufferString[:compPos1] + compositionString

        cbTS.compositionBufferCursor += len(compositionString) - removeStringLength
        cbTS.setCompositionString(cbTS.compositionBufferString)
        cbTS.setCompositionCursor(cbTS.compositionBufferCursor)

    def setCompositionBufferChar(self, cbTS, compositionType, compositionChar, compositionCursor):
        if compositionCursor - 1 in cbTS.compositionBufferChar:
            for key in sorted(cbTS.compositionBufferChar.keys(), reverse=True):
                if key >= compositionCursor - 1:
                    cbTS.compositionBufferChar[key + 1] = cbTS.compositionBufferChar.pop(key)
        cbTS.compositionBufferChar[compositionCursor - 1] = [compositionType, compositionChar]

    def removeCompositionBufferString(self, cbTS, removeStringLength, removeBefore):
        if removeBefore:
            compPos1 = cbTS.compositionBufferCursor - removeStringLength
            compPos2 = cbTS.compositionBufferCursor - len(cbTS.compositionBufferString)
            if compPos2 < 0:
                cbTS.compositionBufferString = cbTS.compositionBufferString[:compPos1] + cbTS.compositionBufferString[compPos2:]
            else:
                cbTS.compositionBufferString = cbTS.compositionBufferString[:compPos1]
            cbTS.compositionBufferCursor -= removeStringLength
        else:
            compPos1 = cbTS.compositionBufferCursor
            compPos2 = cbTS.compositionBufferCursor - len(cbTS.compositionBufferString) + removeStringLength
            if compPos2 < 0:
                cbTS.compositionBufferString = cbTS.compositionBufferString[:compPos1] + cbTS.compositionBufferString[compPos2:]
            else:
                cbTS.compositionBufferString = cbTS.compositionBufferString[:compPos1]
            cbTS.compositionBufferCursor = cbTS.compositionBufferCursor

        cbTS.setCompositionString(cbTS.compositionBufferString)
        cbTS.setCompositionCursor(cbTS.compositionBufferCursor)

    def setOutputString(self, cbTS, RCinTable, commitStr):
        # 如果使用萬用字元解碼
        if cbTS.isWildcardChardefs:
            cbTS.isShowMessage = True
            cbTS.showMessageOnKeyUp = True
            cbTS.onKeyUpMessage = cbTS.cin.getCharEncode(commitStr)
            cbTS.wildcardcandidates = []
            cbTS.wildcardpagecandidates = []
            cbTS.isWildcardChardefs = False

        if cbTS.imeReverseLookup:
            if RCinTable.cin is not None:
                if not RCinTable.cin.getCharEncode(commitStr) == "":
                    cbTS.isShowMessage = True
                    cbTS.showMessageOnKeyUp = True
                    cbTS.onKeyUpMessage = RCinTable.cin.getCharEncode(commitStr)
            else:
                cbTS.isShowMessage = True
                cbTS.showMessageOnKeyUp = True
                cbTS.onKeyUpMessage = "反查字根碼表尚在載入中！"

        if cbTS.homophoneQuery and cbTS.isHomophoneChardefs:
            cbTS.isHomophoneChardefs = False
            cbTS.isShowMessage = True
            cbTS.showMessageOnKeyUp = True
            cbTS.onKeyUpMessage = cbTS.cin.getCharEncode(commitStr)

        # 如果使用打繁出簡，就轉成簡體中文
        if cbTS.outputSimpChinese:
            commitStr = cbTS.opencc.convert(commitStr)

        if not cbTS.compositionBufferMode:
            cbTS.setCommitString(commitStr)
        else:
            RemoveStringLength = 0
            if not cbTS.selcandmode:
                if cbTS.menusymbolsmode:
                    RemoveStringLength = len(cbTS.compositionChar) - 1
                    cbTS.menusymbolsmode = False
                elif cbTS.dayisymbolsmode:
                    RemoveStringLength = self.calcRemoveStringLength(cbTS) - 1
                else:
                    RemoveStringLength = self.calcRemoveStringLength(cbTS)
            else:
                self.removeCompositionBufferString(cbTS, 1, False if cbTS.compositionBufferCursor < len(cbTS.compositionBufferString) else True)
            self.setCompositionBufferString(cbTS, commitStr, RemoveStringLength)
            if not cbTS.selcandmode:
                strLength = len(commitStr)
                if strLength > 1:
                    for cStr in commitStr:
                        strLength -= 1
                        if cbTS.compositionBufferType == "msymbols":
                            cChar = cbTS.compositionChar[commitStr.index(cStr)] if cbTS.compositionChar[0] != "`" else cbTS.compositionChar[commitStr.index(cStr) + 1]
                            self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, cChar, cbTS.compositionBufferCursor - strLength)
                        else:
                            self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, cbTS.compositionChar, cbTS.compositionBufferCursor - strLength)
                else:
                    self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, cbTS.compositionChar, cbTS.compositionBufferCursor)

    def setOutputFSymbols(self, cbTS, charStr):
        if cbTS.homophoneQuery and cbTS.homophonemode:
            self.resetHomophoneMode(cbTS)

        cbTS.compositionBufferType = "fsymbols"
        if cbTS.compositionBufferMode and cbTS.directShowCand and cbTS.directOutFSymbols and cbTS.fullsymbolsmode:
            self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, cbTS.compositionChar, cbTS.compositionBufferCursor)
            self.resetComposition(cbTS)

        RemoveStringLength = 0
        if cbTS.compositionBufferMode:
            if not cbTS.compositionChar == '':
                RemoveStringLength = self.calcRemoveStringLength(cbTS)

        cbTS.compositionChar = charStr
        fullShapeSymbolsList = cbTS.fsymbols.getCharDef(cbTS.compositionChar)

        if cbTS.compositionBufferMode:
            self.setCompositionBufferString(cbTS, fullShapeSymbolsList[0], RemoveStringLength)
            if not cbTS.directShowCand:
                self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, cbTS.compositionChar, cbTS.compositionBufferCursor)
                self.resetComposition(cbTS)
        else:
            commitStr = cbTS.compositionString

            if cbTS.directOutFSymbols and cbTS.fullsymbolsmode:
                cbTS.setCommitString(commitStr)
                cbTS.keepComposition = True
                cbTS.keepType = "fullShapeSymbols"

            cbTS.compositionChar = charStr
            cbTS.setCompositionString(fullShapeSymbolsList[0])
            cbTS.setCompositionCursor(len(cbTS.compositionString))
        cbTS.fullsymbolsmode = True

    def calcRemoveStringLength(self, cbTS):
        RemoveStringLength = 0
        if not cbTS.compositionChar == '':
            if cbTS.menusymbolsmode:
                if cbTS.msymbols.isInCharDef(cbTS.compositionChar[1:]):
                    RemoveStringLength = len(cbTS.msymbols.getCharDef(cbTS.compositionChar[1:])[0])
            else:
                for char in cbTS.compositionChar:
                    if cbTS.cin.isInKeyName(char):
                        RemoveStringLength += len(cbTS.cin.getKeyName(char))
                    else:
                        RemoveStringLength += 1
        return RemoveStringLength

    def moveCursorInBrackets(self, cbTS):
        bracketStr = cbTS.compositionBufferString[cbTS.compositionBufferCursor - 2] + cbTS.compositionBufferString[cbTS.compositionBufferCursor - 1]
        if bracketStr in cbTS.bracketSymbolList and cbTS.compositionChar != "":
            strLength = len(bracketStr)
            if cbTS.compositionBufferType == "msymbols" and cbTS.compositionChar[0] == "`":
                compChar = cbTS.compositionChar[1:]
            else:
                compChar = cbTS.compositionChar
            if ((cbTS.cin.isInCharDef(cbTS.compositionChar) and bracketStr in cbTS.cin.getCharDef(cbTS.compositionChar)) or
                (cbTS.msymbols.isInCharDef(compChar) and bracketStr in cbTS.msymbols.getCharDef(compChar))):
                for bStr in bracketStr:
                    strLength -= 1
                    if cbTS.compositionBufferType == "msymbols":
                        cChar = cbTS.compositionChar[bracketStr.index(bStr)] if cbTS.compositionChar[0] != "`" else cbTS.compositionChar[bracketStr.index(bStr) + 1]
                        self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, cChar, cbTS.compositionBufferCursor - strLength)
                    else:
                        self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, compChar, cbTS.compositionBufferCursor - strLength)
            else:
                self.setCompositionBufferChar(cbTS, cbTS.compositionBufferType, compChar, cbTS.compositionBufferCursor)
            cbTS.compositionBufferCursor -= 1
            cbTS.setCompositionCursor(cbTS.compositionBufferCursor)
            self.resetComposition(cbTS)
        elif bracketStr in cbTS.bracketSymbolList and cbTS.compositionBufferType == "fsymbols":
            cbTS.compositionBufferCursor -= 1
            cbTS.setCompositionCursor(cbTS.compositionBufferCursor)
            self.resetComposition(cbTS)


    ################################################################
    # config 相關
    ################################################################
    # 初始化 CinBase 輸入法引擎
    def initCinBaseContext(self, cbTS):
        cfg = cbTS.cfg # 所有 TextService 共享一份設定物件

        if not cbTS.initCinBaseState:
            # 預設英數 or 中文模式
            cbTS.langMode = ENGLISH_MODE if cfg.defaultEnglish else CHINESE_MODE

            # 預設全形 or 半形
            cbTS.shapeMode = FULLSHAPE_MODE if cfg.defaultFullSpace else HALFSHAPE_MODE

            self.updateLangButtons(cbTS)

        # 所有 CheCJTextService 共享一份輸入法碼表
        cbTS.selCinType = cfg.selCinType

        if hasattr(cbTS, 'swkb'):
            del cbTS.swkb
        if hasattr(cbTS, 'symbols'):
            del cbTS.symbols
        if hasattr(cbTS, 'fsymbols'):
            del cbTS.fsymbols
        if hasattr(cbTS, 'flangs'):
            del cbTS.flangs
        if hasattr(cbTS, 'userphrase'):
            del cbTS.userphrase
        if hasattr(cbTS, 'msymbols'):
            del cbTS.msymbols
        if hasattr(cbTS, 'extendtable'):
            del cbTS.extendtable
        if hasattr(cbTS, 'dsymbols'):
            del cbTS.dsymbols

        datadirs = (cfg.getConfigDir(), cfg.getDataDir())
        swkbPath = cfg.findFile(datadirs, "swkb.dat")
        with io.open(swkbPath, 'r', encoding='utf-8') as fs:
            cbTS.swkb = swkb(fs)

        symbolsPath = cfg.findFile(datadirs, "symbols.dat")
        with io.open(symbolsPath, 'r', encoding='utf-8') as fs:
            cbTS.symbols = symbols(fs)

        fsymbolsPath = cfg.findFile(datadirs, "fsymbols.dat")
        with io.open(fsymbolsPath, 'r', encoding='utf-8') as fs:
            cbTS.fsymbols = fsymbols(fs)

        flangsPath = cfg.findFile(datadirs, "flangs.dat")
        with io.open(flangsPath, 'r', encoding='utf-8') as fs:
            cbTS.flangs = flangs(fs)

        userphrasePath = cfg.findFile(datadirs, "userphrase.dat")
        with io.open(userphrasePath, 'r', encoding='utf-8') as fs:
            cbTS.userphrase = userphrase(fs)

        msymbolsPath = cfg.findFile(datadirs, "msymbols.json")
        with io.open(msymbolsPath, 'r', encoding='utf-8') as fs:
            cbTS.msymbols = msymbols(fs)

        extendtablePath = cfg.findFile(datadirs, "extendtable.dat")
        with io.open(extendtablePath, 'r', encoding='utf8') as fs:
            cbTS.extendtable = extendtable(fs)

        if cbTS.useDayiSymbols:
            dsymbolsPath = cfg.findFile(datadirs, "dsymbols.json")
            with io.open(dsymbolsPath, 'r', encoding='utf8') as fs:
                cbTS.dsymbols = dsymbols(fs)

        if not PhraseData.phrase and not PhraseData.loading:
            loadPhraseData = LoadPhraseData(cbTS, PhraseData)
            loadPhraseData.start()

        cbTS.initCinBaseState = True
        self.applyConfig(cbTS) # 套用其餘的使用者設定

    def applyConfig(self, cbTS):
        cfg = cbTS.cfg # 所有 TextService 共享一份設定物件
        cbTS.configVersion = cfg.getVersion()

        # 每列顯示幾個候選字
        cbTS.candPerRow = cfg.candPerRow

        # 如果程式為 UiLess 模式就取代設定
        if cbTS.client.isUiLess:
            cbTS.candPerRow = 1

        # 每頁顯示幾個候選字
        cbTS.candPerPage = cfg.candPerPage

        # 設定 UI 外觀
        cbTS.customizeUI(candFontSize = cfg.fontSize,
                        candFontName = 'MingLiu',
                        candPerRow = cfg.candPerRow,
                        candUseCursor = cfg.cursorCandList)

        # 設定選字按鍵 (123456..., asdf.... 等)
        # if cbTS.cin.getSelection():
        #     cbTS.setSelKeys(cbTS.cin.getSelection())

        # 押住 Shift 輸出英文時預設小寫?
        cbTS.outputSmallLetterWithShift = cfg.outputSmallLetterWithShift

        # 使用空白鍵作為候選清單換頁鍵?
        cbTS.switchPageWithSpace = cfg.switchPageWithSpace

        # 轉換輸出成簡體中文?
        self.setOutputSimplifiedChinese(cbTS, cfg.outputSimpChinese)

        # Shift 輸入全形標點?
        cbTS.fullShapeSymbols = cfg.fullShapeSymbols

        # 直接輸出全形標點首個候選符號?
        cbTS.directOutFSymbols = cfg.directOutFSymbols

        # Shift 快速輸入符號?
        cbTS.easySymbolsWithShift = cfg.easySymbolsWithShift

        # 提示訊息顯示時間?
        cbTS.messageDurationTime = cfg.messageDurationTime + 2

        # 隱藏提示訊息?
        cbTS.hidePromptMessages = cfg.hidePromptMessages

        # 輸出字串後顯示聯想字詞?
        cbTS.showPhrase = cfg.showPhrase

        # 優先以聯想字詞排序候選清單?
        cbTS.sortByPhrase = cfg.sortByPhrase

        # 拆錯字碼時自動清除輸入字串?
        cbTS.autoClearCompositionChar = cfg.autoClearCompositionChar

        # 拆錯字碼時發出警告嗶聲提示?
        cbTS.playSoundWhenNonCand  = cfg.playSoundWhenNonCand 

        # 直接顯示候選字清單 (不須按空白鍵)?
        cbTS.directShowCand = cfg.directShowCand

        # 直接輸出候選字 (當候選字僅有一個)?
        cbTS.directCommitString = cfg.directCommitString

        # 標點符號自動確認輸入?
        cbTS.directCommitSymbol = cfg.directCommitSymbol

        # 允許內建符號輸入方式連續輸入?
        cbTS.directOutMSymbols = cfg.directOutMSymbols

        # 支援以萬用字元代替組字字根?
        cbTS.supportWildcard = cfg.supportWildcard

        # 使用的萬用字元?
        if cfg.selWildcardType == 0:
            cbTS.selWildcardChar = 'z'
        elif cfg.selWildcardType == 1:
            cbTS.selWildcardChar = '*'

        # 最大候選字個數?
        cbTS.candMaxItems = cfg.candMaxItems

        # 啟用組字編輯模式?
        cbTS.compositionBufferMode = cfg.compositionBufferMode

        # 自動移動組字游標至括號中間?
        cbTS.autoMoveCursorInBrackets = cfg.autoMoveCursorInBrackets

        # 反查輸入法字根
        self.updateRcinFileList(cbTS)
        cbTS.imeReverseLookup = cfg.imeReverseLookup
        cbTS.selRCinType = cfg.selRCinType

        # 同音字查詢
        cbTS.homophoneQuery = cfg.homophoneQuery
        cbTS.selHCinType = cfg.selHCinType

        # 載入碼表時忽略 Unicode 私用區?
        cbTS.ignorePrivateUseArea = cfg.ignorePrivateUseArea

        # 擴充碼表?
        cbTS.userExtendTable = cfg.userExtendTable
        cbTS.reLoadTable = cfg.reLoadTable
        cbTS.priorityExtendTable = cfg.priorityExtendTable

        # 訊息顯示時間?
        cbTS.messageDurationTime = cfg.messageDurationTime

        if cbTS.imeDirName == "chedayi":
            cbTS.selDayiSymbolCharType = cfg.selDayiSymbolCharType


    # 檢查設定檔是否有被更改，是否需要套用新設定
    def checkConfigChange(self, cbTS, CinTable, RCinTable, HCinTable):
        cfg = cbTS.cfg # 所有 TextService 共享一份設定物件
        cfg.update() # 更新設定檔狀態
        reLoadCinTable = False
        updateExtendTable = False

        if hasattr(cbTS, 'cin'):
            if hasattr(cbTS.cin, 'cincount'):
                if not os.path.exists(cbTS.cin.getCountFile()):
                    cbTS.cin.saveCountFile()

        # 如果有更換輸入法碼表，就重新載入碼表資料
        if not CinTable.loading:
            if not CinTable.curCinType == cfg.selCinType:
                reLoadCinTable = True

            if not CinTable.ignorePrivateUseArea == cfg.ignorePrivateUseArea:
                reLoadCinTable = True

            if cfg.reLoadTable:
                updateExtendTable = True
                reLoadCinTable = True
                cfg.reLoadTable = False
                cfg.save()

            if not CinTable.userExtendTable == cfg.userExtendTable:
                updateExtendTable = True
                reLoadCinTable = True

            if not CinTable.priorityExtendTable == cfg.priorityExtendTable:
                if cfg.userExtendTable:
                    reLoadCinTable = True

        if cfg.imeReverseLookup or cbTS.imeReverseLookup:
            # 載入反查輸入法碼表
            if not RCinTable.loading and not CinTable.loading:
                if not RCinTable.curCinType == cfg.selRCinType or RCinTable.cin is None:
                    loadRCinFile = LoadRCinTable(cbTS, RCinTable)
                    loadRCinFile.start()

        if cfg.homophoneQuery or cbTS.homophoneQuery:
            # 載入同音字碼表
            if not HCinTable.loading and not CinTable.loading:
                if not HCinTable.curCinType == cfg.selHCinType or HCinTable.cin is None:
                    loadHCinFile = LoadHCinTable(cbTS, HCinTable)
                    loadHCinFile.start()

        # 比較我們先前存的版本號碼，和目前設定檔的版本號
        if cfg.isFullReloadNeeded(cbTS.configVersion):
            # 資料改變需整個 reload，重建一個新的 checj context
            self.initCinBaseContext(cbTS)
        elif cfg.isConfigChanged(cbTS.configVersion):
            # 只有偵測到設定檔變更，需要套用新設定
            self.applyConfig(cbTS)

        if reLoadCinTable or updateExtendTable:
            datadirs = (cfg.getConfigDir(), cfg.getDataDir())
            if updateExtendTable:
                if hasattr(cbTS, 'extendtable'):
                    del cbTS.extendtable
                extendtablePath = cfg.findFile(datadirs, "extendtable.dat")
                with io.open(extendtablePath, encoding='utf-8') as fs:
                    cbTS.extendtable = extendtable(fs)
            if reLoadCinTable:
                cbTS.reLoadCinTable = True
            loadCinFile = LoadCinTable(cbTS, CinTable)
            loadCinFile.start()
        else:
            if not cbTS.cin == CinTable.cin:
                cbTS.cin = CinTable.cin

        if DEBUG_MODE:
            if not cbTS.debugLog == cbTS.debug.debugLog:
                if not CinTable.loading and (not cbTS.imeReverseLookup or not RCinTable.loading) and (not cbTS.homophoneQuery or not HCinTable.loading):
                    cbTS.debug.saveDebugLog(cbTS.debugLog)


    def updateRcinFileList(self, cbTS):
        cfg = cbTS.cfg
        cbTS.rcinFileList = []
        for imeName in self.imeNameList:
            filelist = self.ReverseCinDict[imeName]
            for filename in filelist:
                filepath = os.path.join(cbTS.jsondir, filename)
                if os.path.exists(filepath):
                    cbTS.rcinFileList.append(filename)
        if not cfg.rcinFileList == cbTS.rcinFileList:
            cfg.rcinFileList = cbTS.rcinFileList
            cfg.save()


CinBase = CinBase()

class PhraseData:
    loading = False
    def __init__(self):
        self.phrase = None
PhraseData = PhraseData()


class LoadPhraseData(threading.Thread):
    def __init__(self, cbTS, PhraseData):
        threading.Thread.__init__(self)
        self.cbTS = cbTS
        self.PhraseData = PhraseData

    def run(self):
        self.PhraseData.loading = True
        cfg = self.cbTS.cfg
        datadirs = (cfg.getConfigDir(), cfg.getDataDir())

        if hasattr(self.PhraseData.phrase, '__del__'):
            self.PhraseData.phrase.__del__()

        self.PhraseData.phrase = None

        phrasePath = cfg.findFile(datadirs, "phrase.json")
        with io.open(phrasePath, 'r', encoding='utf8') as fs:
            self.PhraseData.phrase = phrase(fs)
        self.PhraseData.loading = False


class LoadCinTable(threading.Thread):
    def __init__(self, cbTS, CinTable):
        threading.Thread.__init__(self)
        self.cbTS = cbTS
        self.CinTable = CinTable

    def run(self):
        if DEBUG_MODE:
            self.cbTS.debug.setStartTimer("LoadCinTable")

        self.CinTable.loading = True
        if self.cbTS.cfg.selCinType >= len(self.cbTS.cinFileList):
            self.cbTS.cfg.selCinType = 0
        selCinFile = self.cbTS.cinFileList[self.cbTS.cfg.selCinType]
        jsonPath = os.path.join(self.cbTS.jsondir, selCinFile)

        if self.cbTS.reLoadCinTable or not hasattr(self.cbTS, 'cin'):
            self.cbTS.reLoadCinTable = False

            if hasattr(self.cbTS, 'cin'):
                self.cbTS.cin.__del__()
            if hasattr(self.CinTable.cin, '__del__'):
                self.CinTable.cin.__del__()

            self.cbTS.cin = None
            self.CinTable.cin = None

            with io.open(jsonPath, 'r', encoding='utf8') as fs:
                self.cbTS.cin = Cin(fs, self.cbTS.imeDirName, self.cbTS.ignorePrivateUseArea)
            self.CinTable.cin = self.cbTS.cin
            self.CinTable.curCinType = self.cbTS.cfg.selCinType

        if not hasattr(self.cbTS, 'extendtable'):
            if self.cbTS.cfg.userExtendTable:
                datadirs = (self.cbTS.cfg.getConfigDir(), self.cbTS.cfg.getDataDir())
                extendtablePath = self.cbTS.cfg.findFile(datadirs, "extendtable.dat")
                with io.open(extendtablePath, encoding='utf-8') as fs:
                    self.cbTS.extendtable = extendtable(fs)
            else:
                self.cbTS.extendtable = {}
        self.cbTS.cin.updateCinTable(self.cbTS.cfg.userExtendTable, self.cbTS.cfg.priorityExtendTable, self.cbTS.extendtable, self.cbTS.cfg.ignorePrivateUseArea)
        self.CinTable.userExtendTable = self.cbTS.cfg.userExtendTable
        self.CinTable.priorityExtendTable = self.cbTS.cfg.priorityExtendTable
        self.CinTable.ignorePrivateUseArea = self.cbTS.cfg.ignorePrivateUseArea
        self.CinTable.loading = False

        if DEBUG_MODE:
            self.cbTS.debug.setEndTimer("LoadCinTable")
            self.cbTS.debugLog[time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + " [C]"] = self.cbTS.debug.info['brand'] + ":「" + self.cbTS.debug.jsonNameDict[selCinFile] + "」碼表載入時間約為 " + self.cbTS.debug.getDurationTime("LoadCinTable") + " 秒"


class LoadRCinTable(threading.Thread):
    def __init__(self, cbTS, RCinTable):
        threading.Thread.__init__(self)
        self.cbTS = cbTS
        self.RCinTable = RCinTable

    def run(self):
        if DEBUG_MODE:
            self.cbTS.debug.setStartTimer("LoadRCinTable")

        self.RCinTable.loading = True
        selCinFile = self.cbTS.rcinFileList[self.cbTS.cfg.selRCinType]
        jsonPath = os.path.join(self.cbTS.jsondir, selCinFile)

        if self.RCinTable.cin is not None and hasattr(self.RCinTable.cin, '__del__'):
            self.RCinTable.cin.__del__()

        self.RCinTable.cin = None

        with io.open(jsonPath, 'r', encoding='utf8') as fs:
            self.RCinTable.cin = RCin(fs, self.cbTS.imeDirName)
        self.RCinTable.curCinType = self.cbTS.cfg.selRCinType
        self.RCinTable.loading = False

        if DEBUG_MODE:
            self.cbTS.debug.setEndTimer("LoadRCinTable")
            self.cbTS.debugLog[time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + " [R]"] = self.cbTS.debug.info['brand'] + ":「" + self.cbTS.debug.jsonNameDict[selCinFile] + "」反查碼表載入時間約為 " + self.cbTS.debug.getDurationTime("LoadRCinTable") + " 秒"


class LoadHCinTable(threading.Thread):
    def __init__(self, cbTS, HCinTable):
        threading.Thread.__init__(self)
        self.cbTS = cbTS
        self.HCinTable = HCinTable

    def run(self):
        if DEBUG_MODE:
            self.cbTS.debug.setStartTimer("LoadHCinTable")

        self.HCinTable.loading = True
        selCinFile = CinBase.hcinFileList[self.cbTS.cfg.selHCinType]
        jsonPath = os.path.join(self.cbTS.jsondir, selCinFile)

        if self.HCinTable.cin is not None and hasattr(self.HCinTable.cin, '__del__'):
            self.HCinTable.cin.__del__()

        self.HCinTable.cin = None

        with io.open(jsonPath, 'r', encoding='utf8') as fs:
            self.HCinTable.cin = HCin(fs, self.cbTS.imeDirName)
        self.HCinTable.curCinType = self.cbTS.cfg.selHCinType
        self.HCinTable.loading = False

        if DEBUG_MODE:
            self.cbTS.debug.setEndTimer("LoadHCinTable")
            self.cbTS.debugLog[time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + " [H]"] = self.cbTS.debug.info['brand'] + ":「" + self.cbTS.debug.jsonNameDict[selCinFile] + "」同音字碼表載入時間約為 " + self.cbTS.debug.getDurationTime("LoadHCinTable") + " 秒"
