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
import math
import copy
import ctypes
import winsound
from .swkb import swkb
from .symbols import symbols
from .dsymbols import dsymbols
from .fsymbols import fsymbols
from .msymbols import msymbols
from .flangs import flangs
from .phrase import phrase
from .userphrase import userphrase
from .emoji import emoji

CHINESE_MODE = 1
ENGLISH_MODE = 0
FULLSHAPE_MODE = 1
HALFSHAPE_MODE = 0

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
        self.emoji = emoji
        self.emojimenulist = ["表情符號", "圖形符號", "其它符號", "雜錦符號", "交通運輸", "調色盤"]


    # 初始化輸入行為設定
    def initTextService(self, CinBaseTextService, TextService):
        CinBaseTextService.TextService = TextService
        CinBaseTextService.TextService.setSelKeys(CinBaseTextService, self.candselKeys)
        # 使用 OpenCC 繁體中文轉簡體
        CinBaseTextService.opencc = None

        CinBaseTextService.keyboardLayout = 0
        CinBaseTextService.selKeys = "1234567890"
        CinBaseTextService.langMode = -1
        CinBaseTextService.shapeMode = -1
        CinBaseTextService.switchPageWithSpace = False
        CinBaseTextService.outputSimpChinese = False
        CinBaseTextService.hidePromptMessages = True
        CinBaseTextService.autoClearCompositionChar = False
        CinBaseTextService.playSoundWhenNonCand = False
        CinBaseTextService.directShowCand = False
        CinBaseTextService.directCommitString = False
        CinBaseTextService.directCommitSymbol = False
        CinBaseTextService.fullShapeSymbols = False
        CinBaseTextService.easySymbolsWithShift = False
        CinBaseTextService.supportSymbolCoding = False
        CinBaseTextService.showPhrase = False
        CinBaseTextService.sortByPhrase = False
        CinBaseTextService.lastKeyDownCode = 0
        CinBaseTextService.lastKeyDownTime = 0.0

        CinBaseTextService.menucandidates = []
        CinBaseTextService.smenucandidates = []
        CinBaseTextService.wildcardcandidates = []
        CinBaseTextService.wildcardpagecandidates = []
        CinBaseTextService.wildcardcompositionChar = ""
        CinBaseTextService.currentCandPage = 0

        CinBaseTextService.emojitype = 0
        CinBaseTextService.prevmenutypelist = []
        CinBaseTextService.prevmenucandlist = []

        CinBaseTextService.showmenu = False
        CinBaseTextService.switchmenu = False
        CinBaseTextService.closemenu = True
        CinBaseTextService.multifunctionmode = False
        CinBaseTextService.emojimenumode = False
        CinBaseTextService.ctrlsymbolsmode = False
        CinBaseTextService.phrasemode = False
        CinBaseTextService.isSelKeysChanged = False
        CinBaseTextService.isWildcardChardefs = False
        CinBaseTextService.isLangModeChanged = False
        CinBaseTextService.isShapeModeChanged = False
        CinBaseTextService.isShowCandidates = False
        CinBaseTextService.isShowPhraseCandidates = False
        CinBaseTextService.canSetCommitString = True
        CinBaseTextService.canUseSelKey = True
        CinBaseTextService.canUseSpaceAsPageKey = True
        CinBaseTextService.endKeyList = []
        CinBaseTextService.useEndKey = False
        CinBaseTextService.useDayiSymbols = False
        CinBaseTextService.dayisymbolsmode = False
        CinBaseTextService.autoShowCandWhenMaxChar = False
        CinBaseTextService.lastCommitString = ""
        CinBaseTextService.lastCompositionCharLength = 0
        CinBaseTextService.menutype = 0
        CinBaseTextService.resetMenuCand = False
        CinBaseTextService.capsStates = True if self.getKeyState(VK_CAPITAL) else False


    # 輸入法被使用者啟用
    def onActivate(self, CinBaseTextService):
        # 向系統宣告 Shift + Space 這個組合為特殊用途 (全半形切換)
        # 當 Shift + Space 被按下的時候，onPreservedKey() 會被呼叫
        CinBaseTextService.addPreservedKey(VK_SPACE, TF_MOD_SHIFT, SHIFT_SPACE_GUID); # shift + space

        # 切換中英文
        icon_name = "chi.ico" if CinBaseTextService.langMode == CHINESE_MODE else "eng.ico"
        CinBaseTextService.addButton("switch-lang",
            icon=os.path.join(self.icondir, icon_name),
            tooltip="中英文切換",
            commandId=ID_SWITCH_LANG
        )

        # Windows 8 以上已取消語言列功能，改用 systray IME mode icon
        if CinBaseTextService.client.isWindows8Above:
            if CinBaseTextService.langMode == CHINESE_MODE:
                if CinBaseTextService.shapeMode == FULLSHAPE_MODE:
                    icon_name = "chi_full_capson.ico" if CinBaseTextService.capsStates else "chi_full_capsoff.ico"
                else:
                    icon_name = "chi_half_capson.ico" if CinBaseTextService.capsStates else "chi_half_capsoff.ico"
            else:
                if CinBaseTextService.shapeMode == FULLSHAPE_MODE:
                    icon_name = "eng_full_capson.ico" if CinBaseTextService.capsStates else "eng_full_capsoff.ico"
                else:
                    icon_name = "eng_half_capson.ico" if CinBaseTextService.capsStates else "eng_half_capsoff.ico"
            
            CinBaseTextService.addButton("windows-mode-icon",
                icon=os.path.join(self.icondir, icon_name),
                tooltip="中英文切換",
                commandId=ID_MODE_ICON
            )
            
        # 切換全半形
        icon_name = "full.ico" if CinBaseTextService.shapeMode == FULLSHAPE_MODE else "half.ico"
        CinBaseTextService.addButton("switch-shape",
            icon = os.path.join(self.icondir, icon_name),
            tooltip = "全形/半形切換",
            commandId = ID_SWITCH_SHAPE
        )
        
        # 設定
        CinBaseTextService.addButton("settings",
            icon = os.path.join(self.icondir, "config.ico"),
            tooltip = "設定",
            type = "menu"
        )


    # 使用者離開輸入法
    def onDeactivate(self, CinBaseTextService):
        CinBaseTextService.lastKeyDownCode = 0
        # 向系統宣告移除 Shift + Space 這個組合鍵用途 (全半形切換)
        CinBaseTextService.removePreservedKey(SHIFT_SPACE_GUID); # shift + space
        
        CinBaseTextService.removeButton("switch-lang")
        CinBaseTextService.removeButton("switch-shape")
        CinBaseTextService.removeButton("settings")
        if CinBaseTextService.client.isWindows8Above:
            CinBaseTextService.removeButton("windows-mode-icon")


    # 使用者按下按鍵，在 app 收到前先過濾那些鍵是輸入法需要的。
    # return True，系統會呼叫 onKeyDown() 進一步處理這個按鍵
    # return False，表示我們不需要這個鍵，系統會原封不動把按鍵傳給應用程式
    def filterKeyDown(self, CinBaseTextService, keyEvent):
        # 紀錄最後一次按下的鍵和按下的時間，在 filterKeyUp() 中要用
        CinBaseTextService.lastKeyDownCode = keyEvent.keyCode
        if CinBaseTextService.lastKeyDownTime == 0.0:
            CinBaseTextService.lastKeyDownTime = time.time()

        # 使用者開始輸入，還沒送出前的編輯區內容稱 composition string
        # isComposing() 是 False，表示目前編輯區是空的
        # 若正在編輯中文，則任何按鍵我們都需要送給輸入法處理，直接 return True
        # 另外，若使用 "`" key 輸入特殊符號，可能會有編輯區是空的
        # 但選字清單開啟，輸入法需要處理的情況
        if CinBaseTextService.isComposing() or CinBaseTextService.showCandidates:
            return True
        # --------------   以下都是「沒有」正在輸入中文的狀況   --------------

        # 如果按下 Alt，可能是應用程式熱鍵，輸入法不做處理
        if keyEvent.isKeyDown(VK_MENU):
            return False

        # 如果按下 Ctrl 鍵
        if keyEvent.isKeyDown(VK_CONTROL):
            # 若按下的是指定的符號鍵，輸入法需要處理此按鍵
            if self.isCtrlSymbolsChar(keyEvent.keyCode) and CinBaseTextService.langMode == CHINESE_MODE:
                return True
            else:
                return False

        # 若按下 Shift 鍵
        if keyEvent.isKeyDown(VK_SHIFT):
            if CinBaseTextService.langMode == CHINESE_MODE and not keyEvent.isKeyDown(VK_CONTROL):
                # 若開啟 Shift 快速輸入符號，輸入法需要處理此按鍵
                if CinBaseTextService.easySymbolsWithShift and self.isLetterChar(keyEvent.keyCode):
                    return True
                # 若開啟 Shift 輸入全形標點，輸入法需要處理此按鍵
                if CinBaseTextService.fullShapeSymbols and (self.isSymbolsChar(keyEvent.keyCode) or self.isNumberChar(keyEvent.keyCode)):
                    return True
                # 若萬用字元使用*，輸入法需要處理*按鍵
                if CinBaseTextService.selWildcardChar == '*' and keyEvent.keyCode == 0x38:
                    return True

        # 不論中英文模式，NumPad 都允許直接輸入數字，輸入法不處理
        if keyEvent.isKeyToggled(VK_NUMLOCK): # NumLock is on
            # if this key is Num pad 0-9, +, -, *, /, pass it back to the system
            if keyEvent.keyCode >= VK_NUMPAD0 and keyEvent.keyCode <= VK_DIVIDE:
                return False # bypass IME

        # 不管中英文模式，只要是全形可見字元或空白，輸入法都需要進一步處理(半形轉為全形)
        if CinBaseTextService.shapeMode == FULLSHAPE_MODE:
            return (keyEvent.isPrintableChar() or keyEvent.keyCode == VK_SPACE)

        # --------------   以下皆為半形模式   --------------

        # 如果是英文半形模式，輸入法不做任何處理
        if CinBaseTextService.langMode == ENGLISH_MODE:
            return False
        # --------------   以下皆為中文模式   --------------

        # 中文模式下，當中文編輯區是空的，輸入法只需處理倉頡字根
        # 檢查按下的鍵是否為倉頡字根
        if CinBaseTextService.cin.isInKeyName(chr(keyEvent.charCode).lower()):
            return True

        # 中文模式下，當中文編輯區是空的，且不是預設鍵盤,輸入法需處理其它鍵盤所定義的字根
        # 檢查按下的鍵是否為其它鍵盤定義的字根
        if not CinBaseTextService.keyboardLayout == 0:
            if chr(keyEvent.charCode).lower() in CinBaseTextService.kbtypelist[CinBaseTextService.keyboardLayout]:
                return True

        # 中文模式下，若按下 ` 鍵，讓輸入法進行處理
        if keyEvent.isKeyDown(VK_OEM_3):
            return True

        if CinBaseTextService.useDayiSymbols and keyEvent.isKeyDown(VK_OEM_PLUS):
            return True
        
        # 其餘狀況一律不處理，原按鍵輸入直接送還給應用程式
        return False
        
    def onKeyDown(self, CinBaseTextService, keyEvent):
        charCode = keyEvent.charCode
        keyCode = keyEvent.keyCode
        charStr = chr(charCode)
        
        # 不論中英文模式，NumPad 都允許直接輸入數字，輸入法不處理
        if keyEvent.isKeyToggled(VK_NUMLOCK): # NumLock is on
            # if this key is Num pad 0-9, +, -, *, /, pass it back to the system
            if keyEvent.keyCode >= VK_NUMPAD0 and keyEvent.keyCode <= VK_DIVIDE:
                return True # bypass IME

        # 鍵盤對映 (注音)
        if not CinBaseTextService.keyboardLayout == 0 and charStr.lower() in CinBaseTextService.kbtypelist[CinBaseTextService.keyboardLayout]:
            if not keyEvent.isKeyDown(VK_SHIFT) and not keyEvent.isKeyDown(VK_CONTROL):
                charIndex = CinBaseTextService.kbtypelist[CinBaseTextService.keyboardLayout].index(charStr.lower())
                charStr = CinBaseTextService.kbtypelist[0][charIndex]

        # 檢查選字鍵
        if not CinBaseTextService.imeDirName == "chedayi":
            CinBaseTextService.selKeys = "1234567890"
            if not self.candselKeys == "1234567890":
                self.candselKeys = "1234567890"
                CinBaseTextService.TextService.setSelKeys(CinBaseTextService, self.candselKeys)
                CinBaseTextService.isSelKeysChanged = True

        candidates = []
        charStrLow = charStr.lower()
        CinBaseTextService.isWildcardChardefs = False
        CinBaseTextService.canSetCommitString = True
        CinBaseTextService.showMessage("", 0)
        
        if CinBaseTextService.langMode == ENGLISH_MODE:
            if CinBaseTextService.isComposing() or CinBaseTextService.showCandidates:
                CinBaseTextService.setCommitString(charStr)
                self.resetComposition(CinBaseTextService)
                return True
        
        # 多功能前導字元 ---------------------------------------------------------
        if CinBaseTextService.multifunctionmode:
            CinBaseTextService.canUseSelKey = True
            
        if CinBaseTextService.langMode == CHINESE_MODE and not CinBaseTextService.showmenu:
            if len(CinBaseTextService.compositionChar) == 0 and charStr == '`' and not CinBaseTextService.imeDirName == "cheez":
                CinBaseTextService.compositionChar += charStr
                CinBaseTextService.setCompositionString(CinBaseTextService.compositionChar)
                if not CinBaseTextService.hidePromptMessages:
                    messagestr = '多功能前導字元'
                    CinBaseTextService.showMessage(messagestr, 5)
                CinBaseTextService.multifunctionmode = True
            elif len(CinBaseTextService.compositionChar) == 1 and CinBaseTextService.multifunctionmode:
                if charStrLow == 'm':
                    CinBaseTextService.compositionChar = ''
                    CinBaseTextService.setCompositionString('')
                    CinBaseTextService.multifunctionmode = False
                    CinBaseTextService.closemenu = False
                elif charStrLow == 'u':
                    CinBaseTextService.compositionChar += charStr.upper()
                    CinBaseTextService.setCompositionString(CinBaseTextService.compositionChar)
                elif charStrLow == 'e':
                    CinBaseTextService.compositionChar = ''
                    CinBaseTextService.setCompositionString('')
                    CinBaseTextService.multifunctionmode = False
                    CinBaseTextService.closemenu = False
                    CinBaseTextService.emojimenumode = True
                elif self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode):
                    if self.isNumberChar(keyCode):
                        CinBaseTextService.canUseSelKey = False
                    CinBaseTextService.compositionChar += charStr
            elif len(CinBaseTextService.compositionChar) > 1 and CinBaseTextService.multifunctionmode:
                if CinBaseTextService.msymbols.isInCharDef(CinBaseTextService.compositionChar[1:] + charStr):
                    CinBaseTextService.compositionChar += charStr
                elif CinBaseTextService.compositionChar[:2] == '`U':
                    if keyCode >= 0x30 and keyCode <= 0x46:
                        CinBaseTextService.compositionChar += charStr.upper()
                        CinBaseTextService.setCompositionString(CinBaseTextService.compositionChar)
                elif CinBaseTextService.compositionChar[:2] == '``':
                    if keyCode == VK_OEM_3:
                        CinBaseTextService.compositionChar += charStr
                    
            if len(CinBaseTextService.compositionChar) == 3 and CinBaseTextService.multifunctionmode:
                if CinBaseTextService.compositionChar == '```':
                    CinBaseTextService.compositionChar = ''
                    CinBaseTextService.setCompositionString('')
                    CinBaseTextService.multifunctionmode = False
                    CinBaseTextService.closemenu = False

        if CinBaseTextService.multifunctionmode:
            # 按下 ESC 鍵
            if keyCode == VK_ESCAPE and (CinBaseTextService.showCandidates or len(CinBaseTextService.compositionChar) > 0):
                self.resetComposition(CinBaseTextService)
                return True

            # 刪掉一個字根
            if keyCode == VK_BACK:
                if CinBaseTextService.compositionString != '':
                    CinBaseTextService.setCompositionString(CinBaseTextService.compositionString[:-1])
                    CinBaseTextService.compositionChar = CinBaseTextService.compositionChar[:-1]
                    CinBaseTextService.setCandidateCursor(0)
                    CinBaseTextService.setCandidatePage(0)
                    if CinBaseTextService.compositionString == '':
                        self.resetComposition(CinBaseTextService)
                        return True

            # Unicode 編碼字元超過 5 + 2 個
            if CinBaseTextService.compositionChar[:2] == '`U' and len(CinBaseTextService.compositionChar) > 7:
                CinBaseTextService.setCompositionString(CinBaseTextService.compositionString[:-1])
                CinBaseTextService.compositionChar = CinBaseTextService.compositionChar[:-1]

            # 按下的鍵為微軟有定義的字根
            if CinBaseTextService.msymbols.isInCharDef(CinBaseTextService.compositionChar[1:]) and CinBaseTextService.closemenu and len(CinBaseTextService.compositionChar) >= 2:
                candidates = CinBaseTextService.msymbols.getCharDef(CinBaseTextService.compositionChar[1:])
                CinBaseTextService.setCompositionString(candidates[0])

        # 輕鬆輸入法進入選單模式
        if CinBaseTextService.imeDirName == "cheez" and CinBaseTextService.compositionChar + charStrLow == 'menu':
            CinBaseTextService.compositionChar = ''
            CinBaseTextService.setCompositionString('')
            CinBaseTextService.multifunctionmode = False
            CinBaseTextService.closemenu = False

        # 功能選單 ----------------------------------------------------------------
        if CinBaseTextService.langMode == CHINESE_MODE and len(CinBaseTextService.compositionChar) == 0:
            menu_OutputSimpChinese = "輸出繁體" if CinBaseTextService.outputSimpChinese else "輸出簡體"
            menu_fullShapeSymbols = "☑ Shift 輸入全形標點" if CinBaseTextService.fullShapeSymbols else "☐ Shift 輸入全形標點"
            menu_easySymbolsWithShift = "☑ Shift 快速輸入符號" if CinBaseTextService.easySymbolsWithShift else "☐ Shift 快速輸入符號"
            menu_supportSymbolCoding = "☑ Cin 碼表的符號編碼" if CinBaseTextService.supportSymbolCoding else "☐ Cin 碼表的符號編碼"
            menu_supportWildcard = "☑ 以萬用字元代替組字字根" if CinBaseTextService.supportWildcard else "☐ 以萬用字元代替組字字根"
            menu_autoClearCompositionChar = "☑ 拆錯字碼時自動清除輸入字串" if CinBaseTextService.autoClearCompositionChar else "☐ 拆錯字碼時自動清除輸入字串"
            menu_playSoundWhenNonCand = "☑ 拆錯字碼時發出警告嗶聲提示" if CinBaseTextService.playSoundWhenNonCand else "☐ 拆錯字碼時發出警告嗶聲提示"
            menu_showPhrase = "☑ 輸出字串後顯示聯想字詞" if CinBaseTextService.showPhrase else "☐ 輸出字串後顯示聯想字詞"
            menu_sortByPhrase = "☑ 優先以聯想字詞排序候選清單" if CinBaseTextService.sortByPhrase else "☐ 優先以聯想字詞排序候選清單"

            if CinBaseTextService.imeDirName == "chephonetic":
                CinBaseTextService.smenucandidates = [menu_fullShapeSymbols, menu_easySymbolsWithShift, menu_autoClearCompositionChar, menu_playSoundWhenNonCand, menu_showPhrase, menu_sortByPhrase]
                CinBaseTextService.smenuitems =  ["fullShapeSymbols", "easySymbolsWithShift", "autoClearCompositionChar", "playSoundWhenNonCand", "showPhrase", "sortByPhrase"]
            elif CinBaseTextService.imeDirName == "cheez":
                CinBaseTextService.smenucandidates = [menu_supportWildcard, menu_autoClearCompositionChar, menu_playSoundWhenNonCand, menu_showPhrase, menu_sortByPhrase]
                CinBaseTextService.smenuitems = ["supportWildcard", "autoClearCompositionChar", "playSoundWhenNonCand", "showPhrase", "sortByPhrase"]
            elif CinBaseTextService.imeDirName == "chearray" or CinBaseTextService.imeDirName == "chedayi":
                CinBaseTextService.smenucandidates = [menu_fullShapeSymbols, menu_easySymbolsWithShift, menu_supportWildcard, menu_autoClearCompositionChar, menu_playSoundWhenNonCand, menu_showPhrase, menu_sortByPhrase]
                CinBaseTextService.smenuitems = ["fullShapeSymbols", "easySymbolsWithShift", "supportWildcard", "autoClearCompositionChar", "playSoundWhenNonCand", "showPhrase", "sortByPhrase"]
            else:
                CinBaseTextService.smenucandidates = [menu_fullShapeSymbols, menu_easySymbolsWithShift, menu_supportSymbolCoding, menu_supportWildcard, menu_autoClearCompositionChar, menu_playSoundWhenNonCand, menu_showPhrase, menu_sortByPhrase]
                CinBaseTextService.smenuitems = ["fullShapeSymbols", "easySymbolsWithShift", "supportSymbolCoding", "supportWildcard", "autoClearCompositionChar", "playSoundWhenNonCand", "showPhrase", "sortByPhrase"]

            if not CinBaseTextService.closemenu:
                CinBaseTextService.setCandidateCursor(0)
                CinBaseTextService.setCandidatePage(0)
                
                # 大易須更換選字鍵
                if CinBaseTextService.imeDirName == "chedayi":
                    CinBaseTextService.selKeys = "1234567890"
                    if not self.candselKeys == "1234567890":
                        self.candselKeys = "1234567890"
                        CinBaseTextService.TextService.setSelKeys(CinBaseTextService, self.candselKeys)
                        CinBaseTextService.isShowCandidates = True
                        CinBaseTextService.isSelKeysChanged = True

                if not CinBaseTextService.emojimenumode:
                    CinBaseTextService.menutype = 0
                    menu = ["功能設定", menu_OutputSimpChinese, "功能開關", "特殊符號", "注音符號", "外語文字", "表情符號"]
                    CinBaseTextService.setCandidateList(menu)
                else:
                    CinBaseTextService.menutype = 7
                    CinBaseTextService.setCandidateList(self.emojimenulist)
                    
                CinBaseTextService.menucandidates = CinBaseTextService.candidateList
                CinBaseTextService.prevmenutypelist = []
                CinBaseTextService.prevmenucandlist = []
                CinBaseTextService.showmenu = True

            if CinBaseTextService.showmenu:
                CinBaseTextService.closemenu = False
                candidates = CinBaseTextService.menucandidates
                candCursor = CinBaseTextService.candidateCursor  # 目前的游標位置
                candCount = len(CinBaseTextService.candidateList)  # 目前選字清單項目數
                currentCandPageCount = math.ceil(len(candidates) / CinBaseTextService.candPerPage) # 目前的選字清單總頁數
                currentCandPage = CinBaseTextService.currentCandPage # 目前的選字清單頁數
                
                # 候選清單分頁
                pagecandidates = list(self.chunks(candidates, CinBaseTextService.candPerPage))
                CinBaseTextService.setCandidateList(pagecandidates[currentCandPage])
                if not CinBaseTextService.isSelKeysChanged:
                    CinBaseTextService.setShowCandidates(True)
                CinBaseTextService.resetMenuCand = False
                itemName = ""

                # 選單按鍵處理
                if keyCode == VK_UP:  # 游標上移
                    if (candCursor - CinBaseTextService.candPerRow) < 0:
                        if currentCandPage > 0:
                            currentCandPage -= 1
                            candCursor = 0
                    else:
                        if (candCursor - CinBaseTextService.candPerRow) >= 0:
                            candCursor = candCursor - CinBaseTextService.candPerRow
                elif keyCode == VK_DOWN:  # 游標下移
                    if (candCursor + CinBaseTextService.candPerRow) >= CinBaseTextService.candPerPage:
                        if (currentCandPage + 1) < currentCandPageCount:
                            currentCandPage += 1
                            candCursor = 0
                    else:
                        if (candCursor + CinBaseTextService.candPerRow) < len(pagecandidates[currentCandPage]):
                            candCursor = candCursor + CinBaseTextService.candPerRow
                elif keyCode == VK_LEFT:  # 游標左移
                    if candCursor > 0:
                        candCursor -= 1
                elif keyCode == VK_RIGHT:  # 游標右移
                    if (candCursor + 1) < candCount:
                        candCursor += 1
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
                    CinBaseTextService.showmenu = False
                    CinBaseTextService.emojimenumode = False
                    CinBaseTextService.menutype = 0
                    CinBaseTextService.prevmenutypelist = []
                    CinBaseTextService.prevmenucandlist = []
                    self.resetComposition(CinBaseTextService)
                elif self.isInSelKeys(CinBaseTextService, charCode) and not keyEvent.isKeyDown(VK_SHIFT): # 使用選字鍵執行項目或輸出候選字
                    if CinBaseTextService.selKeys.index(charStr) < CinBaseTextService.candPerPage and CinBaseTextService.selKeys.index(charStr) < len(CinBaseTextService.candidateList):
                        candCursor = CinBaseTextService.selKeys.index(charStr)
                        itemName = CinBaseTextService.candidateList[candCursor]
                        CinBaseTextService.switchmenu = True
                elif keyCode == VK_RETURN:  # 按下 Enter 鍵
                    itemName = CinBaseTextService.candidateList[candCursor]
                    CinBaseTextService.switchmenu = True
                elif keyCode == VK_SPACE: # 按下空白鍵
                    if CinBaseTextService.switchPageWithSpace and currentCandPageCount > 1:
                        if (currentCandPage + 1) < currentCandPageCount:
                            currentCandPage += 1
                            candCursor = 0
                        else:
                            currentCandPage = 0
                            candCursor = 0
                    else:
                        itemName = CinBaseTextService.candidateList[candCursor]
                        CinBaseTextService.switchmenu = True
                elif keyCode == VK_BACK:
                    if CinBaseTextService.prevmenutypelist:
                        prevmenulist =[]
                        prevmenutype = len(CinBaseTextService.prevmenutypelist) - 1
                        prevmenulist = CinBaseTextService.prevmenutypelist[prevmenutype].split(',', 2)
                        CinBaseTextService.menutype = int(prevmenulist[0], 10)
                        CinBaseTextService.prevmenucandlist = []
                        CinBaseTextService.prevmenucandlist.append(int(prevmenulist[1], 10))
                        CinBaseTextService.prevmenucandlist.append(int(prevmenulist[2], 10))
                        CinBaseTextService.prevmenutypelist.remove(CinBaseTextService.prevmenutypelist[prevmenutype])
                        pagecandidates = self.switchMenuCand(CinBaseTextService, CinBaseTextService.menutype)

                # 選單切換及執行
                if CinBaseTextService.switchmenu and not itemName == "":
                    CinBaseTextService.switchmenu = False
                    if CinBaseTextService.menutype == 0 and itemName == "功能開關": # 切至功能開關頁面
                        CinBaseTextService.menucandidates = CinBaseTextService.smenucandidates
                        pagecandidates = list(self.chunks(CinBaseTextService.menucandidates, CinBaseTextService.candPerPage))
                        CinBaseTextService.resetMenuCand = self.switchMenuType(CinBaseTextService, 1, ["0," + str(candCursor) + "," + str(currentCandPage)])
                    elif CinBaseTextService.menutype == 0 and itemName == "特殊符號": # 切至特殊符號頁面
                        CinBaseTextService.menucandidates = CinBaseTextService.symbols.getKeyNames()
                        pagecandidates = list(self.chunks(CinBaseTextService.menucandidates, CinBaseTextService.candPerPage))
                        CinBaseTextService.resetMenuCand = self.switchMenuType(CinBaseTextService, 2, ["0," + str(candCursor) + "," + str(currentCandPage)])
                    elif CinBaseTextService.menutype == 0 and itemName == "注音符號": # 切至注音符號頁面
                        bopomofolist = []
                        for i in range(0x3105,0x311A):
                            bopomofolist.append(chr(i))
                        for i in range(0x3127,0x312A):
                            bopomofolist.append(chr(i))
                        for i in range(0x311A,0x3127):
                            bopomofolist.append(chr(i))
                        bopomofolist.append(chr(0x02D9))
                        bopomofolist.append(chr(0x02CA))
                        bopomofolist.append(chr(0x02C7))
                        bopomofolist.append(chr(0x02CB))
                        
                        CinBaseTextService.menucandidates = bopomofolist
                        pagecandidates = list(self.chunks(CinBaseTextService.menucandidates, CinBaseTextService.candPerPage))
                        CinBaseTextService.resetMenuCand = self.switchMenuType(CinBaseTextService, 4, ["0," + str(candCursor) + "," + str(currentCandPage)])
                    elif CinBaseTextService.menutype == 0 and itemName == "外語文字": # 切至外語文字頁面
                        CinBaseTextService.menucandidates = CinBaseTextService.flangs.getKeyNames()
                        pagecandidates = list(self.chunks(CinBaseTextService.menucandidates, CinBaseTextService.candPerPage))
                        CinBaseTextService.resetMenuCand = self.switchMenuType(CinBaseTextService, 5, ["0," + str(candCursor) + "," + str(currentCandPage)])
                    elif CinBaseTextService.menutype == 0 and itemName == "表情符號": # 切至表情符號頁面
                        CinBaseTextService.menucandidates = self.emojimenulist
                        pagecandidates = list(self.chunks(CinBaseTextService.menucandidates, CinBaseTextService.candPerPage))
                        if not CinBaseTextService.emojimenumode:
                            CinBaseTextService.resetMenuCand = self.switchMenuType(CinBaseTextService, 7, ["0," + str(candCursor) + "," + str(currentCandPage)])
                        else:
                            CinBaseTextService.resetMenuCand = self.switchMenuType(CinBaseTextService, 7, [])
                    elif CinBaseTextService.menutype == 0: # 執行主頁面其它項目
                        menu = ["功能設定", menu_OutputSimpChinese, "功能開關", "特殊符號", "注音符號", "外語文字", "表情符號"]
                        i = menu.index(itemName)
                        self.onMenuCommand(CinBaseTextService, i, 0)
                        CinBaseTextService.resetMenuCand = self.closeMenuCand(CinBaseTextService)
                    elif CinBaseTextService.menutype == 1: # 執行功能開關頁面項目
                        i = CinBaseTextService.smenucandidates.index(itemName)
                        self.onMenuCommand(CinBaseTextService, i, 1)
                        CinBaseTextService.resetMenuCand = self.closeMenuCand(CinBaseTextService)
                    elif CinBaseTextService.menutype == 2: # 切至特殊符號子頁面
                        CinBaseTextService.menucandidates = CinBaseTextService.symbols.getCharDef(CinBaseTextService.candidateList[candCursor])
                        pagecandidates = list(self.chunks(CinBaseTextService.menucandidates, CinBaseTextService.candPerPage))
                        CinBaseTextService.resetMenuCand = self.switchMenuType(CinBaseTextService, 3, ["2," + str(candCursor) + "," + str(currentCandPage)])
                    elif CinBaseTextService.menutype == 3: # 執行特殊符號子頁面項目
                        CinBaseTextService.setCommitString(CinBaseTextService.candidateList[candCursor])
                        CinBaseTextService.resetMenuCand = self.closeMenuCand(CinBaseTextService)
                    elif CinBaseTextService.menutype == 4: # 執行注音符號頁面項目
                        CinBaseTextService.setCommitString(CinBaseTextService.candidateList[candCursor])
                        CinBaseTextService.resetMenuCand = self.closeMenuCand(CinBaseTextService)
                    elif CinBaseTextService.menutype == 5: # 切至外語文字子頁面
                        CinBaseTextService.menucandidates = CinBaseTextService.flangs.getCharDef(CinBaseTextService.candidateList[candCursor])
                        pagecandidates = list(self.chunks(CinBaseTextService.menucandidates, CinBaseTextService.candPerPage))
                        CinBaseTextService.resetMenuCand = self.switchMenuType(CinBaseTextService, 6, ["5," + str(candCursor) + "," + str(currentCandPage)])
                    elif CinBaseTextService.menutype == 6: # 執行外語文字子頁面項目
                        CinBaseTextService.setCommitString(CinBaseTextService.candidateList[candCursor])
                        CinBaseTextService.resetMenuCand = self.closeMenuCand(CinBaseTextService)
                    elif CinBaseTextService.menutype == 7: # 切換至表情符號分類頁面
                        menutype = 8
                        i = self.emojimenulist.index(CinBaseTextService.candidateList[candCursor])
                        if i == 0:
                            CinBaseTextService.emojitype = 0
                            CinBaseTextService.menucandidates = self.emoji.emoticons_keynames
                        elif i == 1:
                            CinBaseTextService.emojitype = 1
                            CinBaseTextService.menucandidates = self.emoji.pictographs_keynames
                        elif i == 2:
                            CinBaseTextService.emojitype = 2
                            CinBaseTextService.menucandidates = self.emoji.miscellaneous_keynames
                        elif i == 3:
                            CinBaseTextService.emojitype = 3
                            CinBaseTextService.menucandidates = self.emoji.dingbats_keynames
                        elif i == 4:
                            CinBaseTextService.emojitype = 4
                            CinBaseTextService.menucandidates = self.emoji.transport_keynames
                        elif i == 5:
                            CinBaseTextService.emojitype = 5
                            CinBaseTextService.menucandidates = self.emoji.modifiercolor
                            menutype = 9
                        pagecandidates = list(self.chunks(CinBaseTextService.menucandidates, CinBaseTextService.candPerPage))
                        CinBaseTextService.resetMenuCand = self.switchMenuType(CinBaseTextService, menutype, ["7," + str(candCursor) + "," + str(currentCandPage)])
                    elif CinBaseTextService.menutype == 8: # 切換至表情符號分類子頁面
                        if CinBaseTextService.emojitype == 0:
                            CinBaseTextService.menucandidates = self.emoji.getCharDef("emoticons", CinBaseTextService.candidateList[candCursor])
                        elif CinBaseTextService.emojitype == 1:
                            CinBaseTextService.menucandidates = self.emoji.getCharDef("pictographs", CinBaseTextService.candidateList[candCursor])
                        elif CinBaseTextService.emojitype == 2:
                            CinBaseTextService.menucandidates = self.emoji.getCharDef("miscellaneous", CinBaseTextService.candidateList[candCursor])
                        elif CinBaseTextService.emojitype == 3:
                            CinBaseTextService.menucandidates = self.emoji.getCharDef("dingbats", CinBaseTextService.candidateList[candCursor])
                        elif CinBaseTextService.emojitype == 4:
                            CinBaseTextService.menucandidates = self.emoji.getCharDef("transport", CinBaseTextService.candidateList[candCursor])
                        pagecandidates = list(self.chunks(CinBaseTextService.menucandidates, CinBaseTextService.candPerPage))
                        CinBaseTextService.resetMenuCand = self.switchMenuType(CinBaseTextService, 9, ["8," + str(candCursor) + "," + str(currentCandPage)])
                    elif CinBaseTextService.menutype == 9: # 執行表情符號分類子頁面項目
                        CinBaseTextService.setCommitString(CinBaseTextService.candidateList[candCursor])
                        CinBaseTextService.resetMenuCand = self.closeMenuCand(CinBaseTextService)

                if CinBaseTextService.prevmenucandlist:
                    candCursor = CinBaseTextService.prevmenucandlist[0]
                    currentCandPage = CinBaseTextService.prevmenucandlist[1]
                    CinBaseTextService.prevmenucandlist = []

                if CinBaseTextService.resetMenuCand:
                    candCursor = 0
                    currentCandPage = 0
                        
                # 更新選字視窗游標位置
                CinBaseTextService.setCandidateCursor(candCursor)
                CinBaseTextService.setCandidatePage(currentCandPage)
                CinBaseTextService.setCandidateList(pagecandidates[currentCandPage])
        
        # 按鍵處理 ----------------------------------------------------------------
        # 某些狀況須要特別處理或忽略
        # 如果輸入編輯區為空且選單未開啟過，不處理 Enter 及 Backspace 鍵
        if not CinBaseTextService.isComposing() and CinBaseTextService.closemenu and not CinBaseTextService.multifunctionmode:
            if keyCode == VK_RETURN or keyCode == VK_BACK:
                return False

        # 若按下 Shift 鍵,且沒有按下其它的按鍵
        if keyEvent.isKeyDown(VK_SHIFT) and not keyEvent.isPrintableChar():
            return False

        # 若按下 Ctrl 鍵
        if keyEvent.isKeyDown(VK_CONTROL):
            # 若按下的是指定的符號鍵，輸入法需要處理此按鍵
            if self.isCtrlSymbolsChar(keyCode):
                if CinBaseTextService.msymbols.isInCharDef(charStr) and CinBaseTextService.closemenu and not CinBaseTextService.multifunctionmode:
                    if not CinBaseTextService.ctrlsymbolsmode:
                        CinBaseTextService.ctrlsymbolsmode = True
                        CinBaseTextService.compositionChar = charStr
                    elif CinBaseTextService.msymbols.isInCharDef(CinBaseTextService.compositionChar + charStr):
                        CinBaseTextService.compositionChar += charStr
                    candidates = CinBaseTextService.msymbols.getCharDef(CinBaseTextService.compositionChar)
                    CinBaseTextService.setCompositionString(candidates[0])

        # 大易須換回選字鍵
        if not CinBaseTextService.showmenu:
            if CinBaseTextService.imeDirName == "chedayi":
                CinBaseTextService.selKeys = "'[]-\\"
                if not self.candselKeys == "0123456789":
                    self.candselKeys = "0123456789"
                    CinBaseTextService.TextService.setSelKeys(CinBaseTextService, self.candselKeys)
                    CinBaseTextService.isSelKeysChanged = True

        # 按下的鍵為 CIN 內有定義的字根
        if CinBaseTextService.cin.isInKeyName(charStrLow) and CinBaseTextService.closemenu and not CinBaseTextService.multifunctionmode and not keyEvent.isKeyDown(VK_CONTROL) and not CinBaseTextService.ctrlsymbolsmode and not CinBaseTextService.dayisymbolsmode:
            # 若按下 Shift 鍵
            if keyEvent.isKeyDown(VK_SHIFT) and CinBaseTextService.langMode == CHINESE_MODE and not CinBaseTextService.imeDirName == "cheez":
                CommitStr = charStr
                # 使用 Shift 鍵做全形輸入 (easy symbol input)
                # 這裡的 easy symbol input，是定義在 swkb.dat 設定檔中的符號
                if CinBaseTextService.easySymbolsWithShift and self.isLetterChar(keyCode):
                    if CinBaseTextService.swkb.isInCharDef(charStr.upper()):
                        candidates = CinBaseTextService.swkb.getCharDef(charStr.upper())
                        CommitStr = candidates[0]
                        candidates = []
                    else: # 不在快速符號表裡
                        if CinBaseTextService.shapeMode == FULLSHAPE_MODE: # 全形模式
                            CommitStr = self.charCodeToFullshape(charCode)
                    CinBaseTextService.setCommitString(CommitStr)
                    self.resetComposition(CinBaseTextService)
                # 如果啟用 Shift 輸入全形標點
                elif CinBaseTextService.fullShapeSymbols:
                    if charStr == '*' and CinBaseTextService.supportWildcard and CinBaseTextService.selWildcardChar == charStr: # 如果按鍵及萬用字元為*
                        CinBaseTextService.compositionChar += '*'
                        keyname = '＊'
                        CinBaseTextService.setCompositionString(CinBaseTextService.compositionString + keyname)
                    # 如果是符號或數字，將字串轉為全形再輸出
                    elif self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode):
                        if CinBaseTextService.fsymbols.isInCharDef(charStr):
                            CinBaseTextService.compositionChar = charStr
                            fullShapeSymbolsList = CinBaseTextService.fsymbols.getCharDef(CinBaseTextService.compositionChar)
                            CinBaseTextService.setCompositionString(fullShapeSymbolsList[0])
                            CinBaseTextService.setCompositionCursor(len(CinBaseTextService.compositionString))
                        else:
                            if CinBaseTextService.cin.isInKeyName(charStrLow): # 如果是 CIN 所定義的字根
                                CinBaseTextService.compositionChar = charStrLow
                                keyname = CinBaseTextService.cin.getKeyName(charStrLow)
                                CinBaseTextService.setCompositionString(keyname)
                                CinBaseTextService.setCompositionCursor(len(CinBaseTextService.compositionString))
                            else:
                                if CinBaseTextService.shapeMode == FULLSHAPE_MODE: # 全形模式
                                    CommitStr = self.SymbolscharCodeToFullshape(charCode)
                                CinBaseTextService.setCommitString(CommitStr)
                                self.resetComposition(CinBaseTextService)
                    else: #如果是字母
                        if CinBaseTextService.shapeMode == FULLSHAPE_MODE: # 全形模式
                            CommitStr = self.charCodeToFullshape(charCode)
                        CinBaseTextService.setCommitString(CommitStr)
                        self.resetComposition(CinBaseTextService)
                else: # 如果未使用 SHIFT 輸入快速符號或全形標點
                    if charStr == '*' and CinBaseTextService.supportWildcard and CinBaseTextService.selWildcardChar == charStr: # 如果按鍵及萬用字元為*
                        CinBaseTextService.compositionChar += '*'
                        keyname = '＊'
                        CinBaseTextService.setCompositionString(CinBaseTextService.compositionString + keyname)
                    else:
                        if CinBaseTextService.cin.isInKeyName(charStrLow) and (self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode)): # 如果是 CIN 所定義的字根
                            CinBaseTextService.compositionChar = charStrLow
                            keyname = CinBaseTextService.cin.getKeyName(charStrLow)
                            CinBaseTextService.setCompositionString(keyname)
                            CinBaseTextService.setCompositionCursor(len(CinBaseTextService.compositionString))
                        else:
                            if CinBaseTextService.shapeMode == FULLSHAPE_MODE: # 全形模式
                                # 如果是符號或數字，將字串轉為全形再輸出
                                if self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode):
                                    CommitStr = self.SymbolscharCodeToFullshape(charCode)
                                else:
                                    CommitStr = self.charCodeToFullshape(charCode)
                            CinBaseTextService.setCommitString(CommitStr)
                            self.resetComposition(CinBaseTextService)
            else: # 若沒按下 Shift 鍵
                # 如果是英文全形模式，將字串轉為全形再輸出
                if CinBaseTextService.shapeMode == FULLSHAPE_MODE and CinBaseTextService.langMode == ENGLISH_MODE:
                    # 如果是符號或數字，將字串轉為全形再輸出
                    if self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode):
                        CommitStr = self.SymbolscharCodeToFullshape(charCode)
                    else:
                        CommitStr = self.charCodeToFullshape(charCode)
                    CinBaseTextService.setCommitString(CommitStr)
                    self.resetComposition(CinBaseTextService)
                else: # 送出 CIN 所定義的字根
                    if not CinBaseTextService.directShowCand and CinBaseTextService.showCandidates and self.isInSelKeys(CinBaseTextService, charCode):
                        # 不送出 CIN 所定義的字根
                        CinBaseTextService.compositionChar = CinBaseTextService.compositionChar
                    elif CinBaseTextService.imeDirName == "chedayi" and CinBaseTextService.showCandidates and self.isInSelKeys(CinBaseTextService, charCode):
                        # 不送出 CIN 所定義的字根
                        CinBaseTextService.compositionChar = CinBaseTextService.compositionChar
                    else:
                        # 如果是注音輸入法
                        if CinBaseTextService.imeDirName == "chephonetic":
                            if not CinBaseTextService.keyboardLayout == 0 and not chr(charCode).lower() in CinBaseTextService.kbtypelist[CinBaseTextService.keyboardLayout]:
                                CinBaseTextService.compositionChar = CinBaseTextService.compositionChar
                            else:
                                if len(CinBaseTextService.compositionChar) > 0:
                                    CinBaseTextService.updateCompositionChar(charStrLow)
                                else:
                                    CinBaseTextService.compositionChar += charStrLow
                                    keyname = CinBaseTextService.cin.getKeyName(charStrLow)
                                    CinBaseTextService.setCompositionString(CinBaseTextService.compositionString + keyname)
                                    CinBaseTextService.setCompositionCursor(len(CinBaseTextService.compositionString))
                        else:        
                            CinBaseTextService.compositionChar += charStrLow
                            keyname = CinBaseTextService.cin.getKeyName(charStrLow)
                            CinBaseTextService.setCompositionString(CinBaseTextService.compositionString + keyname)
                            CinBaseTextService.setCompositionCursor(len(CinBaseTextService.compositionString))
        # 按下的鍵不存在於 CIN 所定義的字根
        elif not CinBaseTextService.cin.isInKeyName(charStrLow) and CinBaseTextService.closemenu and not CinBaseTextService.multifunctionmode and not keyEvent.isKeyDown(VK_CONTROL) and not CinBaseTextService.ctrlsymbolsmode and not CinBaseTextService.dayisymbolsmode:
            # 若按下 Shift 鍵
            if keyEvent.isKeyDown(VK_SHIFT) and CinBaseTextService.langMode == CHINESE_MODE:
                # 如果停用 Shift 輸入全形標點
                if not CinBaseTextService.fullShapeSymbols:
                    # 如果是全形模式，將字串轉為全形再輸出
                    if CinBaseTextService.shapeMode == FULLSHAPE_MODE:
                        if charStr == '*' and CinBaseTextService.supportWildcard and CinBaseTextService.selWildcardChar == charStr: # 如果按鍵及萬用字元為*
                            CinBaseTextService.compositionChar += '*'
                            keyname = '＊'
                            CinBaseTextService.setCompositionString(CinBaseTextService.compositionString + keyname)
                        else:
                            # 如果是符號或數字，將字串轉為全形再輸出
                            if self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode):
                                CommitStr = self.SymbolscharCodeToFullshape(charCode)
                            else:
                                CommitStr = self.charCodeToFullshape(charCode)
                            CinBaseTextService.setCommitString(CommitStr)
                            self.resetComposition(CinBaseTextService)
                    else: # 半形模式直接輸出不作處理
                        if charStr == '*' and CinBaseTextService.supportWildcard and CinBaseTextService.selWildcardChar == charStr: # 如果按鍵及萬用字元為*
                            CinBaseTextService.compositionChar += '*'
                            keyname = '＊'
                            CinBaseTextService.setCompositionString(CinBaseTextService.compositionString + keyname)
                        else:
                            CommitStr = charStr
                            CinBaseTextService.setCommitString(CommitStr)
                            self.resetComposition(CinBaseTextService)
                else: # 如果啟用 Shift 輸入全形標點
                    # 如果是符號或數字鍵，將字串轉為全形再輸出
                    if self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode):
                        # 如果該鍵有定義在 fsymbols
                        if CinBaseTextService.fsymbols.isInCharDef(charStr):
                            if charStr == '*' and CinBaseTextService.supportWildcard and CinBaseTextService.selWildcardChar == charStr: # 如果按鍵及萬用字元為*
                                CinBaseTextService.compositionChar += '*'
                                keyname = '＊'
                                CinBaseTextService.setCompositionString(CinBaseTextService.compositionString + keyname)
                            else:
                                CinBaseTextService.compositionChar = charStr
                                fullShapeSymbolsList = CinBaseTextService.fsymbols.getCharDef(CinBaseTextService.compositionChar)
                                CinBaseTextService.setCompositionString(fullShapeSymbolsList[0])
                                CinBaseTextService.setCompositionCursor(len(CinBaseTextService.compositionString))
                        else: # 沒有定義在 fsymbols 裡
                            if charStr == '*' and CinBaseTextService.supportWildcard and CinBaseTextService.selWildcardChar == charStr: # 如果按鍵及萬用字元為*
                                CinBaseTextService.compositionChar += '*'
                                keyname = '＊'
                                CinBaseTextService.setCompositionString(CinBaseTextService.compositionString + keyname)
                            else:
                                if self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode):
                                    CommitStr = self.SymbolscharCodeToFullshape(charCode)
                                else:
                                    CommitStr = self.charCodeToFullshape(charCode)
                                CinBaseTextService.setCommitString(CommitStr)
                                self.resetComposition(CinBaseTextService)
                                
            else: # 若沒按下 Shift 鍵
                # 如果是全形模式，將字串轉為全形再輸出
                if CinBaseTextService.shapeMode == FULLSHAPE_MODE and len(CinBaseTextService.compositionChar) == 0:
                    if self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode):
                        CommitStr = self.SymbolscharCodeToFullshape(charCode)
                    else:
                        CommitStr = self.charCodeToFullshape(charCode)
                    CinBaseTextService.setCommitString(CommitStr)
                    self.resetComposition(CinBaseTextService)

        if CinBaseTextService.langMode == CHINESE_MODE and len(CinBaseTextService.compositionChar) >= 1 and not CinBaseTextService.multifunctionmode:
            CinBaseTextService.showmenu = False
            if not CinBaseTextService.directShowCand:
                if not CinBaseTextService.lastCompositionCharLength == len(CinBaseTextService.compositionChar):
                    CinBaseTextService.lastCompositionCharLength = len(CinBaseTextService.compositionChar)
                    CinBaseTextService.isShowCandidates = False
                    CinBaseTextService.setShowCandidates(False)
            
            # 按下 ESC 鍵
            if keyCode == VK_ESCAPE and (CinBaseTextService.showCandidates or len(CinBaseTextService.compositionChar) > 0):
                CinBaseTextService.lastCompositionCharLength = 0
                if not CinBaseTextService.directShowCand:
                    CinBaseTextService.isShowCandidates = False
                self.resetComposition(CinBaseTextService)
                
            # 刪掉一個字根
            if keyCode == VK_BACK:
                if CinBaseTextService.compositionString != "":
                    if CinBaseTextService.cin.isInKeyName(CinBaseTextService.compositionChar[len(CinBaseTextService.compositionChar)-1:]):
                        keyLength = len(CinBaseTextService.cin.getKeyName(CinBaseTextService.compositionChar[len(CinBaseTextService.compositionChar)-1:]))
                    else:
                        keyLength = 1
                    CinBaseTextService.setCompositionString(CinBaseTextService.compositionString[:-keyLength])
                    CinBaseTextService.compositionChar = CinBaseTextService.compositionChar[:-1]
                    CinBaseTextService.lastCompositionCharLength = CinBaseTextService.lastCompositionCharLength - 1
                    CinBaseTextService.setCandidateCursor(0)
                    CinBaseTextService.setCandidatePage(0)
                    CinBaseTextService.wildcardcandidates = []
                    CinBaseTextService.wildcardpagecandidates = []
                    if not CinBaseTextService.directShowCand:
                        CinBaseTextService.isShowCandidates = False
                        CinBaseTextService.setShowCandidates(False)
                    if CinBaseTextService.compositionString == '':
                        self.resetComposition(CinBaseTextService)

            # 組字字根超過最大值
            if len(CinBaseTextService.compositionChar) > CinBaseTextService.maxCharLength:
                if CinBaseTextService.cin.isInKeyName(CinBaseTextService.compositionChar[len(CinBaseTextService.compositionChar)-1:]):
                    keyLength = len(CinBaseTextService.cin.getKeyName(CinBaseTextService.compositionChar[len(CinBaseTextService.compositionChar)-1:]))
                else:
                    keyLength = 1
                CinBaseTextService.setCompositionString(CinBaseTextService.compositionString[:-keyLength])
                CinBaseTextService.compositionChar = CinBaseTextService.compositionChar[:-1]

            if CinBaseTextService.cin.isInCharDef(CinBaseTextService.compositionChar) and CinBaseTextService.closemenu and not CinBaseTextService.ctrlsymbolsmode:
                candidates = CinBaseTextService.cin.getCharDef(CinBaseTextService.compositionChar)
                if CinBaseTextService.sortByPhrase and candidates:
                    candidates = self.sortByPhrase(CinBaseTextService, copy.deepcopy(candidates))
            elif CinBaseTextService.imeDirName == "chepinyin" and CinBaseTextService.cinFileList[CinBaseTextService.cfg.selCinType] == "thpinyin.cin":
                if CinBaseTextService.cin.isInCharDef(CinBaseTextService.compositionChar + "1") and CinBaseTextService.closemenu and not CinBaseTextService.ctrlsymbolsmode:
                    candidates = CinBaseTextService.cin.getCharDef(CinBaseTextService.compositionChar + '1')
                    if CinBaseTextService.sortByPhrase and candidates:
                        candidates = self.sortByPhrase(CinBaseTextService, copy.deepcopy(candidates))
            elif CinBaseTextService.fullShapeSymbols and CinBaseTextService.fsymbols.isInCharDef(CinBaseTextService.compositionChar) and CinBaseTextService.closemenu:
                candidates = CinBaseTextService.fsymbols.getCharDef(CinBaseTextService.compositionChar)
            elif CinBaseTextService.msymbols.isInCharDef(CinBaseTextService.compositionChar) and CinBaseTextService.closemenu and CinBaseTextService.ctrlsymbolsmode:
                candidates = CinBaseTextService.msymbols.getCharDef(CinBaseTextService.compositionChar)
            elif CinBaseTextService.dayisymbolsmode and CinBaseTextService.closemenu:
                if CinBaseTextService.dsymbols.isInCharDef(CinBaseTextService.compositionChar[1:]):
                    candidates = CinBaseTextService.dsymbols.getCharDef(CinBaseTextService.compositionChar[1:])
                    CinBaseTextService.setCompositionString(candidates[0])
            elif CinBaseTextService.supportWildcard and CinBaseTextService.selWildcardChar in CinBaseTextService.compositionChar and CinBaseTextService.closemenu:
                if CinBaseTextService.wildcardcandidates and CinBaseTextService.wildcardcompositionChar == CinBaseTextService.compositionChar:
                    candidates = CinBaseTextService.wildcardcandidates
                else:
                    CinBaseTextService.setCandidateCursor(0)
                    CinBaseTextService.setCandidatePage(0)
                    CinBaseTextService.wildcardcandidates = CinBaseTextService.cin.getWildcardCharDefs(CinBaseTextService.compositionChar, CinBaseTextService.selWildcardChar, CinBaseTextService.candMaxItems)
                    if CinBaseTextService.imeDirName == "chepinyin" and CinBaseTextService.cinFileList[CinBaseTextService.cfg.selCinType] == "thpinyin.cin":
                        if not CinBaseTextService.wildcardcandidates:
                            CinBaseTextService.wildcardcandidates = CinBaseTextService.cin.getWildcardCharDefs(CinBaseTextService.compositionChar + "1", CinBaseTextService.selWildcardChar, CinBaseTextService.candMaxItems)
                    CinBaseTextService.wildcardpagecandidates = []
                    CinBaseTextService.wildcardcompositionChar = CinBaseTextService.compositionChar
                    candidates = CinBaseTextService.wildcardcandidates
                CinBaseTextService.isWildcardChardefs = True
                if CinBaseTextService.sortByPhrase and candidates:
                    candidates = self.sortByPhrase(CinBaseTextService, copy.deepcopy(candidates))
        
        if CinBaseTextService.langMode == CHINESE_MODE and len(CinBaseTextService.compositionChar) >= 1:    
            # 候選清單處理
            if candidates and not CinBaseTextService.phrasemode:
                if not CinBaseTextService.directShowCand:
                    # EndKey 處理 (拼音、注音)
                    if CinBaseTextService.useEndKey:
                        if charStr in CinBaseTextService.endKeyList:
                            if not CinBaseTextService.isShowCandidates:
                                CinBaseTextService.isShowCandidates = True
                                CinBaseTextService.canUseSelKey = False
                            else:
                                CinBaseTextService.canUseSelKey = True
                        else:
                            if CinBaseTextService.isShowCandidates:
                                CinBaseTextService.canUseSelKey = True

                    # 字滿及符號處理 (大易、注音、輕鬆)
                    if CinBaseTextService.autoShowCandWhenMaxChar or CinBaseTextService.dayisymbolsmode:
                        if len(CinBaseTextService.compositionChar) == CinBaseTextService.maxCharLength or CinBaseTextService.dayisymbolsmode:
                            if len(candidates) == 1 and CinBaseTextService.directCommitString:
                                commitStr = candidates[0]
                                CinBaseTextService.lastCommitString = commitStr

                                # 如果使用萬用字元解碼
                                if CinBaseTextService.isWildcardChardefs:
                                    if not CinBaseTextService.hidePromptMessages:
                                        messagestr = CinBaseTextService.cin.getCharEncode(commitStr)
                                        CinBaseTextService.showMessage(messagestr, 5)
                                    CinBaseTextService.wildcardcandidates = []
                                    CinBaseTextService.wildcardpagecandidates = []
                                    CinBaseTextService.isWildcardChardefs = False

                                # 如果使用打繁出簡，就轉成簡體中文
                                if CinBaseTextService.outputSimpChinese:
                                    commitStr = CinBaseTextService.opencc.convert(commitStr)

                                CinBaseTextService.setCommitString(commitStr)

                                if CinBaseTextService.showPhrase:
                                    CinBaseTextService.phrasemode = True

                                self.resetComposition(CinBaseTextService)
                                candCursor = 0
                                currentCandPage = 0
                                CinBaseTextService.isShowCandidates = False
                                CinBaseTextService.canSetCommitString = True
                            else:
                                if not CinBaseTextService.isShowCandidates:
                                    CinBaseTextService.isShowCandidates = True
                                    CinBaseTextService.canUseSelKey = False
                                else:
                                    if not CinBaseTextService.imeDirName == "chephonetic":
                                        CinBaseTextService.canUseSelKey = True
                        else:
                            if CinBaseTextService.isShowCandidates:
                                if not CinBaseTextService.imeDirName == "chephonetic":
                                    CinBaseTextService.canUseSelKey = True

                    if (keyCode == VK_SPACE or keyCode == VK_DOWN) and not CinBaseTextService.isShowCandidates:  # 按下空白鍵和向下鍵
                        # 如果只有一個候選字就直接出字
                        if len(candidates) == 1 and CinBaseTextService.directCommitString:
                            if keyCode == VK_SPACE:
                                commitStr = candidates[0]
                                CinBaseTextService.lastCommitString = commitStr
                                
                                # 如果使用萬用字元解碼
                                if CinBaseTextService.isWildcardChardefs:
                                    if not CinBaseTextService.hidePromptMessages:
                                        messagestr = CinBaseTextService.cin.getCharEncode(commitStr)
                                        CinBaseTextService.showMessage(messagestr, 5)
                                    CinBaseTextService.wildcardcandidates = []
                                    CinBaseTextService.wildcardpagecandidates = []
                                    CinBaseTextService.isWildcardChardefs = False
                                    
                                # 如果使用打繁出簡，就轉成簡體中文
                                if CinBaseTextService.outputSimpChinese:
                                    commitStr = CinBaseTextService.opencc.convert(commitStr)

                                CinBaseTextService.setCommitString(commitStr)

                                if CinBaseTextService.showPhrase:
                                    CinBaseTextService.phrasemode = True
                                self.resetComposition(CinBaseTextService)
                                candCursor = 0
                                currentCandPage = 0
                                CinBaseTextService.isShowCandidates = False
                                CinBaseTextService.canSetCommitString = True
                            else:
                                CinBaseTextService.isShowCandidates = True
                                CinBaseTextService.canSetCommitString = False
                        else:
                            CinBaseTextService.isShowCandidates = True
                            CinBaseTextService.canSetCommitString = False
                            if keyCode == VK_SPACE:
                                CinBaseTextService.canUseSpaceAsPageKey = False
                else:
                    CinBaseTextService.isShowCandidates = True
                    CinBaseTextService.canSetCommitString = True

                if CinBaseTextService.isShowCandidates:
                    candCursor = CinBaseTextService.candidateCursor  # 目前的游標位置
                    candCount = len(CinBaseTextService.candidateList)  # 目前選字清單項目數
                    currentCandPageCount = math.ceil(len(candidates) / CinBaseTextService.candPerPage) # 目前的選字清單總頁數
                    currentCandPage = CinBaseTextService.currentCandPage # 目前的選字清單頁數
                
                    # 候選清單分頁
                    if CinBaseTextService.isWildcardChardefs:
                        if CinBaseTextService.wildcardpagecandidates:
                            pagecandidates = CinBaseTextService.wildcardpagecandidates
                        else:
                            CinBaseTextService.wildcardpagecandidates = list(self.chunks(candidates, CinBaseTextService.candPerPage))
                            pagecandidates = CinBaseTextService.wildcardpagecandidates
                    else:
                        pagecandidates = list(self.chunks(candidates, CinBaseTextService.candPerPage))
                    CinBaseTextService.setCandidateList(pagecandidates[currentCandPage])
                    if not CinBaseTextService.isSelKeysChanged:
                        CinBaseTextService.setShowCandidates(True)

                # 如果字根首字是符號就直接輸出
                if (self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode)) and len(CinBaseTextService.compositionChar) == 1 and charStrLow == CinBaseTextService.compositionChar and CinBaseTextService.directCommitSymbol:
                    directout = True
                    if CinBaseTextService.cin.isInCharDef(CinBaseTextService.compositionChar) and CinBaseTextService.supportSymbolCoding and len(CinBaseTextService.cin.haveNextCharDef(CinBaseTextService.compositionChar)) > 1:
                        directout = False
                    
                    if len(candidates) == 1 and directout and CinBaseTextService.selWildcardChar != CinBaseTextService.compositionChar:
                        cand = candidates[0]
                        CinBaseTextService.setCommitString(cand)
                        self.resetComposition(CinBaseTextService)
                        candCursor = 0
                        currentCandPage = 0
                
                # 多功能前導字元
                if CinBaseTextService.multifunctionmode and CinBaseTextService.directCommitSymbol:
                    if len(candidates) == 1:
                        cand = candidates[0]
                        CinBaseTextService.setCommitString(cand)
                        self.resetComposition(CinBaseTextService)
                        candCursor = 0
                        currentCandPage = 0

                if CinBaseTextService.isShowCandidates:
                    # 使用選字鍵執行項目或輸出候選字
                    if self.isInSelKeys(CinBaseTextService, charCode) and not keyEvent.isKeyDown(VK_SHIFT) and CinBaseTextService.canUseSelKey:
                        if CinBaseTextService.imeDirName == "chedayi":
                            i = CinBaseTextService.selKeys.index(charStr) + 1
                        else:
                            i = CinBaseTextService.selKeys.index(charStr)
                        if i < CinBaseTextService.candPerPage and i < len(CinBaseTextService.candidateList):
                            commitStr = CinBaseTextService.candidateList[i]
                            CinBaseTextService.lastCommitString = commitStr

                            # 如果使用萬用字元解碼
                            if CinBaseTextService.isWildcardChardefs:
                                if not CinBaseTextService.hidePromptMessages:
                                    messagestr = CinBaseTextService.cin.getCharEncode(commitStr)
                                    CinBaseTextService.showMessage(messagestr, 5)
                                CinBaseTextService.wildcardcandidates = []
                                CinBaseTextService.wildcardpagecandidates = []
                                CinBaseTextService.isWildcardChardefs = False
                    
                            # 如果使用打繁出簡，就轉成簡體中文
                            if CinBaseTextService.outputSimpChinese:
                                commitStr = CinBaseTextService.opencc.convert(commitStr)
                        
                            CinBaseTextService.setCommitString(commitStr)
                            
                            if CinBaseTextService.showPhrase:
                                CinBaseTextService.phrasemode = True
                            self.resetComposition(CinBaseTextService)
                            candCursor = 0
                            currentCandPage = 0
                            if not CinBaseTextService.directShowCand:
                                CinBaseTextService.canSetCommitString = True
                                CinBaseTextService.isShowCandidates = False
                    elif keyCode == VK_UP:  # 游標上移
                        if (candCursor - CinBaseTextService.candPerRow) < 0:
                            if currentCandPage > 0:
                                currentCandPage -= 1
                                candCursor = 0
                        else:
                            if (candCursor - CinBaseTextService.candPerRow) >= 0:
                                candCursor = candCursor - CinBaseTextService.candPerRow
                    elif keyCode == VK_DOWN and CinBaseTextService.canSetCommitString:  # 游標下移
                        if (candCursor + CinBaseTextService.candPerRow) >= CinBaseTextService.candPerPage:
                            if (currentCandPage + 1) < currentCandPageCount:
                                currentCandPage += 1
                                candCursor = 0
                        else:
                            if (candCursor + CinBaseTextService.candPerRow) < len(pagecandidates[currentCandPage]):
                                candCursor = candCursor + CinBaseTextService.candPerRow
                    elif keyCode == VK_LEFT:  # 游標左移
                        if candCursor > 0:
                            candCursor -= 1
                    elif keyCode == VK_RIGHT:  # 游標右移
                        if (candCursor + 1) < candCount:
                            candCursor += 1
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
                    elif (keyCode == VK_RETURN or (keyCode == VK_SPACE and (not CinBaseTextService.switchPageWithSpace or currentCandPageCount <= 1))) and CinBaseTextService.canSetCommitString:  # 按下 Enter 鍵或空白鍵
                        # 找出目前游標位置的選字鍵 (1234..., asdf...等等)
                        commitStr = CinBaseTextService.candidateList[candCursor]
                        CinBaseTextService.lastCommitString = commitStr
                    
                        # 如果使用萬用字元解碼
                        if CinBaseTextService.isWildcardChardefs:
                            if not CinBaseTextService.hidePromptMessages:
                                messagestr = CinBaseTextService.cin.getCharEncode(commitStr)
                                CinBaseTextService.showMessage(messagestr, 5)
                            CinBaseTextService.wildcardcandidates = []
                            CinBaseTextService.wildcardpagecandidates = []
                            CinBaseTextService.isWildcardChardefs = False
                    
                        # 如果使用打繁出簡，就轉成簡體中文
                        if CinBaseTextService.outputSimpChinese:
                            commitStr = CinBaseTextService.opencc.convert(commitStr)
                    
                        CinBaseTextService.setCommitString(commitStr)
                        
                        if CinBaseTextService.showPhrase:
                            CinBaseTextService.phrasemode = True
                            if keyCode == VK_SPACE:
                                CinBaseTextService.canUseSpaceAsPageKey = False
                        self.resetComposition(CinBaseTextService)
                        candCursor = 0
                        currentCandPage = 0
                        if not CinBaseTextService.directShowCand:
                            CinBaseTextService.isShowCandidates = False
                    elif keyCode == VK_SPACE and CinBaseTextService.switchPageWithSpace: # 按下空白鍵
                        if CinBaseTextService.canUseSpaceAsPageKey:
                            if (currentCandPage + 1) < currentCandPageCount:
                                currentCandPage += 1
                                candCursor = 0
                            else:
                                currentCandPage = 0
                                candCursor = 0
                    else: # 按下其它鍵，先將候選字游標位址及目前頁數歸零
                        if not CinBaseTextService.ctrlsymbolsmode:
                            candCursor = 0
                            currentCandPage = 0
                    # 更新選字視窗游標位置及頁數
                    CinBaseTextService.setCandidateCursor(candCursor)
                    CinBaseTextService.setCandidatePage(currentCandPage)
                    CinBaseTextService.setCandidateList(pagecandidates[currentCandPage])
            else: # 沒有候選字
                # 按下空白鍵或 Enter 鍵
                if keyCode == VK_SPACE or keyCode == VK_RETURN:
                    if len(candidates) == 0:
                        if CinBaseTextService.multifunctionmode:
                            if CinBaseTextService.compositionChar == '`':
                                CinBaseTextService.setCommitString(CinBaseTextService.compositionChar)
                                self.resetComposition(CinBaseTextService)
                            else:
                                if CinBaseTextService.compositionChar[:2] == '`U':
                                    if len(CinBaseTextService.compositionChar) > 2:
                                        commitStr = chr(int(CinBaseTextService.compositionChar[2:], 16))
                                        CinBaseTextService.lastCommitString = commitStr
                                        if not CinBaseTextService.hidePromptMessages:
                                            messagestr = CinBaseTextService.cin.getCharEncode(commitStr)
                                            CinBaseTextService.showMessage(messagestr, 5)
                                        CinBaseTextService.setCommitString(commitStr)
                                    
                                        if CinBaseTextService.showPhrase:
                                            CinBaseTextService.phrasemode = True
                                        self.resetComposition(CinBaseTextService)
                                    else:
                                        CinBaseTextService.showMessage("請輸入 Unicode 編碼...", 3)
                        else:
                            CinBaseTextService.showMessage("查無組字...", 3)
                            if CinBaseTextService.autoClearCompositionChar:
                                self.resetComposition(CinBaseTextService)
                            if CinBaseTextService.playSoundWhenNonCand:
                                winsound.PlaySound('alert', winsound.SND_ASYNC)

                CinBaseTextService.setShowCandidates(False)
                CinBaseTextService.isShowCandidates = False

        # 聯想字模式
        if CinBaseTextService.showPhrase and CinBaseTextService.phrasemode:
            phrasecandidates = []
            if CinBaseTextService.userphrase.isInCharDef(CinBaseTextService.lastCommitString):
                phrasecandidates = CinBaseTextService.userphrase.getCharDef(CinBaseTextService.lastCommitString)
            if CinBaseTextService.phrase.isInCharDef(CinBaseTextService.lastCommitString):
                if len(phrasecandidates) == 0:
                    phrasecandidates = CinBaseTextService.phrase.getCharDef(CinBaseTextService.lastCommitString)
                else:
                    if not CinBaseTextService.isShowPhraseCandidates:
                        phrasecandidates.extend(CinBaseTextService.phrase.getCharDef(CinBaseTextService.lastCommitString))
                
            if phrasecandidates:
                candCursor = CinBaseTextService.candidateCursor  # 目前的游標位置
                candCount = len(CinBaseTextService.candidateList)  # 目前選字清單項目數
                currentCandPageCount = math.ceil(len(phrasecandidates) / CinBaseTextService.candPerPage) # 目前的選字清單總頁數
                currentCandPage = CinBaseTextService.currentCandPage # 目前的選字清單頁數

                # 候選清單分頁
                pagecandidates = list(self.chunks(phrasecandidates, CinBaseTextService.candPerPage))
                CinBaseTextService.setCandidateList(pagecandidates[currentCandPage])
                CinBaseTextService.setShowCandidates(True)

                # 使用選字鍵執行項目或輸出候選字
                if self.isInSelKeys(CinBaseTextService, charCode) and not keyEvent.isKeyDown(VK_SHIFT):
                    if CinBaseTextService.isShowPhraseCandidates:
                        if CinBaseTextService.imeDirName == "chedayi":
                            i = CinBaseTextService.selKeys.index(charStr) + 1
                        else:
                            i = CinBaseTextService.selKeys.index(charStr) 
                        if i < CinBaseTextService.candPerPage and i < len(CinBaseTextService.candidateList):
                            commitStr = CinBaseTextService.candidateList[i]

                            # 如果使用打繁出簡，就轉成簡體中文
                            if CinBaseTextService.outputSimpChinese:
                                commitStr = CinBaseTextService.opencc.convert(commitStr)
                    
                            CinBaseTextService.setCommitString(commitStr)
                            CinBaseTextService.phrasemode = False
                            CinBaseTextService.isShowPhraseCandidates = False
                        
                            self.resetComposition(CinBaseTextService)
                            candCursor = 0
                            currentCandPage = 0
                        
                            if not CinBaseTextService.directShowCand:
                                CinBaseTextService.canSetCommitString = True
                                CinBaseTextService.isShowCandidates = False
                    else:
                        CinBaseTextService.isShowPhraseCandidates = True
                elif keyCode == VK_UP:  # 游標上移
                    if (candCursor - CinBaseTextService.candPerRow) < 0:
                        if currentCandPage > 0:
                            currentCandPage -= 1
                            candCursor = 0
                    else:
                        if (candCursor - CinBaseTextService.candPerRow) >= 0:
                            candCursor = candCursor - CinBaseTextService.candPerRow
                elif keyCode == VK_DOWN and CinBaseTextService.canSetCommitString:  # 游標下移
                    if (candCursor + CinBaseTextService.candPerRow) >= CinBaseTextService.candPerPage:
                        if (currentCandPage + 1) < currentCandPageCount:
                            currentCandPage += 1
                            candCursor = 0
                    else:
                        if (candCursor + CinBaseTextService.candPerRow) < len(pagecandidates[currentCandPage]):
                            candCursor = candCursor + CinBaseTextService.candPerRow
                elif keyCode == VK_LEFT:  # 游標左移
                    if candCursor > 0:
                        candCursor -= 1
                elif keyCode == VK_RIGHT:  # 游標右移
                    if (candCursor + 1) < candCount:
                        candCursor += 1
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
                elif keyCode == VK_RETURN or (keyCode == VK_SPACE and (not CinBaseTextService.switchPageWithSpace or currentCandPageCount <= 1)):  # 按下 Enter 鍵或空白鍵
                    if CinBaseTextService.isShowPhraseCandidates:
                        # 找出目前游標位置的選字鍵 (1234..., asdf...等等)
                        commitStr = CinBaseTextService.candidateList[candCursor]

                        # 如果使用打繁出簡，就轉成簡體中文
                        if CinBaseTextService.outputSimpChinese:
                            commitStr = CinBaseTextService.opencc.convert(commitStr)

                        CinBaseTextService.setCommitString(commitStr)
                        CinBaseTextService.phrasemode = False
                        CinBaseTextService.isShowPhraseCandidates = False

                        self.resetComposition(CinBaseTextService)
                        candCursor = 0
                        currentCandPage = 0
                        
                        if not CinBaseTextService.directShowCand:
                            CinBaseTextService.isShowCandidates = False
                elif keyCode == VK_SPACE and CinBaseTextService.switchPageWithSpace: # 按下空白鍵
                    if CinBaseTextService.canUseSpaceAsPageKey:
                        if (currentCandPage + 1) < currentCandPageCount:
                            currentCandPage += 1
                            candCursor = 0
                        else:
                            currentCandPage = 0
                            candCursor = 0
                else: # 按下其它鍵，先將候選字游標位址及目前頁數歸零
                    CinBaseTextService.phrasemode = False
                    CinBaseTextService.isShowPhraseCandidates = False
                    self.resetComposition(CinBaseTextService)
                    candCursor = 0
                    currentCandPage = 0
                    if CinBaseTextService.cin.isInKeyName(charStrLow):
                        CinBaseTextService.compositionChar = charStrLow
                        keyname = CinBaseTextService.cin.getKeyName(charStrLow)
                        CinBaseTextService.setCompositionString(keyname)
                        CinBaseTextService.setCompositionCursor(len(CinBaseTextService.compositionString))
                        if CinBaseTextService.directShowCand:
                            pagecandidates = list(self.chunks(candidates, CinBaseTextService.candPerPage))
                            CinBaseTextService.setCandidateList(pagecandidates[currentCandPage])
                            CinBaseTextService.setShowCandidates(True)
                    elif len(CinBaseTextService.compositionChar) == 0 and charStr == '`':
                        CinBaseTextService.compositionChar += charStr
                        CinBaseTextService.setCompositionString(CinBaseTextService.compositionChar)
                        CinBaseTextService.multifunctionmode = True
                    
                # 更新選字視窗游標位置及頁數
                CinBaseTextService.setCandidateCursor(candCursor)
                CinBaseTextService.setCandidatePage(currentCandPage)
                CinBaseTextService.setCandidateList(pagecandidates[currentCandPage])
                
                if CinBaseTextService.showCandidates and CinBaseTextService.phrasemode:
                    CinBaseTextService.isShowPhraseCandidates = True
            else:
                CinBaseTextService.phrasemode = False
                CinBaseTextService.isShowPhraseCandidates = False
            
        if not CinBaseTextService.canUseSpaceAsPageKey:
            CinBaseTextService.canUseSpaceAsPageKey = True
            
        if not CinBaseTextService.closemenu:
            CinBaseTextService.closemenu = True
        return True

    # 使用者放開按鍵，在 app 收到前先過濾那些鍵是輸入法需要的。
    # return True，系統會呼叫 onKeyUp() 進一步處理這個按鍵
    # return False，表示我們不需要這個鍵，系統會原封不動把按鍵傳給應用程式
    def filterKeyUp(self, CinBaseTextService, keyEvent):
        # 不管中英文模式，只要放開 CapsLock 鍵，輸入法都須要處理
        if CinBaseTextService.lastKeyDownCode == VK_CAPITAL and keyEvent.keyCode == VK_CAPITAL:
            return True

        # 若啟用使用 Shift 鍵切換中英文模式
        if CinBaseTextService.cfg.switchLangWithShift:
            # 剛才最後一個按下的鍵，和現在放開的鍵，都是 Shift
            if CinBaseTextService.lastKeyDownCode == VK_SHIFT and keyEvent.keyCode == VK_SHIFT:
                pressedDuration = time.time() - CinBaseTextService.lastKeyDownTime
                # 按下和放開的時間相隔 < 0.5 秒
                if pressedDuration < 0.5:
                    CinBaseTextService.isLangModeChanged = True
                    return True
        
        # 若切換全形/半形模式
        if CinBaseTextService.isShapeModeChanged:
            return True
            
        if CinBaseTextService.isSelKeysChanged:
            return True
            
        CinBaseTextService.lastKeyDownCode = 0
        CinBaseTextService.lastKeyDownTime = 0.0
        return False


    def onKeyUp(self, CinBaseTextService, keyEvent):
        charCode = keyEvent.charCode
        keyCode = keyEvent.keyCode
        
        CinBaseTextService.lastKeyDownCode = 0
        CinBaseTextService.lastKeyDownTime = 0.0
        
        # 若放開 Shift 鍵,且觸發中英文切換
        if CinBaseTextService.isLangModeChanged and keyCode == VK_SHIFT:
            self.toggleLanguageMode(CinBaseTextService)  # 切換中英文模式
            CinBaseTextService.isLangModeChanged = False
            CinBaseTextService.showmenu = False
            CinBaseTextService.multifunctionmode = False
            if not CinBaseTextService.hidePromptMessages:
                message = '中文模式' if CinBaseTextService.langMode == CHINESE_MODE else '英數模式'
                CinBaseTextService.showMessage(message, 3)
            if CinBaseTextService.showCandidates or len(CinBaseTextService.compositionChar) > 0:
                self.resetComposition(CinBaseTextService)

        # 若放開 CapsLock 鍵
        if keyEvent.keyCode == VK_CAPITAL:
            self.updateLangButtons(CinBaseTextService)

        if CinBaseTextService.isShapeModeChanged:
            CinBaseTextService.isShapeModeChanged = False
            if not CinBaseTextService.hidePromptMessages:
                message = '半形模式' if CinBaseTextService.shapeMode == HALFSHAPE_MODE else '全形模式'
                CinBaseTextService.showMessage(message, 3)
            if CinBaseTextService.showCandidates or len(CinBaseTextService.compositionChar) > 0:
                self.resetComposition(CinBaseTextService)

        if CinBaseTextService.isSelKeysChanged:
            CinBaseTextService.setCandidateList(CinBaseTextService.candidateList)
            if CinBaseTextService.isShowCandidates:
                CinBaseTextService.setShowCandidates(True)
            CinBaseTextService.isSelKeysChanged = False
            

    def onPreservedKey(self, CinBaseTextService, guid):
        CinBaseTextService.lastKeyDownCode = 0;
        # some preserved keys registered are pressed
        if guid == SHIFT_SPACE_GUID: # 使用者按下 shift + space
            CinBaseTextService.isShapeModeChanged = True
            self.toggleShapeMode(CinBaseTextService)  # 切換全半形
            return True
        return False


    def onCommand(self, CinBaseTextService, commandId, commandType):
        if commandId == ID_SWITCH_LANG and commandType == COMMAND_LEFT_CLICK:  # 切換中英文模式
            self.toggleLanguageMode(CinBaseTextService)
        elif commandId == ID_SWITCH_SHAPE and commandType == COMMAND_LEFT_CLICK:  # 切換全形/半形
            self.toggleShapeMode(CinBaseTextService)
        elif commandId == ID_SETTINGS:  # 開啟設定工具
            config_tool = os.path.join(CinBaseTextService.curdir, "config", "config.hta")
            os.startfile(config_tool)
        elif commandId == ID_MODE_ICON: # windows 8 mode icon
            self.toggleLanguageMode(CinBaseTextService)  # 切換中英文模式
        elif commandId == ID_WEBSITE: # visit chewing website
            os.startfile("https://github.com/EasyIME/PIME")
        elif commandId == ID_BUGREPORT: # visit bug tracker page
            os.startfile("https://github.com/EasyIME/PIME/issues")
        elif commandId == ID_FORUM:
            os.startfile("https://github.com/EasyIME/forum")
        elif commandId == ID_MOEDICT: # a very awesome online Chinese dictionary
            os.startfile("https://www.moedict.tw/")
        elif commandId == ID_DICT: # online Chinese dictonary
            os.startfile("http://dict.revised.moe.edu.tw/")
        elif commandId == ID_SIMPDICT: # a simplified version of the online dictonary
            os.startfile("http://dict.concised.moe.edu.tw/main/cover/main.htm")
        elif commandId == ID_LITTLEDICT: # a simplified dictionary for little children
            os.startfile("http://dict.mini.moe.edu.tw/cgi-bin/gdic/gsweb.cgi?o=ddictionary")
        elif commandId == ID_PROVERBDICT: # a dictionary for proverbs (seems to be broken at the moment?)
            os.startfile("http://dict.idioms.moe.edu.tw/?")
        elif commandId == ID_OUTPUT_SIMP_CHINESE:  # 切換簡體中文輸出
            self.setOutputSimplifiedChinese(CinBaseTextService, not CinBaseTextService.outputSimpChinese)


    # 開啟語言列按鈕選單
    def onMenu(self, CinBaseTextService, buttonId):
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
                {"text": "輸出簡體中文 (&S)", "id": ID_OUTPUT_SIMP_CHINESE, "checked": CinBaseTextService.outputSimpChinese}
            ]
        return None


    # 鍵盤開啟/關閉時會被呼叫 (在 Windows 10 Ctrl+Space 時)
    def onKeyboardStatusChanged(self, CinBaseTextService, opened):
        if opened: # 鍵盤開啟
            self.resetComposition(CinBaseTextService)
        else: # 鍵盤關閉，輸入法停用
            self.resetComposition(CinBaseTextService)

        # Windows 8 systray IME mode icon
        if CinBaseTextService.client.isWindows8Above:
            # 若鍵盤關閉，我們需要把 widnows 8 mode icon 設定為 disabled
            CinBaseTextService.changeButton("windows-mode-icon", enable=opened)
        # FIXME: 是否需要同時 disable 其他語言列按鈕？


    # 當中文編輯結束時會被呼叫。若中文編輯不是正常結束，而是因為使用者
    # 切換到其他應用程式或其他原因，導致我們的輸入法被強制關閉，此時
    # forced 參數會是 True，在這種狀況下，要清除一些 buffer
    def onCompositionTerminated(self, CinBaseTextService, forced):
        pass



    # 切換中英文模式
    def toggleLanguageMode(self, CinBaseTextService):
        if CinBaseTextService.langMode == CHINESE_MODE:
            CinBaseTextService.langMode = ENGLISH_MODE
        elif CinBaseTextService.langMode == ENGLISH_MODE:
            CinBaseTextService.langMode = CHINESE_MODE
        self.updateLangButtons(CinBaseTextService)


    # 切換全形/半形
    def toggleShapeMode(self, CinBaseTextService):
        if CinBaseTextService.shapeMode == HALFSHAPE_MODE:
            CinBaseTextService.shapeMode = FULLSHAPE_MODE
        elif CinBaseTextService.shapeMode == FULLSHAPE_MODE:
            CinBaseTextService.shapeMode = HALFSHAPE_MODE
        self.updateLangButtons(CinBaseTextService)


    # 依照目前輸入法狀態，更新語言列顯示
    def updateLangButtons(self, CinBaseTextService):
        # 如果中英文模式發生改變
        icon_name = "chi.ico" if CinBaseTextService.langMode == CHINESE_MODE else "eng.ico"
        icon_path = os.path.join(self.icondir, icon_name)
        CinBaseTextService.changeButton("switch-lang", icon=icon_path)
        
        
        if CinBaseTextService.client.isWindows8Above:  # windows 8 mode icon
            CinBaseTextService.capsStates = True if self.getKeyState(VK_CAPITAL) else False

            if CinBaseTextService.langMode == CHINESE_MODE:
                if CinBaseTextService.shapeMode == FULLSHAPE_MODE:
                    icon_name = "chi_full_capson.ico" if CinBaseTextService.capsStates else "chi_full_capsoff.ico"
                else:
                    icon_name = "chi_half_capson.ico" if CinBaseTextService.capsStates else "chi_half_capsoff.ico"
            else:
                if CinBaseTextService.shapeMode == FULLSHAPE_MODE:
                    icon_name = "eng_full_capson.ico" if CinBaseTextService.capsStates else "eng_full_capsoff.ico"
                else:
                    icon_name = "eng_half_capson.ico" if CinBaseTextService.capsStates else "eng_half_capsoff.ico"
            
            icon_path = os.path.join(self.icondir, icon_name)
            CinBaseTextService.changeButton("windows-mode-icon", icon=icon_path)
        
        # 如果全形半形模式改變
        icon_name = "full.ico" if CinBaseTextService.shapeMode == FULLSHAPE_MODE else "half.ico"
        icon_path = os.path.join(self.icondir, icon_name)
        CinBaseTextService.changeButton("switch-shape", icon=icon_path)


    # 設定輸出成簡體中文
    def setOutputSimplifiedChinese(self, CinBaseTextService, outputSimpChinese):
        CinBaseTextService.outputSimpChinese = outputSimpChinese
        # 建立 OpenCC instance 用來做繁簡體中文轉換
        if outputSimpChinese:
            if not CinBaseTextService.opencc:
                CinBaseTextService.opencc = opencc.OpenCC(opencc.OPENCC_DEFAULT_CONFIG_TRAD_TO_SIMP)
        else:
            CinBaseTextService.opencc = None


    # 按下「`」鍵的選單命令
    def onMenuCommand(self, CinBaseTextService, commandId, commandType):
        if commandType == 0:
            if commandId == 0:
                config_tool = os.path.join(CinBaseTextService.curdir, "config", "config.hta")
                os.startfile(config_tool)
            elif commandId == 1:
                self.setOutputSimplifiedChinese(CinBaseTextService, not CinBaseTextService.outputSimpChinese)
        elif commandType == 1: # 功能開關
            commandItem = CinBaseTextService.smenuitems[commandId]
            if commandItem == "fullShapeSymbols":
                CinBaseTextService.fullShapeSymbols = not CinBaseTextService.fullShapeSymbols
            elif commandItem == "easySymbolsWithShift":
                CinBaseTextService.easySymbolsWithShift = not CinBaseTextService.easySymbolsWithShift
            elif commandItem == "supportSymbolCoding":
                CinBaseTextService.supportSymbolCoding = not CinBaseTextService.supportSymbolCoding
            elif commandItem == "supportWildcard":
                CinBaseTextService.supportWildcard = not CinBaseTextService.supportWildcard
            elif commandItem == "autoClearCompositionChar":
                CinBaseTextService.autoClearCompositionChar = not CinBaseTextService.autoClearCompositionChar
            elif commandItem == "playSoundWhenNonCand":
                CinBaseTextService.playSoundWhenNonCand = not CinBaseTextService.playSoundWhenNonCand
            elif commandItem == "showPhrase":
                CinBaseTextService.showPhrase = not CinBaseTextService.showPhrase
            elif commandItem == "sortByPhrase":
                CinBaseTextService.sortByPhrase = not CinBaseTextService.sortByPhrase


    def switchMenuType(self, CinBaseTextService, menutype, prevmenutypelist):
        CinBaseTextService.menutype = menutype
        if menutype == 0:
            CinBaseTextService.prevmenutypelist = prevmenutypelist
        else:
            if prevmenutypelist:
                CinBaseTextService.prevmenutypelist.append(prevmenutypelist[0])
            else:
                CinBaseTextService.prevmenutypelist = prevmenutypelist
        return True


    def closeMenuCand(self, CinBaseTextService):
        CinBaseTextService.showmenu = False
        CinBaseTextService.emojimenumode = False
        CinBaseTextService.menutype = 0
        CinBaseTextService.prevmenutypelist = []
        self.resetComposition(CinBaseTextService)
        return True


    def switchMenuCand(self, CinBaseTextService, menutype):
        if menutype == 0:
            menu_OutputSimpChinese = "輸出繁體" if CinBaseTextService.outputSimpChinese else "輸出簡體"
            CinBaseTextService.menucandidates = ["功能設定", menu_OutputSimpChinese, "功能開關", "特殊符號", "注音符號", "外語文字", "表情符號"]
        if menutype == 2:
            CinBaseTextService.menucandidates = CinBaseTextService.symbols.getKeyNames()
        if menutype == 5:
            CinBaseTextService.menucandidates = CinBaseTextService.menucandidates = CinBaseTextService.flangs.getKeyNames()
        if menutype == 7:
            CinBaseTextService.menucandidates = self.emojimenulist
        if menutype == 8:
            if CinBaseTextService.emojitype == 0:
                CinBaseTextService.menucandidates = self.emoji.emoticons_keynames
            elif CinBaseTextService.emojitype == 1:
                CinBaseTextService.menucandidates = self.emoji.pictographs_keynames
            elif CinBaseTextService.emojitype == 2:
                CinBaseTextService.menucandidates = self.emoji.miscellaneous_keynames
            elif CinBaseTextService.emojitype == 3:
                CinBaseTextService.menucandidates = self.emoji.dingbats_keynames
            elif CinBaseTextService.emojitype == 4:
                CinBaseTextService.menucandidates = self.emoji.transport_keynames
            elif CinBaseTextService.emojitype == 5:
                CinBaseTextService.menucandidates = self.emoji.modifiercolor

        pagecandidates = list(self.chunks(CinBaseTextService.menucandidates, CinBaseTextService.candPerPage))
        return pagecandidates


    # 重置輸入的字根
    def resetComposition(self, CinBaseTextService):
        CinBaseTextService.compositionChar = ''
        CinBaseTextService.setCompositionString('')
        CinBaseTextService.setShowCandidates(False)
        CinBaseTextService.isShowCandidates = False
        CinBaseTextService.setCandidateCursor(0)
        CinBaseTextService.setCandidatePage(0)
        CinBaseTextService.wildcardcandidates = []
        CinBaseTextService.wildcardpagecandidates = []
        CinBaseTextService.multifunctionmode = False
        CinBaseTextService.ctrlsymbolsmode = False
        CinBaseTextService.dayisymbolsmode = False
        CinBaseTextService.lastCompositionCharLength = 0
    
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
        
    # 判斷選字鍵?
    def isInSelKeys(self, CinBaseTextService, charCode):
        for key in CinBaseTextService.selKeys:
            if ord(key) == charCode:
                return True
        return False

    # 一般字元轉全形
    def charCodeToFullshape(self, charCode):
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
        
    def sortByPhrase(self, CinBaseTextService, candidates):
        sortbyphraselist = []
        if CinBaseTextService.userphrase.isInCharDef(CinBaseTextService.lastCommitString):
            sortbyphraselist = CinBaseTextService.userphrase.getCharDef(CinBaseTextService.lastCommitString)
        if CinBaseTextService.phrase.isInCharDef(CinBaseTextService.lastCommitString):
            if len(sortbyphraselist) == 0:
                sortbyphraselist = CinBaseTextService.phrase.getCharDef(CinBaseTextService.lastCommitString)
            else:
                sortbyphraselist.extend(CinBaseTextService.phrase.getCharDef(CinBaseTextService.lastCommitString))
        
        i = 0
        if len(sortbyphraselist) > 0:
            for str in sortbyphraselist:
                if str in candidates:
                    candidates.remove(str)
                    candidates.insert(i, str)
                    i += 1
        return candidates
        
    # List 分段
    def chunks(self, l, n):
        for i in range(0, len(l), n):
            yield l[i:i+n]

    def getKeyState(self, keyCode):
        return ctypes.WinDLL("User32.dll").GetKeyState(keyCode)

    ################################################################
    # config 相關
    ################################################################
    # 初始化 CinBase 輸入法引擎
    def initCinBaseContext(self, CinBaseTextService):
        cfg = CinBaseTextService.cfg # 所有 TextService 共享一份設定物件
        
        # 預設英數 or 中文模式
        CinBaseTextService.langMode = ENGLISH_MODE if cfg.defaultEnglish else CHINESE_MODE

        # 預設全形 or 半形
        CinBaseTextService.shapeMode = FULLSHAPE_MODE if cfg.defaultFullSpace else HALFSHAPE_MODE

        self.updateLangButtons(CinBaseTextService)
        
        # 所有 CheCJTextService 共享一份輸入法碼表
        CinBaseTextService.selCinType = cfg.selCinType

        datadirs = (cfg.getConfigDir(), cfg.getDataDir())
        swkbPath = cfg.findFile(datadirs, "swkb.dat")
        with io.open(swkbPath, encoding='utf-8') as fs:
            CinBaseTextService.swkb = swkb(fs)

        symbolsPath = cfg.findFile(datadirs, "symbols.dat")
        with io.open(symbolsPath, encoding='utf-8') as fs:
            CinBaseTextService.symbols = symbols(fs)

        fsymbolsPath = cfg.findFile(datadirs, "fsymbols.dat")
        with io.open(fsymbolsPath, encoding='utf-8') as fs:
            CinBaseTextService.fsymbols = fsymbols(fs)

        flangsPath = cfg.findFile(datadirs, "flangs.dat")
        with io.open(flangsPath, encoding='utf-8') as fs:
            CinBaseTextService.flangs = flangs(fs)

        userphrasePath = cfg.findFile(datadirs, "userphrase.dat")
        with io.open(userphrasePath, encoding='utf-8') as fs:
            CinBaseTextService.userphrase = userphrase(fs)

        msymbolsPath = cfg.findFile(datadirs, "msymbols.dat")
        with io.open(msymbolsPath, encoding='utf-8') as fs:
            CinBaseTextService.msymbols = msymbols(fs)

        if CinBaseTextService.useDayiSymbols:
            dsymbolsPath = cfg.findFile(datadirs, "dsymbols.dat")
            with io.open(dsymbolsPath, encoding='utf-8') as fs:
                CinBaseTextService.dsymbols = dsymbols(fs)

        if not PhraseData.phrase:
            PhraseData.loadPhraseFile(CinBaseTextService)
            CinBaseTextService.phrase = PhraseData.phrase
        else:
            CinBaseTextService.phrase = PhraseData.phrase

        self.applyConfig(CinBaseTextService) # 套用其餘的使用者設定

    def applyConfig(self, CinBaseTextService):
        cfg = CinBaseTextService.cfg # 所有 TextService 共享一份設定物件
        CinBaseTextService.configVersion = cfg.getVersion()

        # 每列顯示幾個候選字
        CinBaseTextService.candPerRow = cfg.candPerRow;
        
        # 每頁顯示幾個候選字
        CinBaseTextService.candPerPage = cfg.candPerPage;

        # 設定 UI 外觀
        CinBaseTextService.customizeUI(candFontSize = cfg.fontSize,
                                        candPerRow = cfg.candPerRow,
                                        candUseCursor = cfg.cursorCandList)

        # 設定選字按鍵 (123456..., asdf.... 等)
        # if CinBaseTextService.cin.getSelection():
        #     CinBaseTextService.setSelKeys(CinBaseTextService.cin.getSelection())
        
        # 使用空白鍵作為候選清單換頁鍵?
        CinBaseTextService.switchPageWithSpace = cfg.switchPageWithSpace

        # 轉換輸出成簡體中文?
        self.setOutputSimplifiedChinese(CinBaseTextService, cfg.outputSimpChinese)

        # Shift 輸入全形標點?
        CinBaseTextService.fullShapeSymbols = cfg.fullShapeSymbols

        # Shift 快速輸入符號?
        CinBaseTextService.easySymbolsWithShift = cfg.easySymbolsWithShift
        
        # 隱藏提示訊息?
        CinBaseTextService.hidePromptMessages = cfg.hidePromptMessages

        # 輸出字串後顯示聯想字詞?
        CinBaseTextService.showPhrase = cfg.showPhrase
        
        # 優先以聯想字詞排序候選清單?
        CinBaseTextService.sortByPhrase = cfg.sortByPhrase

        # 拆錯字碼時自動清除輸入字串?
        CinBaseTextService.autoClearCompositionChar = cfg.autoClearCompositionChar

        # 拆錯字碼時發出警告嗶聲提示?
        CinBaseTextService.playSoundWhenNonCand  = cfg.playSoundWhenNonCand 

        # 直接顯示候選字清單 (不須按空白鍵)?
        CinBaseTextService.directShowCand = cfg.directShowCand

        # 直接輸出候選字 (當候選字僅有一個)?
        CinBaseTextService.directCommitString = cfg.directCommitString
        
        # 直接輸出候選符號 (當候選符號僅有一個)?
        CinBaseTextService.directCommitSymbol = cfg.directCommitSymbol

        # 支援 CIN 碼表中以符號字元所定義的編碼?
        CinBaseTextService.supportSymbolCoding = cfg.supportSymbolCoding

        # 支援以萬用字元代替組字字根?
        CinBaseTextService.supportWildcard = cfg.supportWildcard

        # 使用的萬用字元?
        if cfg.selWildcardType == 0:
            CinBaseTextService.selWildcardChar = 'z'
        elif cfg.selWildcardType == 1:
            CinBaseTextService.selWildcardChar = '*'

        # 最大候選字個數?
        CinBaseTextService.candMaxItems = cfg.candMaxItems

    # 檢查設定檔是否有被更改，是否需要套用新設定
    def checkConfigChange(self, CinBaseTextService, CinTable):
        cfg = CinBaseTextService.cfg # 所有 TextService 共享一份設定物件
        cfg.update() # 更新設定檔狀態
        
        # 如果有更換輸入法碼表，就重新載入碼表資料
        if not CinBaseTextService.selCinType == cfg.selCinType:
            CinBaseTextService.selCinType = cfg.selCinType
            CinTable.loadCinFile(CinBaseTextService)
            CinBaseTextService.cin = CinTable.cin

        # 比較我們先前存的版本號碼，和目前設定檔的版本號
        if cfg.isFullReloadNeeded(CinBaseTextService.configVersion):
            # 資料改變需整個 reload，重建一個新的 checj context
            self.initCinBaseContext(CinBaseTextService)
        elif cfg.isConfigChanged(CinBaseTextService.configVersion):
            # 只有偵測到設定檔變更，需要套用新設定
            self.applyConfig(CinBaseTextService)

CinBase = CinBase()

class PhraseData:
    def __init__(self):
        self.phrase = None
        
    def loadPhraseFile(self, CinBaseTextService):
        cfg = CinBaseTextService.cfg # 所有 TextService 共享一份設定物件
        datadirs = (cfg.getConfigDir(), cfg.getDataDir())
        
        phrasePath = cfg.findFile(datadirs, "phrase.dat")
        with io.open(phrasePath, encoding='utf-8') as fs:
            self.phrase = phrase(fs)
PhraseData = PhraseData()