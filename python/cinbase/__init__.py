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

import ctypes
import io
import math
import os.path
import threading
import time

from keycodes import *  # for VK_XXX constants
from .cin import Cin
from .debug import Debug
from .msymbols import msymbols
from .symbols import symbols

ARABIC_MODE = 1
LATIN_MODE = 0
DEBUG_MODE = False

# shift + space 熱鍵的 GUID
SHIFT_SPACE_GUID = "{f1dae0fb-8091-44a7-8a0c-3082a1515447}"
TF_MOD_SHIFT = 0x0004

# 選單項目和語言列按鈕的 command ID
ID_SWITCH_LANG = 1
ID_MODE_ICON = 3
ID_WEBSITE = 4
ID_BUGREPORT = 5
ID_LEXILOGOS = 6
ID_BAHETH = 7
ID_ALMAANY = 8


class CinBase:
    def __init__(self):
        self.cinbasecurdir = os.path.abspath(os.path.dirname(__file__))
        self.icondir = os.path.join(os.path.dirname(__file__), "icons")
        self.candselKeys = "1234567890"

        self.imeNameList = ["arabic"]

    def initTextService(self, cbTS, TextService):
        cbTS.TextService = TextService
        cbTS.TextService.setSelKeys(cbTS, self.candselKeys)

        cbTS.keyboardLayout = 0
        cbTS.selKeys = "1234567890"
        cbTS.langMode = -1
        cbTS.hidePromptMessages = True
        cbTS.directShowCand = False
        cbTS.directCommitSymbol = False
        cbTS.directCommitSymbolList = ["，", "。", "、", "；", "？", "！"]
        cbTS.bracketSymbolList = ["「」", "『』", "［］", "【】", "〖〗", "〔〕", "﹝﹞", "（）", "﹙﹚", "〈〉", "《》", "＜＞", "﹤﹥", "｛｝",
                                  "﹛﹜"]
        cbTS.directOutMSymbols = True
        cbTS.reLoadTable = False
        cbTS.messageDurationTime = 3

        cbTS.lastKeyDownCode = 0
        cbTS.lastKeyDownTime = 0.0

        cbTS.currentCandPage = 0

        cbTS.tempengcandidates = []
        cbTS.keyUsedState = False
        cbTS.selcandmode = False

        cbTS.initCinBaseState = False
        cbTS.showmenu = False
        cbTS.switchmenu = False
        cbTS.closemenu = True
        cbTS.tempEnglishMode = False
        cbTS.menusymbolsmode = False
        cbTS.ctrlsymbolsmode = False
        cbTS.isSelKeysChanged = False
        cbTS.isLangModeChanged = False
        cbTS.isShowCandidates = False
        cbTS.isShowMessage = False
        cbTS.canSetCommitString = True
        cbTS.canUseSelKey = True
        cbTS.canUseSpaceAsPageKey = True
        cbTS.endKeyList = []
        cbTS.useEndKey = False
        cbTS.lastCommitString = ""
        cbTS.lastCompositionCharLength = 0
        cbTS.resetMenuCand = False
        cbTS.keepComposition = False
        cbTS.keepType = ""

        cbTS.showMessageOnKeyUp = False
        cbTS.hideMessageOnKeyUp = False
        cbTS.onKeyUpMessage = ""
        cbTS.reLoadCinTable = False
        cbTS.capsStates = True if self.getKeyState(VK_CAPITAL) else False

        if DEBUG_MODE:
            cbTS.debug = Debug(cbTS.imeDirName)
            cbTS.debugLog = cbTS.debug.loadDebugLog()

    # When the input method is activated by the user
    def onActivate(self, cbTS):
        cfg = cbTS.cfg
        # Declare to the system that the combination of Shift + Space is of a special purpose
        # When Shift + Space is pressed, onPreservedKey() will be called
        cbTS.addPreservedKey(VK_SPACE, TF_MOD_SHIFT, SHIFT_SPACE_GUID)  # shift + space

        # Switch between arabic and latin
        icon_name = "arabic.ico" if cbTS.langMode == ARABIC_MODE else "latin.ico"
        cbTS.addButton("switch-lang",
                       icon=os.path.join(self.icondir, icon_name),
                       tooltip="Switching language mode",
                       commandId=ID_SWITCH_LANG
                       )

        if cbTS.client.isWindows8Above:
            cbTS.addButton("windows-mode-icon",
                           icon=os.path.join(self.icondir, icon_name),
                           tooltip="Switch language mode",
                           commandId=ID_MODE_ICON
                           )

            # Arabic input is enabled by default at startup
            cbTS.setKeyboardOpen(not cfg.disableOnStartup)

        # Settings
        cbTS.addButton("settings",
                       icon=os.path.join(self.icondir, "config.ico"),
                       tooltip="settings",
                       type="menu"
                       )

    # When the input method is deactivated by the user
    def onDeactivate(self, cbTS):
        cbTS.lastKeyDownCode = 0
        # Announce the removal of the key combination Shift + Space to the system
        cbTS.removePreservedKey(SHIFT_SPACE_GUID)  # shift + space

        cbTS.removeButton("switch-lang")
        cbTS.removeButton("settings")
        if cbTS.client.isWindows8Above:
            cbTS.removeButton("windows-mode-icon")

        if hasattr(cbTS, 'symbols'):
            del cbTS.symbols
        if hasattr(cbTS, 'msymbols'):
            del cbTS.msymbols

    def getCandidates(self, cbTS, keys, step=1):
        candidates = []
        for i in reversed(range(1, len(keys) + 1)):
            charset = cbTS.cin.getCharDef(keys[0:i])
            if charset:
                for char in charset:
                    newCandidates = self.getCandidates(cbTS, keys[i:], i)
                    if newCandidates:
                        for newCandidate in newCandidates:
                            candidates.append(char + newCandidate)
                    else:
                        candidates.append(char)
        return candidates

    # The user presses the keys and filters those keys before the app receives them,
    # which is required by the input method.
    # return True, the system will call onKeyDown() to further process this button.
    # return False, means that we don’t need this key, the system will pass the key to the application intact.
    def filterKeyDown(self, cbTS, keyEvent, CinTable):
        # Record the last key pressed and the time pressed, used in filterKeyUp()
        cbTS.lastKeyDownCode = keyEvent.keyCode
        if cbTS.lastKeyDownTime == 0.0:
            cbTS.lastKeyDownTime = time.time()

        if CinTable.loading:
            return True

        # The user starts to input, the content of the editing area before sending it out is called composition string
        # isComposing() is False, indicating that the editing area is currently empty
        # If you are editing Arabic, we need to send any key to the input method for processing, directly return True
        # In addition, if you use the "`" key to input special symbols, the editing area may be empty
        # But the word selection list is open and the input method needs to be processed
        if cbTS.isComposing() or cbTS.showCandidates:
            return True

        # --------------   The following are "no" Arabic input status   --------------

        # 如果按下 Alt，可能是應用程式熱鍵，輸入法不做處理
        if keyEvent.isKeyDown(VK_MENU):
            if cbTS.isShowMessage:
                cbTS.hideMessageOnKeyUp = True
            return False

        # 如果按下 Ctrl 鍵
        if keyEvent.isKeyDown(VK_CONTROL):
            # 若按下的是指定的符號鍵，輸入法需要處理此按鍵
            if self.isCtrlSymbolsChar(keyEvent.keyCode) and cbTS.langMode == ARABIC_MODE:
                return True
            else:
                if cbTS.isShowMessage:
                    cbTS.hideMessageOnKeyUp = True
                return False

        # 不論中英文模式，NumPad 都允許直接輸入數字，輸入法不處理
        if keyEvent.isKeyToggled(VK_NUMLOCK):  # NumLock is on
            # if this key is Num pad 0-9, +, -, *, /, pass it back to the system
            if VK_NUMPAD0 <= keyEvent.keyCode <= VK_DIVIDE:
                if cbTS.isShowMessage:
                    cbTS.hideMessageOnKeyUp = True
                return False  # bypass IME

        # 如果是英文半形模式，輸入法不做任何處理
        if cbTS.langMode == LATIN_MODE:
            if cbTS.isShowMessage and not keyEvent.isKeyDown(VK_SHIFT):
                cbTS.hideMessageOnKeyUp = True
            return False

        # Check whether the pressed key is keyname list
        if cbTS.cin.isInKeyName(chr(keyEvent.charCode)):
            return True

        # Check whether the pressed key is defined by other keyboards
        if not cbTS.keyboardLayout == 0:
            if chr(keyEvent.charCode) in cbTS.kbtypelist[cbTS.keyboardLayout]:
                return True

        # In Chinese mode, if you press the `key, let the input method process
        if keyEvent.isKeyDown(VK_OEM_3):
            return True

        # The rest of the situation will not be processed,
        # the original key input will be directly returned to the application
        if cbTS.isShowMessage and not keyEvent.isKeyDown(VK_SHIFT):
            cbTS.hideMessageOnKeyUp = True
        return False

    def onKeyDown(self, cbTS, keyEvent, CinTable):
        charCode = keyEvent.charCode
        keyCode = keyEvent.keyCode
        charStr = chr(charCode)

        if CinTable.loading:
            if not cbTS.client.isUiLess:
                messagestr = 'Loading input method code table, please wait...'
                cbTS.isShowMessage = True
                cbTS.showMessage(messagestr, cbTS.messageDurationTime)
            return True

        # NumPad 某些狀況允許輸入法處理
        if keyEvent.isKeyToggled(VK_NUMLOCK):  # NumLock is on
            # if this key is Num pad 0-9, +, -, *, /, pass it back to the system
            if VK_NUMPAD0 <= keyEvent.keyCode <= VK_DIVIDE:
                if cbTS.showCandidates:
                    return True  # bypass IME

        if cbTS.langMode == LATIN_MODE:
            if cbTS.isComposing() or cbTS.showCandidates:
                cbTS.tempEnglishMode = True
        else:
            cbTS.tempEnglishMode = False

        # 鍵盤對映 (注音)
        if not cbTS.keyboardLayout == 0 and charStr in cbTS.kbtypelist[
            cbTS.keyboardLayout] and not cbTS.tempEnglishMode:
            if not keyEvent.isKeyDown(VK_SHIFT) and not keyEvent.isKeyDown(VK_CONTROL):
                charIndex = cbTS.kbtypelist[cbTS.keyboardLayout].index(charStr)
                charStr = cbTS.kbtypelist[0][charIndex]

        cbTS.selKeys = "1234567890"
        if not self.candselKeys == "1234567890":
            self.candselKeys = "1234567890"
            cbTS.TextService.setSelKeys(cbTS, self.candselKeys)
            cbTS.isSelKeysChanged = True

        candidates = []
        cbTS.canSetCommitString = True
        cbTS.keyUsedState = False

        if cbTS.isShowMessage:
            cbTS.isShowMessage = False
            cbTS.hideMessage()

        # 按鍵處理 ----------------------------------------------------------------
        # 某些狀況須要特別處理或忽略
        # 如果輸入編輯區為空且選單未開啟過，不處理 Enter 及 Backspace 鍵
        if not cbTS.isComposing() and cbTS.closemenu:
            if keyCode == VK_RETURN or keyCode == VK_BACK:
                return False

        # 若按下 Shift 鍵,且沒有按下其它的按鍵
        if keyEvent.isKeyDown(VK_SHIFT) and not keyEvent.isPrintableChar():
            return False

        # 若按下 Ctrl 鍵
        if cbTS.langMode == ARABIC_MODE and keyEvent.isKeyDown(VK_CONTROL):
            # If the specified symbol key is pressed, the input method needs to process this key
            if self.isCtrlSymbolsChar(keyCode):
                if cbTS.msymbols.isInCharDef(charStr) and cbTS.closemenu:
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

        if cbTS.ctrlsymbolsmode and keyCode == VK_RETURN and cbTS.isComposing() and not cbTS.showCandidates:
            cbTS.setCommitString(cbTS.compositionString)
            self.resetComposition(cbTS)

        if cbTS.ctrlsymbolsmode and cbTS.directCommitSymbol and not keyEvent.isKeyDown(
                VK_CONTROL) and keyEvent.isPrintableChar():
            if not cbTS.msymbols.isInCharDef(cbTS.compositionChar + charStr) and cbTS.cin.isInKeyName(charStr):
                cbTS.setCommitString(cbTS.compositionString)
                self.resetComposition(cbTS)
                cbTS.keepComposition = True

        # 按下的鍵為 CIN 內有定義的字根
        if cbTS.cin.isInKeyName(
                charStr) and cbTS.closemenu and not keyEvent.isKeyDown(
            VK_CONTROL) and not cbTS.ctrlsymbolsmode and not cbTS.selcandmode and not cbTS.tempEnglishMode:
            if not cbTS.directShowCand and cbTS.showCandidates and self.isInSelKeys(cbTS, charCode):
                # 不送出 CIN 所定義的字根
                cbTS.compositionChar = cbTS.compositionChar
            else:
                if not cbTS.menusymbolsmode:
                    cbTS.compositionChar += charStr
                    keyname = cbTS.cin.getKeyName(charStr)
                    cbTS.setCompositionString(cbTS.compositionString + keyname)
                    cbTS.setCompositionCursor(len(cbTS.compositionString))
                else:
                    cbTS.menusymbolsmode = False

        if cbTS.langMode == ARABIC_MODE and len(cbTS.compositionChar) >= 1:
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
                else:
                    self.resetComposition(cbTS)

            # 刪掉一個字根
            if keyCode == VK_BACK:
                if cbTS.compositionString != "":
                    if cbTS.cin.isInKeyName(cbTS.compositionChar[len(cbTS.compositionChar) - 1:]):
                        keyLength = len(cbTS.cin.getKeyName(cbTS.compositionChar[len(cbTS.compositionChar) - 1:]))
                    else:
                        keyLength = 1
                    cbTS.setCompositionString(cbTS.compositionString[:-keyLength])
                    cbTS.keyUsedState = True

                if cbTS.keyUsedState:
                    cbTS.compositionChar = cbTS.compositionChar[:-1]
                    cbTS.lastCompositionCharLength = cbTS.lastCompositionCharLength - 1
                    cbTS.setCandidateCursor(0)
                    cbTS.setCandidatePage(0)
                    if not cbTS.directShowCand:
                        cbTS.isShowCandidates = False
                        cbTS.setShowCandidates(False)
                    if cbTS.compositionChar == '':
                        self.resetComposition(cbTS)

            # Group word exceeds maximum
            if len(cbTS.compositionChar) > cbTS.maxCharLength:
                if cbTS.cin.isInKeyName(cbTS.compositionChar[len(cbTS.compositionChar) - 1:]):
                    keyLength = len(cbTS.cin.getKeyName(cbTS.compositionChar[len(cbTS.compositionChar) - 1:]))
                else:
                    keyLength = 1
                cbTS.setCompositionString(cbTS.compositionString[:-keyLength])
                cbTS.compositionChar = cbTS.compositionChar[:-1]

            if cbTS.cin.isCharactersInKeyName(cbTS.compositionChar) and cbTS.closemenu and not cbTS.ctrlsymbolsmode:
                candidates = self.getCandidates(cbTS, cbTS.compositionChar)
            elif cbTS.msymbols.isInCharDef(cbTS.compositionChar) and cbTS.closemenu and cbTS.ctrlsymbolsmode:
                candidates = cbTS.msymbols.getCharDef(cbTS.compositionChar)

        if cbTS.selcandmode and cbTS.compositionChar != '':
            candidates = cbTS.tempengcandidates

        # Candidate list processing
        if (cbTS.langMode == ARABIC_MODE and len(cbTS.compositionChar) >= 1) or (
                cbTS.tempEnglishMode and cbTS.isComposing()):
            # If the first character is a symbol, output directly
            if cbTS.directCommitSymbol and not cbTS.tempEnglishMode and not cbTS.selcandmode:
                # If it is code table punctuation
                if cbTS.cin.isInKeyName(cbTS.compositionChar[0]):
                    if cbTS.cin.getKeyName(cbTS.compositionChar[0]) in cbTS.directCommitSymbolList:
                        if not cbTS.cin.isInCharDef(cbTS.compositionChar):
                            if len(cbTS.compositionChar) >= 2 and not cbTS.cin.getKeyName(
                                    cbTS.compositionChar[1]) in cbTS.directCommitSymbolList:
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

            if candidates:
                if not cbTS.selcandmode:
                    if not cbTS.directShowCand:
                        # EndKey 處理 (拼音、注音)
                        if cbTS.useEndKey:
                            if charStr in cbTS.endKeyList and len(cbTS.compositionChar) > 1:
                                if not cbTS.isShowCandidates:
                                    cbTS.isShowCandidates = True
                                    cbTS.canUseSelKey = False
                                else:
                                    cbTS.canUseSelKey = True
                            else:
                                if cbTS.isShowCandidates:
                                    cbTS.canUseSelKey = True

                        cbTS.isShowCandidates = True
                        if keyCode == VK_SPACE:
                            cbTS.canUseSpaceAsPageKey = False
                    else:
                        cbTS.isShowCandidates = True
                        cbTS.canSetCommitString = True

                if cbTS.isShowCandidates:
                    candCursor = cbTS.candidateCursor  # 目前的游標位置
                    candCount = len(cbTS.candidateList)  # 目前選字清單項目數
                    currentCandPageCount = math.ceil(len(candidates) / cbTS.candPerPage)  # 目前的選字清單總頁數
                    currentCandPage = cbTS.currentCandPage  # 目前的選字清單頁數

                    pagecandidates = list(self.chunks(candidates, cbTS.candPerPage))
                    cbTS.setCandidateList(pagecandidates[currentCandPage])

                    if not cbTS.isSelKeysChanged:
                        cbTS.setShowCandidates(True)

                if cbTS.isShowCandidates:
                    # 使用選字鍵執行項目或輸出候選字
                    if self.isInSelKeys(cbTS, charCode) and not keyEvent.isKeyDown(VK_SHIFT) and cbTS.canUseSelKey:
                        i = cbTS.selKeys.index(charStr)
                        if i < cbTS.candPerPage and i < len(cbTS.candidateList):
                            commitStr = cbTS.candidateList[i]
                            cbTS.lastCommitString = commitStr
                            self.setOutputString(cbTS, commitStr)
                            self.resetComposition(cbTS)
                            candCursor = 0
                            currentCandPage = 0

                            if not cbTS.directShowCand:
                                cbTS.canSetCommitString = True
                                cbTS.isShowCandidates = False
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
                    elif (keyCode == VK_RETURN or keyCode == VK_SPACE) and cbTS.canSetCommitString:  # 按下 Enter 鍵或空白鍵
                        commitStr = cbTS.candidateList[candCursor]
                        cbTS.lastCommitString = commitStr
                        self.setOutputString(cbTS, commitStr)
                        self.resetComposition(cbTS)
                        candCursor = 0
                        currentCandPage = 0

                        if not cbTS.directShowCand:
                            cbTS.isShowCandidates = False

                    else:  # 按下其它鍵，先將候選字游標位址及目前頁數歸零
                        if not cbTS.ctrlsymbolsmode:
                            candCursor = 0
                            currentCandPage = 0
                    # 更新選字視窗游標位置及頁數
                    cbTS.setCandidateCursor(candCursor)
                    cbTS.setCandidatePage(currentCandPage)
                    cbTS.setCandidateList(pagecandidates[currentCandPage])
            else:  # No candidates
                # Pressed space or enter
                if (keyCode == VK_SPACE or keyCode == VK_RETURN) and not cbTS.tempEnglishMode:
                    if len(candidates) == 0:
                        if not cbTS.client.isUiLess:
                            cbTS.isShowMessage = True
                            cbTS.showMessage("Check no group words 1...", cbTS.messageDurationTime)
                elif cbTS.useEndKey and charStr in cbTS.endKeyList:
                    if len(candidates) == 0:
                        if not len(cbTS.compositionChar) == 1 and not cbTS.compositionChar == charStr:
                            if not cbTS.client.isUiLess:
                                cbTS.isShowMessage = True
                                cbTS.showMessage("Check no group words 2...", cbTS.messageDurationTime)

                cbTS.setShowCandidates(False)
                cbTS.isShowCandidates = False

        if cbTS.langMode == ARABIC_MODE and cbTS.isComposing() and not cbTS.showCandidates:
            if cbTS.closemenu and not cbTS.selcandmode:
                if keyCode == VK_RETURN:
                    if cbTS.cin.isInKeyName(cbTS.compositionChar) and len(
                            cbTS.compositionChar) == 1 and self.isSymbolsAndNumberChar(cbTS.compositionChar):
                        cbTS.setCommitString(cbTS.compositionString)
                        self.resetComposition(cbTS)

        if not cbTS.canUseSpaceAsPageKey:
            cbTS.canUseSpaceAsPageKey = True

        if not cbTS.closemenu:
            cbTS.closemenu = True

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

        if cbTS.isSelKeysChanged:
            return True

        if cbTS.showMessageOnKeyUp:
            return True

        if cbTS.hideMessageOnKeyUp:
            return True

        return False

    def onKeyUp(self, cbTS, keyEvent):
        keyCode = keyEvent.keyCode
        cbTS.lastKeyDownCode = 0
        cbTS.lastKeyDownTime = 0.0

        #
        # If you release the Shift key then trigger Switch language mode
        if cbTS.isLangModeChanged and keyCode == VK_SHIFT:
            self.toggleLanguageMode(cbTS)  # Switch between Arabic and Latin mode
            cbTS.isLangModeChanged = False
            cbTS.showmenu = False
            if not cbTS.hidePromptMessages and not cbTS.client.isUiLess:
                message = 'Arabic mode' if cbTS.langMode == ARABIC_MODE else 'Latin mode'
                cbTS.isShowMessage = True
                cbTS.showMessage(message, cbTS.messageDurationTime)
            if cbTS.showCandidates or len(cbTS.compositionChar) > 0:
                self.resetComposition(cbTS)

        # If you release the CapsLock key
        if keyEvent.keyCode == VK_CAPITAL:
            self.updateLangButtons(cbTS)

        if cbTS.isSelKeysChanged:
            cbTS.setCandidateList(cbTS.candidateList)
            if cbTS.isShowCandidates:
                cbTS.setShowCandidates(True)
            cbTS.isSelKeysChanged = False

        if cbTS.showMessageOnKeyUp:
            if not cbTS.onKeyUpMessage == "" and not cbTS.client.isUiLess:
                cbTS.showMessage(cbTS.onKeyUpMessage, cbTS.messageDurationTime)
            cbTS.showMessageOnKeyUp = False
            cbTS.onKeyUpMessage = ""

        if cbTS.hideMessageOnKeyUp:
            cbTS.hideMessage()
            cbTS.isShowMessage = False
            cbTS.hideMessageOnKeyUp = False

    def onPreservedKey(self, cbTS, guid):
        cbTS.lastKeyDownCode = 0
        # some preserved keys registered are pressed
        return False

    def onCommand(self, cbTS, commandId, commandType):
        if commandId == ID_SWITCH_LANG and commandType == 0:  # Switch between Arabic and Latin mode
            self.toggleLanguageMode(cbTS)
        elif commandId == ID_MODE_ICON:  # windows 8 mode icon
            self.toggleLanguageMode(cbTS)
        elif commandId == ID_WEBSITE:
            os.startfile("https://github.com/ArabicIME/arabic-ime")
        elif commandId == ID_BUGREPORT:
            os.startfile("https://github.com/ArabicIME/arabic-ime/issues")
        elif commandId == ID_LEXILOGOS:
            os.startfile("https://www.lexilogos.com/english/arabic_dictionary.htm")
        elif commandId == ID_BAHETH:
            os.startfile("http://www.baheth.info")
        elif commandId == ID_ALMAANY:
            os.startfile("https://www.almaany.com/en/dict/ar-en/")

    def onMenu(self, cbTS, buttonId):
        # (windows 8 mode icon)
        if buttonId == "settings" or buttonId == "windows-mode-icon":
            return [
                {"text": "ArabicIME (&W)", "id": ID_WEBSITE},
                {},
                {"text": "ArabicIME Bug Report (&B)", "id": ID_BUGREPORT},
                {},
                {"text": "Dictionaries (&D)", "submenu": [
                    {"text": "Lexilogos", "id": ID_LEXILOGOS},
                    {},
                    {"text": "الباحِثُ العَرَبيُّ", "id": ID_BAHETH},
                    {"text": "المَعاني", "id": ID_ALMAANY},
                ]},
            ]
        return None

    # 鍵盤開啟/關閉時會被呼叫 (在 Windows 10 Ctrl+Space 時)
    def onKeyboardStatusChanged(self, cbTS, opened):
        if opened:  # 鍵盤開啟
            self.resetComposition(cbTS)
        else:  # 鍵盤關閉，輸入法停用
            self.resetComposition(cbTS)

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

        if cbTS.keepComposition:
            cbTS.keepComposition = False

            if cbTS.keepType != "":
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
            cbTS.setCompositionCursor(len(cbTS.compositionString))

    # 切換中英文模式
    def toggleLanguageMode(self, cbTS):
        if cbTS.langMode == ARABIC_MODE:
            cbTS.langMode = LATIN_MODE
        elif cbTS.langMode == LATIN_MODE:
            cbTS.langMode = ARABIC_MODE
        self.updateLangButtons(cbTS)

    def updateLangButtons(self, cbTS):
        icon_name = "arabic.ico" if cbTS.langMode == ARABIC_MODE else "latin.ico"
        icon_path = os.path.join(self.icondir, icon_name)
        cbTS.changeButton("switch-lang", icon=icon_path)
        cbTS.capsStates = True if self.getKeyState(VK_CAPITAL) else False
        icon_path = os.path.join(self.icondir, icon_name)

        if cbTS.client.isWindows8Above:  # windows 8 mode icon
            cbTS.changeButton("windows-mode-icon", icon=icon_path)

    def resetComposition(self, cbTS):
        cbTS.compositionChar = ''
        cbTS.setCompositionString('')
        cbTS.isShowCandidates = False
        cbTS.setCandidateCursor(0)
        cbTS.setCandidatePage(0)
        cbTS.setCandidateList([])
        cbTS.setShowCandidates(False)
        cbTS.menusymbolsmode = False
        cbTS.ctrlsymbolsmode = False
        cbTS.keepComposition = False
        cbTS.selcandmode = False
        cbTS.lastCompositionCharLength = 0

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
        return (ord(char) >= 33 and ord(char) <= 64) or (ord(char) >= 91 and ord(char) <= 96) or (
                ord(char) >= 123 and ord(char) <= 126)

    # 判斷選字鍵?
    def isInSelKeys(self, cbTS, charCode):
        for key in cbTS.selKeys:
            if ord(key) == charCode:
                return True
        return False

    # List 分段
    def chunks(self, l, n):
        for i in range(0, len(l), n):
            yield l[i:i + n]

    def getKeyState(self, keyCode):
        return ctypes.WinDLL("User32.dll").GetKeyState(keyCode)

    def setOutputString(self, cbTS, commitStr):
        cbTS.setCommitString(commitStr)

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

    ################################################################
    # config 相關
    ################################################################
    # 初始化 CinBase 輸入法引擎
    def initCinBaseContext(self, cbTS):
        cfg = cbTS.cfg  # 所有 TextService 共享一份設定物件

        if not cbTS.initCinBaseState:
            # 預設英數 or 中文模式
            cbTS.langMode = LATIN_MODE if cfg.defaultLatin else ARABIC_MODE

            self.updateLangButtons(cbTS)

        cbTS.selCinType = cfg.selCinType

        if hasattr(cbTS, 'symbols'):
            del cbTS.symbols
        if hasattr(cbTS, 'msymbols'):
            del cbTS.msymbols

        self.applyConfig(cbTS)  # 套用其餘的使用者設定

        datadirs = (cfg.getConfigDir(), cfg.getDataDir())
        symbolsPath = cfg.findFile(datadirs, "symbols.dat")
        with io.open(symbolsPath, 'r', encoding='utf-8') as fs:
            cbTS.symbols = symbols(fs)

        msymbolsPath = cfg.findFile(datadirs, "msymbols.json")
        with io.open(msymbolsPath, 'r', encoding='utf-8') as fs:
            cbTS.msymbols = msymbols(fs)

        cbTS.initCinBaseState = True

    def applyConfig(self, cbTS):
        cfg = cbTS.cfg  # All TextService share a configuration object
        cbTS.configVersion = cfg.getVersion()

        # Number of candidates in each column
        cbTS.candPerRow = cfg.candPerRow

        # If the program is in UiLess mode, replace the setting
        if cbTS.client.isUiLess:
            cbTS.candPerRow = 1

        # Number of candidates per page
        cbTS.candPerPage = cfg.candPerPage

        # Set UI appearance
        cbTS.customizeUI(candFontSize=cfg.fontSize,
                         candFontName='Segoe UI',
                         candPerRow=cfg.candPerRow,
                         candUseCursor=cfg.cursorCandList)

        # Set word selection buttons (123456..., asdf.... etc.)
        # if cbTS.cin.getSelection():
        #     cbTS.setSelKeys(cbTS.cin.getSelection())

        # 提示訊息顯示時間?
        cbTS.messageDurationTime = cfg.messageDurationTime

        # 隱藏提示訊息?
        cbTS.hidePromptMessages = cfg.hidePromptMessages

        # Directly display the candidate list (no need to press the blank key)?
        cbTS.directShowCand = cfg.directShowCand

        # 標點符號自動確認輸入?
        cbTS.directCommitSymbol = cfg.directCommitSymbol

        # 允許內建符號輸入方式連續輸入?
        cbTS.directOutMSymbols = cfg.directOutMSymbols

        # 最大候選字個數?
        cbTS.candMaxItems = cfg.candMaxItems

        # 擴充碼表?
        cbTS.reLoadTable = cfg.reLoadTable

        # 訊息顯示時間?
        cbTS.messageDurationTime = cfg.messageDurationTime

    # 檢查設定檔是否有被更改，是否需要套用新設定
    def checkConfigChange(self, cbTS, CinTable):
        cfg = cbTS.cfg  # 所有 TextService 共享一份設定物件
        cfg.update()  # 更新設定檔狀態
        reLoadCinTable = False

        # If the input method code table is changed, reload the code table data
        if not CinTable.loading:
            if not CinTable.curCinType == cfg.selCinType:
                reLoadCinTable = True

            if cfg.reLoadTable:
                reLoadCinTable = True
                cfg.reLoadTable = False
                cfg.save()

        # 比較我們先前存的版本號碼，和目前設定檔的版本號
        if cfg.isFullReloadNeeded(cbTS.configVersion):
            # 資料改變需整個 reload，重建一個新的 checj context
            self.initCinBaseContext(cbTS)
        elif cfg.isConfigChanged(cbTS.configVersion):
            # 只有偵測到設定檔變更，需要套用新設定
            self.applyConfig(cbTS)

        if reLoadCinTable:
            datadirs = (cfg.getConfigDir(), cfg.getDataDir())
            if reLoadCinTable:
                cbTS.reLoadCinTable = True
            loadCinFile = LoadCinTable(cbTS, CinTable)
            loadCinFile.start()
        else:
            if not cbTS.cin == CinTable.cin:
                cbTS.cin = CinTable.cin

        if DEBUG_MODE:
            if not cbTS.debugLog == cbTS.debug.debugLog:
                if not CinTable.loading:
                    cbTS.debug.saveDebugLog(cbTS.debugLog)


CinBase = CinBase()


class LoadCinTable(threading.Thread):
    def __init__(self, cbTS, CinTable):
        threading.Thread.__init__(self)
        self.cbTS = cbTS
        self.CinTable = CinTable

    def run(self):
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
                self.cbTS.cin = Cin(fs, self.cbTS.imeDirName)
            self.CinTable.cin = self.cbTS.cin
            self.CinTable.curCinType = self.cbTS.cfg.selCinType

        self.CinTable.loading = False
