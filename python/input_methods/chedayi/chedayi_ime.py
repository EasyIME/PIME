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
from textService import *
import io
import os.path
import copy

from cinbase import CinBase
from cinbase import LoadCinTable
from cinbase import LoadRCinTable
from cinbase import LoadHCinTable
from cinbase.config import CinBaseConfig


class CheDayiTextService(TextService):

    compositionChar = ''

    def __init__(self, client):
        TextService.__init__(self, client)

        # 輸入法模組自訂區域
        self.imeDirName = "chedayi"
        self.maxCharLength = 4 # 輸入法最大編碼字元數量
        self.cinFileList = ["thdayi.json", "dayi4.json", "dayi3.json"]

        self.cinbase = CinBase
        self.curdir = os.path.abspath(os.path.dirname(__file__))

        # 初始化輸入行為設定
        self.cinbase.initTextService(self, TextService)
        self.useDayiSymbols = True
        self.selDayiSymbolCharType = 0

        # 載入用戶設定值
        CinBaseConfig.__init__()
        self.configVersion = CinBaseConfig.getVersion()
        self.cfg = copy.deepcopy(CinBaseConfig)
        self.cfg.imeDirName = self.imeDirName
        self.cfg.cinFileList = self.cinFileList
        self.cfg.load()
        self.jsondir = self.cfg.getJsonDir()
        self.cindir = self.cfg.getCinDir()
        self.ignorePrivateUseArea = self.cfg.ignorePrivateUseArea
        self.cinbase.initCinBaseContext(self)

        # 載入輸入法碼表
        if not CinTable.curCinType == self.cfg.selCinType and not CinTable.loading:
            loadCinFile = LoadCinTable(self, CinTable)
            loadCinFile.start()
        else:
            while CinTable.loading:
                continue
            self.cin = CinTable.cin


    # 檢查設定檔是否有被更改，是否需要套用新設定
    def checkConfigChange(self):
        self.cinbase.checkConfigChange(self, CinTable, RCinTable, HCinTable)


    # 輸入法被使用者啟用
    def onActivate(self):
        TextService.onActivate(self)
        self.cinbase.onActivate(self)


    # 使用者離開輸入法
    def onDeactivate(self):
        TextService.onDeactivate(self)
        self.cinbase.onDeactivate(self)


    # 使用者按下按鍵，在 app 收到前先過濾那些鍵是輸入法需要的。
    # return True，系統會呼叫 onKeyDown() 進一步處理這個按鍵
    # return False，表示我們不需要這個鍵，系統會原封不動把按鍵傳給應用程式
    def filterKeyDown(self, keyEvent):
        KeyState = self.cinbase.filterKeyDown(self, keyEvent, CinTable, RCinTable, HCinTable)
        return KeyState


    def onKeyDown(self, keyEvent):
        if self.cfg.selCinType == 0 or self.cfg.selCinType == 1:
            self.maxCharLength = 4
        elif self.cfg.selCinType == 2:
            self.maxCharLength = 3

        charCode = keyEvent.charCode
        keyCode = keyEvent.keyCode
        charStr = chr(charCode)

        # 大易符號 ---------------------------------------------------------
        self.DayiSymbolChar = "=" if self.selDayiSymbolCharType == 0 else "'"
        self.DayiSymbolString = "＝" if self.selDayiSymbolCharType == 0 else "號"

        if self.langMode == 1 and not self.showmenu:
            if len(self.compositionChar) == 0 and not self.phrasemode and charStr == self.DayiSymbolChar and not keyEvent.isKeyDown(VK_CONTROL):
                self.compositionChar += charStr
                self.dayisymbolsmode = True
                if self.compositionBufferMode:
                    self.cinbase.setCompositionBufferString(self, self.DayiSymbolString, 0)
                else:
                    self.setCompositionString(self.DayiSymbolString)
            elif self.dayisymbolsmode and self.isShowCandidates:
                self.canUseSelKey = True
            elif len(self.compositionChar) >= 1 and self.dayisymbolsmode:
                if self.dsymbols.isInCharDef(self.compositionChar[1:] + charStr):
                    self.compositionChar += charStr
                    self.canUseSelKey = False
                    candidates = self.dsymbols.getCharDef(self.compositionChar[1:])

        if not self.directShowCand:
            self.autoShowCandWhenMaxChar = True
        KeyState = self.cinbase.onKeyDown(self, keyEvent, CinTable, RCinTable, HCinTable)
        return KeyState


    # 使用者放開按鍵，在 app 收到前先過濾那些鍵是輸入法需要的。
    # return True，系統會呼叫 onKeyUp() 進一步處理這個按鍵
    # return False，表示我們不需要這個鍵，系統會原封不動把按鍵傳給應用程式
    def filterKeyUp(self, keyEvent):
        KeyState = self.cinbase.filterKeyUp(self, keyEvent)
        return KeyState


    def onKeyUp(self, keyEvent):
        self.cinbase.onKeyUp(self, keyEvent)


    def onPreservedKey(self, guid):
        KeyState = self.cinbase.onPreservedKey(self, guid)
        return KeyState


    def onCommand(self, commandId, commandType):
        self.cinbase.onCommand(self, commandId, commandType)


    # 開啟語言列按鈕選單
    def onMenu(self, buttonId):
        MenuItems = self.cinbase.onMenu(self, buttonId)
        return MenuItems


    # 鍵盤開啟/關閉時會被呼叫 (在 Windows 10 Ctrl+Space 時)
    def onKeyboardStatusChanged(self, opened):
        TextService.onKeyboardStatusChanged(self, opened)
        self.cinbase.onKeyboardStatusChanged(self, opened)


    # 當中文編輯結束時會被呼叫。若中文編輯不是正常結束，而是因為使用者
    # 切換到其他應用程式或其他原因，導致我們的輸入法被強制關閉，此時
    # forced 參數會是 True，在這種狀況下，要清除一些 buffer
    def onCompositionTerminated(self, forced):
        TextService.onCompositionTerminated(self, forced)
        self.cinbase.onCompositionTerminated(self, forced)


    # 設定候選字頁數
    def setCandidatePage(self, page):
        self.currentCandPage = page


class CinTable:
    loading = False
    def __init__(self):
        self.cin = None
        self.curCinType = None
        self.userExtendTable = None
        self.priorityExtendTable = None
        self.ignorePrivateUseArea = None
CinTable = CinTable()


class RCinTable:
    loading = False
    def __init__(self):
        self.cin = None
        self.curCinType = None
RCinTable = RCinTable()


class HCinTable:
    loading = False
    def __init__(self):
        self.cin = None
        self.curCinType = None
HCinTable = HCinTable()
