#! python3
# Copyright (C) 2015 - 2016 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
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
import os.path
import time
from .libchewing import ChewingContext
from .chewing_config import chewingConfig
import opencc  # OpenCC 繁體簡體中文轉換
import sys
from ctypes import windll  # for ShellExecuteW()


# from libchewing/include/global.h
CHINESE_MODE = 1
ENGLISH_MODE = 0
FULLSHAPE_MODE = 1
HALFSHAPE_MODE = 0

# 按鍵內碼和名稱的對應
keyNames = {
    VK_ESCAPE: "Esc",
    VK_RETURN: "Enter",
    VK_TAB: "Tab",
    VK_DELETE: "Del",
    VK_BACK: "Backspace",
    VK_UP: "Up",
    VK_DOWN: "Down",
    VK_LEFT: "Left",
    VK_RIGHT: "Right",
    VK_HOME: "Home",
    VK_END: "End",
    VK_PRIOR: "PageUp",
    VK_NEXT: "PageDown"
}

# shift + space 熱鍵的 GUID
SHIFT_SPACE_GUID = "{f1dae0fb-8091-44a7-8a0c-3082a1515447}"

# 選單項目和語言列按鈕的 command ID
ID_SWITCH_LANG = 1
ID_SWITCH_SHAPE = 2
ID_SETTINGS = 3
ID_MODE_ICON = 4
ID_ABOUT = 5
ID_WEBSITE = 6
ID_GROUP = 7
ID_BUGREPORT = 8
ID_DICT_BUGREPORT = 9
ID_CHEWING_HELP = 10
ID_HASHED = 11
ID_MOEDICT = 13
ID_DICT = 14
ID_SIMPDICT = 15
ID_LITTLEDICT = 16
ID_PROVERBDICT = 17
ID_OUTPUT_SIMP_CHINESE = 18


class ChewingTextService(TextService):
    def __init__(self, client):
        TextService.__init__(self, client)
        self.curdir = os.path.abspath(os.path.dirname(__file__))
        self.datadir = os.path.join(self.curdir, "data")
        # print(self.datadir)
        self.icon_dir = self.curdir
        self.chewingContext = None # libchewing context

        self.langMode = -1
        self.shapeMode = -1
        self.outputSimpChinese = False
        self.lastKeyDownCode = 0
        self.lastKeyDownTime = 0.0
        self.configVersion = chewingConfig.getVersion()

        # 使用 OpenCC 繁體中文轉簡體
        self.opencc = None

    # 檢查設定檔是否有被更改，是否需要套用新設定
    def checkConfigChange(self):
        cfg = chewingConfig
        cfg.update() # 更新設定檔狀態

        # 比較我們先前存的版本號碼，和目前設定檔的版本號
        if cfg.isFullReloadNeeded(self.configVersion):
            # 資料改變需整個 reload，重建一個新的 chewing context
            self.chewingContext = None
            self.initChewingContext()
        elif cfg.isConfigChanged(self.configVersion):
            # 只有偵測到設定檔變更，需要套用新設定
            self.applyConfig()

    def applyConfig(self):
        cfg = chewingConfig # globally shared config object
        self.configVersion = cfg.getVersion()
        chewingContext = self.chewingContext

        # 按下 Ctrl+ 數字加入游標"前方"的詞 (或是後方)
        chewingContext.set_addPhraseDirection(cfg.addPhraseForward);

        # 選字後自動把游標往後移一個字
        chewingContext.set_autoShiftCur(cfg.advanceAfterSelection);

        # 每頁顯示幾個候選字
        chewingContext.set_candPerPage(cfg.candPerPage);

        # 按下 ESC 鍵清除正在編輯的字
        chewingContext.set_escCleanAllBuf(cfg.escCleanAllBuf);

        # 鍵盤 layout 種類
        chewingContext.set_KBType(cfg.keyboardLayout);

        # 按下 Space 鍵開啟選字視窗
        chewingContext.set_spaceAsSelection(cfg.showCandWithSpaceKey);

        # 設定 UI 外觀
        self.customizeUI(candFontName = 'MingLiu',
                        candFontSize = cfg.fontSize,
                        candPerRow = cfg.candPerRow,
                        candUseCursor = cfg.cursorCandList)

        # 設定選字按鍵 (123456..., asdf.... 等)
        self.setSelKeys(cfg.getSelKeys())

        # 轉換輸出成簡體中文?
        self.setOutputSimplifiedChinese(cfg.outputSimpChinese)

    # 初始化新酷音輸入法引擎
    def initChewingContext(self):
        # load libchewing context
        if not self.chewingContext:
            cfg = chewingConfig # 所有 ChewingTextService 共享一份設定物件
            # syspath 參數可包含多個路徑，用 ; 分隔
            # 此處把 user 設定檔目錄插入到 system-wide 資料檔路徑前
            # 如此使用者變更設定後，可以比系統預設值有優先權
            search_paths = ";".join((cfg.getConfigDir(), self.datadir)).encode("UTF-8")
            user_phrase = cfg.getUserPhrase().encode("UTF-8")

            # 建立 ChewingContext，此處路徑需要 UTF-8 編碼
            chewingContext = ChewingContext(syspath = search_paths, userpath = user_phrase)
            self.chewingContext = chewingContext
            chewingContext.set_maxChiSymbolLen(50) # 編輯區長度: 50 bytes

            # 預設英數 or 中文模式
            self.langMode = ENGLISH_MODE if cfg.defaultEnglish else CHINESE_MODE
            chewingContext.set_ChiEngMode(self.langMode)

            # 預設全形 or 半形
            self.shapeMode = FULLSHAPE_MODE if cfg.defaultFullSpace else HALFSHAPE_MODE
            chewingContext.set_ShapeMode(self.shapeMode)

        self.applyConfig() # 套用其餘的使用者設定

    # 輸入法被使用者啟用
    def onActivate(self):
        cfg = chewingConfig # globally shared config object
        TextService.onActivate(self)
        self.initChewingContext()

        # 向系統宣告 Shift + Space 這個組合為特殊用途 (全半形切換)
        # 當 Shift + Space 被按下的時候，onPreservedKey() 會被呼叫
        self.addPreservedKey(VK_SPACE, TF_MOD_SHIFT, SHIFT_SPACE_GUID); # shift + space

        # 新增語言列按鈕 (Windows 8 之後已取消語言列)

        # 切換中英文
        icon_name = "chi.ico" if self.langMode == CHINESE_MODE else "eng.ico"
        self.addButton("switch-lang",
            icon = os.path.join(self.icon_dir, icon_name),
            tooltip = "中英文切換",
            commandId = ID_SWITCH_LANG
        )

        # Windows 8 以上已取消語言列功能，改用 systray IME mode icon
        if self.client.isWindows8Above:
            self.addButton("windows-mode-icon",
                icon = os.path.join(self.icon_dir, icon_name),
                tooltip = "中英文切換",
                commandId = ID_MODE_ICON
            )

        # 切換全半形
        icon_name = "full.ico" if self.shapeMode == FULLSHAPE_MODE else "half.ico"
        self.addButton("switch-shape",
            icon = os.path.join(self.icon_dir, icon_name),
            tooltip = "全形/半形切換",
            commandId = ID_SWITCH_SHAPE
        )

        # 設定
        self.addButton("settings",
            icon = os.path.join(self.icon_dir, "config.ico"),
            tooltip = "設定",
            type = "menu"
        )

    # 使用者離開輸入法
    def onDeactivate(self):
        TextService.onDeactivate(self)
        # 釋放 libchewing context 的資源
        self.chewingContext = None
        self.lastKeyDownCode = 0

        self.removeButton("switch-lang")
        self.removeButton("switch-shape")
        self.removeButton("settings")
        if self.client.isWindows8Above:
            self.removeButton("windows-mode-icon")

    # 設定選字按鍵 (123456..., asdf....等等)
    def setSelKeys(self, selKeys):
        TextService.setSelKeys(self, selKeys)
        self.selKeys = selKeys
        if self.chewingContext:
            self.chewingContext.set_selKeys(selKeys)

    # 設定輸出成簡體中文
    def setOutputSimplifiedChinese(self, outputSimpChinese):
        self.outputSimpChinese = outputSimpChinese
        # 建立 OpenCC instance 用來做繁簡體中文轉換
        if outputSimpChinese:
            if not self.opencc:
                self.opencc = opencc.OpenCC(opencc.OPENCC_DEFAULT_CONFIG_TRAD_TO_SIMP)
        else:
            self.opencc = None

    # 使用者按下按鍵，在 app 收到前先過濾那些鍵是輸入法需要的。
    # return True，系統會呼叫 onKeyDown() 進一步處理這個按鍵
    # return False，表示我們不需要這個鍵，系統會原封不動把按鍵傳給應用程式
    def filterKeyDown(self, keyEvent):
        cfg = chewingConfig
        # 紀錄最後一次按下的鍵和按下的時間，在 filterKeyUp() 中要用
        self.lastKeyDownCode = keyEvent.keyCode
        if self.lastKeyDownTime == 0.0:
            self.lastKeyDownTime = time.time()

        # 使用者開始輸入，還沒送出前的編輯區內容稱 composition string
        # isComposing() 是 False，表示目前沒有正在編輯中文
        # 另外，若使用 "`" key 輸入特殊符號，可能會有編輯區是空的，但選字清單開啟，輸入法需要處理的情況
		# 此時 isComposing() 也會是 True
        if self.isComposing():
            return True
        # --------------   以下都是「沒有」正在輸入中文的狀況   --------------

        # 如果按下 Alt，可能是應用程式熱鍵，輸入法不做處理
        if keyEvent.isKeyDown(VK_MENU):
            return False

        # 如果按下 Ctrl 鍵
        if keyEvent.isKeyDown(VK_CONTROL):
            # 開啟 Ctrl 快速輸入符號，輸入法需要此按鍵
            if cfg.easySymbolsWithCtrl and keyEvent.isPrintableChar() and self.langMode == CHINESE_MODE:
                return True
            else: # 否則可能是應用程式熱鍵，輸入法不做處理
                return False

        # 若按下 Shift 鍵
        if keyEvent.isKeyDown(VK_SHIFT):
            # 若開啟 Shift 快速輸入符號，輸入法需要此按鍵
            if cfg.easySymbolsWithShift and keyEvent.isPrintableChar() and self.langMode == CHINESE_MODE:
                return True

        # 不論中英文模式，NumPad 都允許直接輸入數字，輸入法不處理
        if keyEvent.isKeyToggled(VK_NUMLOCK): # NumLock is on
            # if this key is Num pad 0-9, +, -, *, /, pass it back to the system
            if keyEvent.keyCode >= VK_NUMPAD0 and keyEvent.keyCode <= VK_DIVIDE:
                return False # bypass IME

        # 不管中英文模式，只要是全形可見字元或空白，輸入法都需要進一步處理(半形轉為全形)
        if self.shapeMode == FULLSHAPE_MODE:
            return (keyEvent.isPrintableChar() or keyEvent.keyCode == VK_SPACE)

        # --------------   以下皆為半形模式   --------------

        # 如果是英文半形模式，輸入法不做任何處理
        if self.langMode == ENGLISH_MODE:
            return False
        # --------------   以下皆為中文模式   --------------

        # 中文模式下開啟 Capslock，須切換成英文
        if cfg.enableCapsLock and keyEvent.isKeyToggled(VK_CAPITAL):
            # 如果此按鍵是英文字母，中文模式下要從大寫轉小寫，需要輸入法處理
            if keyEvent.isChar() and chr(keyEvent.charCode).isalpha():
                return True
            # 是其他符號或數字，則視同英文模式，不用處理
            else:
                return False

        # 中文模式下，當中文編輯區是空的，輸入法只需處理注音符號和標點
        # 大略可用是否為 printable char 來檢查
        # 注意: 此處不能直接寫死檢查按鍵是否為注音或標點，因為在不同 keyboard layout，例如
        # 倚天鍵盤或許氏...等，代表注音符號的按鍵全都不同
        if keyEvent.isPrintableChar() and keyEvent.keyCode != VK_SPACE:
            return True

        # 其餘狀況一律不處理，原按鍵輸入直接送還給應用程式
        return False

    def onKeyDown(self, keyEvent):
        chewingContext = self.chewingContext
        cfg = chewingConfig
        charCode = keyEvent.charCode
        keyCode = keyEvent.keyCode
        charStr = chr(charCode)

        # 某些狀況下，需要暫時強制切成英文模式，之後再恢復
        temporaryEnglishMode = False
        oldLangMode = chewingContext.get_ChiEngMode()
        ignoreKey = False  # 新酷音是否須忽略這個按鍵
        keyHandled = False # 輸入法是否有處理這個按鍵

        # 使用 Ctrl 或 Shift 鍵做快速符號輸入 (easy symbol input)
        # 這裡的 easy symbol input，是定義在 swkb.dat 設定檔中的符號
        if cfg.easySymbolsWithShift and keyEvent.isKeyDown(VK_SHIFT):
            chewingContext.set_easySymbolInput(1)
        elif cfg.easySymbolsWithCtrl and keyEvent.isKeyDown(VK_CONTROL):
            chewingContext.set_easySymbolInput(1)
        else:
            chewingContext.set_easySymbolInput(0)

        # 若目前輸入的按鍵是可見字元 (字母、數字、標點...等)
        if keyEvent.isPrintableChar():
            keyHandled = True
            invertCase = False  # 是否需要反轉大小寫

            # 中文模式下須特別處理 CapsLock 和 Shift 鍵
            if self.langMode == CHINESE_MODE:
                # 若開啟 Caps lock，需要暫時強制切換成英文模式
                if cfg.enableCapsLock and keyEvent.isKeyToggled(VK_CAPITAL):
                    temporaryEnglishMode = True
                    invertCase = True  # 大寫字母轉成小寫

                # 若按下 Shift 鍵
                if keyEvent.isKeyDown(VK_SHIFT):
                    if charStr.isalpha():  # 如果是英文字母
                        # 如果不使用快速輸入符號功能，則暫時切成英文模式
                        if not cfg.easySymbolsWithShift:
                            temporaryEnglishMode = True  # 暫時切換成英文模式
                            if not cfg.upperCaseWithShift:  # 如果沒有開啟 Shift 輸入大寫英文
                                invertCase = True # 大寫字母轉成小寫
                    else: # 如果不是英文字母
                        # 如果不使用 Shift 輸入全形標點，則暫時切成英文模式
                        if not cfg.fullShapeSymbols:
                            temporaryEnglishMode = True

            if self.langMode == ENGLISH_MODE: # 英文模式
                chewingContext.handle_Default(charCode)
            elif temporaryEnglishMode: # 原為中文模式，暫時強制切成英文
                chewingContext.set_ChiEngMode(ENGLISH_MODE)
                if invertCase: # 先反轉大小寫，再送給新酷音引擎
                    charCode = ord(charStr.lower() if charStr.isupper() else charStr.upper())
                chewingContext.handle_Default(charCode)
            else : # 中文模式
                if charStr.isalpha(): # 英文字母 A-Z
                    # 如果開啟 Ctrl 或 Shift + A-Z 快速輸入符號 (easy symbols，定義在 swkb.dat)
                    # 則只接受大寫英文字母
                    if chewingContext.get_easySymbolInput():
                        charCode = ord(charStr.upper())
                    else:
                        charCode = ord(charStr.lower())
                    chewingContext.handle_Default(charCode)
                elif keyEvent.keyCode == VK_SPACE: # 空白鍵
                    # NOTE: libchewing 有 bug: 當啟用 "使用空白鍵選字" 時，chewing_handle_Space()
                    # 會忽略空白鍵，造成打不出空白。因此在此只有當 composition string 有內容
                    # 有需要選字時，才呼叫 handle_Space()，否則改用 handle_Default()，以免空白鍵被吃掉
                    if self.isComposing():
                        chewingContext.handle_Space()
                    else:
                        chewingContext.handle_Default(charCode)
                elif keyEvent.isKeyDown(VK_CONTROL) and charStr.isdigit(): # Ctrl + 數字(0-9)
                    chewingContext.handle_CtrlNum(charCode)
                elif keyEvent.isKeyToggled(VK_NUMLOCK) and keyCode >= VK_NUMPAD0 and keyCode <= VK_DIVIDE:
                    # numlock 開啟，處理 NumPad 按鍵
                    chewingContext.handle_Numlock(charCode)
                else : # 其他按鍵不需要特殊處理
                    chewingContext.handle_Default(charCode)
        else:  # 不可見字元 (方向鍵, Enter, Page Down...等等)
            # 如果有啟用在選字視窗內移動游標選字，而且目前正在選字
            if cfg.cursorCandList and self.showCandidates:
                candCursor = self.candidateCursor  # 目前的游標位置
                candCount = len(self.candidateList)  # 目前選字清單項目數
                if keyCode == VK_LEFT:  # 游標左移
                    if candCursor > 0:
                        candCursor -= 1
                        ignoreKey = keyHandled = True
                elif keyCode == VK_UP:  # 游標上移
                    if candCursor >= cfg.candPerRow:
                        candCursor -= cfg.candPerRow
                        ignoreKey = keyHandled = True
                elif keyCode == VK_RIGHT:  # 游標右移
                    if (candCursor + 1) < candCount:
                        candCursor += 1
                        ignoreKey = keyHandled = True
                elif keyCode == VK_DOWN:  # 游標下移
                    if (candCursor + cfg.candPerRow) < candCount:
                        candCursor += cfg.candPerRow
                        ignoreKey = keyHandled = True
                elif keyCode == VK_RETURN:  # 按下 Enter 鍵
                    # 找出目前游標位置的選字鍵 (1234..., asdf...等等)
                    selKey = cfg.getSelKeys()[self.candidateCursor]
                    # 代替使用者送出選字鍵給新酷音引擎，進行選字
                    chewingContext.handle_Default(ord(selKey))
                    keyHandled = True
                # 更新選字視窗游標位置
                self.setCandidateCursor(candCursor)

            if not keyHandled:  # 按鍵還沒被處理過
                # the candidate window does not need the key. pass it to libchewing.
                keyName = keyNames.get(keyCode)  #  取得按鍵的名稱
                if keyName: # call libchewing method for the key
                    # 依照按鍵名稱，找 libchewing 對應的 handle_按鍵() method 呼叫
                    methodName = "handle_" + keyName
                    method = getattr(chewingContext, methodName)
                    method()
                    keyHandled = True
                else: # 我們不需要處理的按鍵，直接忽略
                    ignoreKey = True

        # 新酷音引擎忽略不處理此按鍵
        if keyHandled and chewingContext.keystroke_CheckIgnore():
            ignoreKey = True

        if not ignoreKey:  # 如果這個按鍵是有意義的，新酷音有做處理 (不可忽略)
            # 處理選字清單
            if chewingContext.cand_TotalChoice() > 0: # 若有候選字/詞
                candidates = []
                # 要求新酷音引擎列出每個候選字
                chewingContext.cand_Enumerate()
                for i in range(chewingContext.cand_ChoicePerPage()):
                    if not chewingContext.cand_hasNext():
                        break
                    # 新酷音返回的是 UTF-8 byte string，須轉成 python 字串
                    cand = chewingContext.cand_String().decode("UTF-8")
                    candidates.append(cand)

                # 檢查選字清單是否改變 (沒效率但是簡單)
                if candidates != self.candidateList:
                    self.setCandidateList(candidates)  # 更新候選字清單
                    self.setShowCandidates(True)
                    if cfg.cursorCandList:  # 如果啟用選字清單內使用游標選字
                        self.setCandidateCursor(0)  # 重設游標位置

                if not self.showCandidates:  # 如果目前沒有顯示選字視窗
                    self.setShowCandidates(True)  # 顯示選字視窗
            else:  # 沒有候選字
                if self.showCandidates:
                    self.setShowCandidates(False)  # 隱藏選字視窗
                    self.setCandidateList([])  # 更新候選字清單

            # 有輸入完成的中文字串要送出(commit)到應用程式
            if chewingContext.commit_Check():
                commitStr = chewingContext.commit_String().decode("UTF-8")
                
                # 如果使用打繁出簡，就轉成簡體中文
                if self.outputSimpChinese:
                    commitStr = self.opencc.convert(commitStr)

                self.setCommitString(commitStr)  # 設定要輸出的 commit string

            # 編輯區正在輸入中，尚未送出的中文字串 (composition string)
            compStr = ""
            if chewingContext.buffer_Check():
                compStr = chewingContext.buffer_String().decode("UTF-8")

            # 輸入到一半，還沒組成字的注音符號 (bopomofo)
            if chewingContext.bopomofo_Check():
                bopomofoStr = ""
                bopomofoStr = chewingContext.bopomofo_String(None).decode("UTF-8")
                # 把輸入到一半，還沒組成字的注音字串，也插入到編輯區內，並且更新游標位置
                pos = chewingContext.cursor_Current()
                compStr = compStr[:pos] + bopomofoStr + compStr[pos:]
                self.setCompositionCursor(chewingContext.cursor_Current() + len(bopomofoStr))
            else:
                self.setCompositionCursor(chewingContext.cursor_Current())

            # 更新編輯區內容 (composition string)
            self.setCompositionString(compStr)

            # 顯示額外提示訊息 (例如：Ctrl+數字加入自訂詞之後，會顯示提示)
            if chewingContext.aux_Check():
                message = chewingContext.aux_String().decode("UTF-8")
                # FIXME: sometimes libchewing shows the same aux info
                # for subsequent key events... I think this is a bug.
                self.showMessage(message, 2)

        # 若先前有暫時強制切成英文模式，需要復原
        if temporaryEnglishMode:
            chewingContext.set_ChiEngMode(oldLangMode)

        # 依照目前狀態，更新語言列顯示的圖示
        self.updateLangButtons()

        return keyHandled  # 告知系統我們是否有處理這個按鍵

    # 使用者放開按鍵，在 app 收到前先過濾那些鍵是輸入法需要的。
    # return True，系統會呼叫 onKeyUp() 進一步處理這個按鍵
    # return False，表示我們不需要這個鍵，系統會原封不動把按鍵傳給應用程式
    def filterKeyUp(self, keyEvent):
        # 若啟用使用 Shift 鍵切換中英文模式
        if chewingConfig.switchLangWithShift:
            # 剛才最後一個按下的鍵，和現在放開的鍵，都是 Shift
            if self.lastKeyDownCode == VK_SHIFT and keyEvent.keyCode == VK_SHIFT:
                pressedDuration = time.time() - self.lastKeyDownTime
                # 按下和放開的時間相隔 < 0.5 秒
                if pressedDuration < 0.5:
                    self.toggleLanguageMode()  # 切換中英文模式
        self.lastKeyDownCode = 0
        self.lastKeyDownTime = 0.0
        return False

    def onPreservedKey(self, guid):
        self.lastKeyDownCode = 0;
        # some preserved keys registered are pressed
        if guid == SHIFT_SPACE_GUID: # 使用者按下 shift + space
            self.toggleShapeMode()  # 切換全半形
            return True
        return False

    # 使用者按下語言列按鈕
    def onCommand(self, commandId, commandType):
        print("onCommand", commandId, commandType)
        # FIXME: We should distinguish left and right click using commandType
        if commandId == ID_SWITCH_LANG and commandType == COMMAND_LEFT_CLICK:  # 切換中英文模式
            self.toggleLanguageMode()
        elif commandId == ID_SWITCH_SHAPE and commandType == COMMAND_LEFT_CLICK:  # 切換全形/半形
            self.toggleShapeMode()
        elif commandId == ID_SETTINGS:  # 開啟設定工具
            config_tool = '"{0}"'.format(os.path.join(self.curdir, "config", "configTool.py"))
            python_exe = sys.executable  # 找到 python 執行檔
            # 使用我們自帶的 python runtime exe 執行 config tool
            # 此處也可以用 subprocess，不過使用 windows API 比較方便
            r = windll.shell32.ShellExecuteW(None, "open", python_exe, config_tool, os.path.dirname(config_tool), 1)  # SW_SHOWNORMAL = 1
            print(r)
        elif commandId == ID_MODE_ICON: # windows 8 mode icon
            self.toggleLanguageMode()  # 切換中英文模式
        elif commandId == ID_ABOUT: # 關於新酷音輸入法
            pass
        elif commandId == ID_WEBSITE: # visit chewing website
            os.startfile("http://chewing.im/")
        elif commandId == ID_GROUP: # visit chewing google groups website
            os.startfile("http://groups.google.com/group/chewing-devel")
        elif commandId == ID_BUGREPORT: # visit bug tracker page
            os.startfile("https://github.com/EasyIME/PIME/issues")
        elif commandId == ID_DICT_BUGREPORT:
            os.startfile("https://github.com/chewing/libchewing/issues")
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
        elif commandId == ID_CHEWING_HELP:
            pass
        elif commandId == ID_OUTPUT_SIMP_CHINESE:  # 切換簡體中文輸出
            self.setOutputSimplifiedChinese(not self.outputSimpChinese)

    # 開啟語言列按鈕選單
    def onMenu(self, buttonId):
        # 設定按鈕 (windows 8 mode icon 按鈕也使用同一個選單)
        if buttonId == "settings" or buttonId == "windows-mode-icon":
            # 用 json 語法表示選單結構
            return [
                # {"text": "關於新酷音輸入法(&A)", "id": ID_ABOUT},
                {"text": "參觀新酷音官方網站(&W)", "id": ID_WEBSITE},
                {"text": "新酷音線上討論區(&G)", "id": ID_GROUP},
                {},
                {"text": "軟體本身的建議及錯誤回報(&B)", "id": ID_BUGREPORT},
                {"text": "注音及選字選詞錯誤回報 (&P)", "id": ID_DICT_BUGREPORT},
                {},
                # {"text": "新酷音使用說明 (&H)", "id": ID_CHEWING_HELP},
                # {"text": "編輯使用者詞庫 (&E)", "id": ID_HASHED},
                {"text": "設定新酷音輸入法(&C)", "id": ID_SETTINGS},
                {},
                {"text": "網路辭典 (&D)", "submenu": [
                    {"text": "萌典 (moedict)", "id": ID_MOEDICT},
                    {},
                    {"text": "教育部國語辭典", "id": ID_DICT},
                    {"text": "教育部國語辭典簡編本", "id": ID_SIMPDICT},
                    {"text": "教育部國語小字典", "id": ID_LITTLEDICT},
                    {"text": "教育部成語典", "id": ID_PROVERBDICT},
                ]},
                {"text": "輸出簡體中文 (&S)", "id": ID_OUTPUT_SIMP_CHINESE, "checked": self.outputSimpChinese}
            ]
        return None

    # 依照目前輸入法狀態，更新語言列顯示
    def updateLangButtons(self):
        chewingContext = self.chewingContext
        if not chewingContext:
            return
        langMode = chewingContext.get_ChiEngMode()
        if langMode != self.langMode:  # 如果中英文模式發生改變
            self.langMode = langMode
            icon_name = "chi.ico" if langMode == CHINESE_MODE else "eng.ico"
            icon_path = os.path.join(self.icon_dir, icon_name)
            self.changeButton("switch-lang", icon=icon_path)

            if self.client.isWindows8Above: # windows 8 mode icon
                # FIXME: we need a better set of icons to meet the 
                #        WIndows 8 IME guideline and UX guidelines.
                self.changeButton("windows-mode-icon", icon=icon_path)

        shapeMode = chewingContext.get_ShapeMode()
        if shapeMode != self.shapeMode:  # 如果全形半形模式改變
            self.shapeMode = shapeMode
            icon_name = "full.ico" if shapeMode == FULLSHAPE_MODE else "half.ico"
            icon_path = os.path.join(self.icon_dir, icon_name)
            self.changeButton("switch-shape", icon=icon_path)

    # 切換中英文模式
    def toggleLanguageMode(self):
        chewingContext = self.chewingContext
        if chewingContext:
            if chewingContext.get_ChiEngMode() == CHINESE_MODE:
                new_mode = ENGLISH_MODE
            else:
                new_mode = CHINESE_MODE
            chewingContext.set_ChiEngMode(new_mode)
            self.updateLangButtons()

    # 切換全形/半形
    def toggleShapeMode(self):
        chewingContext = self.chewingContext
        if chewingContext:
            if chewingContext.get_ShapeMode() == HALFSHAPE_MODE:
                new_mode = FULLSHAPE_MODE
            else:
                new_mode = HALFSHAPE_MODE
            chewingContext.set_ShapeMode(new_mode)
            self.updateLangButtons()

    # 鍵盤開啟/關閉時會被呼叫 (在 Windows 10 Ctrl+Space 時)
    def onKeyboardStatusChanged(self, opened):
        TextService.onKeyboardStatusChanged(self, opened)
        if opened: # 鍵盤開啟
            self.initChewingContext() # 確保新酷音引擎啟動
        else: # 鍵盤關閉，輸入法停用
            # 若選字中，隱藏選字視窗
            if self.showCandidates:
                self.setShowCandidates(False)
            # self.hideMessage() # hide message window, if there's any
            self.chewingContext = None  # 釋放新酷音引擎資源

        # Windows 8 systray IME mode icon
        if self.client.isWindows8Above:
            # 若鍵盤關閉，我們需要把 widnows 8 mode icon 設定為 disabled
            self.changeButton("windows-mode-icon", enable=opened)
        # FIXME: 是否需要同時 disable 其他語言列按鈕？

    # 當中文編輯結束時會被呼叫。若中文編輯不是正常結束，而是因為使用者
    # 切換到其他應用程式或其他原因，導致我們的輸入法被強制關閉，此時
    # forced 參數會是 True，在這種狀況下，要清除一些 buffer
    def onCompositionTerminated(self, forced):
        TextService.onCompositionTerminated(self, forced)
        if forced:
            # 中文組字到一半被系統強制關閉，清除編輯區內容
            chewingContext = self.chewingContext
            if chewingContext:
                if self.showCandidates:
                    chewingContext.cand_close()
                    self.setShowCandidates(False)
                if chewingContext.bopomofo_Check():
                    chewingContext.clean_bopomofo_buf()
                if chewingContext.buffer_Check():
                    chewingContext.commit_preedit_buf()
