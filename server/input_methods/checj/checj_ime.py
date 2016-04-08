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
import os.path
import time
from .checj_config import ChecjConfig
import opencc  # OpenCC 繁體簡體中文轉換

# CheCJ
import io
import math
from .cin import Cin
from .swkb import swkb
from .symbols import symbols
from .fsymbols import fsymbols
from .flangs import flangs

# from libchewing/include/global.h
CHINESE_MODE = 1
ENGLISH_MODE = 0
FULLSHAPE_MODE = 1
HALFSHAPE_MODE = 0

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

# CheCJ
MAX_CHAR_LENGTH = 5


class CheCJTextService(TextService):
    # CheCJ
    compositionChar = ''

    def __init__(self, client):
        TextService.__init__(self, client)
        self.curdir = os.path.abspath(os.path.dirname(__file__))
        self.datadir = os.path.join(self.curdir, "data")

        self.icon_dir = self.curdir
        
        self.langMode = -1
        self.shapeMode = -1
        self.outputSimpChinese = False
        self.fullShapeSymbols = False
        self.easySymbolsWithShift = False
        self.supportSymbolCoding = False
        self.lastKeyDownCode = 0
        self.lastKeyDownTime = 0.0
        self.configVersion = ChecjConfig.getVersion()

        # 使用 OpenCC 繁體中文轉簡體
        self.opencc = None
        
        # CheCJ
        self.candidates = []
        self.wildcardcandidates = []
        self.wildcardpagecandidates = []
        self.wildcardcompositionChar = ""
        self.currentCandPage = 0
        self.showmenu = False
        self.closemenu = True
        self.isWildcardChardefs = False
        self.isLangModeChanged = False
        self.isShapeModeChanged = False
        self.menutype = 0
        cfg = ChecjConfig # 所有 CheCJTextService 共享一份設定物件
        

    # 檢查設定檔是否有被更改，是否需要套用新設定
    def checkConfigChange(self):
        cfg = ChecjConfig
        cfg.update() # 更新設定檔狀態
        
        # 如果有更換輸入法碼表，就重新載入碼表資料
        if not self.selCinType == cfg.selCinType:
            self.selCinType = cfg.selCinType
            cfg.loadCinFile()
            self.cin = cfg.cin

        # 比較我們先前存的版本號碼，和目前設定檔的版本號
        if cfg.isFullReloadNeeded(self.configVersion):
            # 資料改變需整個 reload，重建一個新的 checj context
            self.initChecjContext()
        elif cfg.isConfigChanged(self.configVersion):
            # 只有偵測到設定檔變更，需要套用新設定
            self.applyConfig()
            
    def applyConfig(self):
        cfg = ChecjConfig # globally shared config object
        self.configVersion = cfg.getVersion()

        # 每列顯示幾個候選字
        self.candPerRow = cfg.candPerRow;
        
        # 每頁顯示幾個候選字
        self.candPerPage = cfg.candPerPage;

        # 設定 UI 外觀
        self.customizeUI(candFontSize = cfg.fontSize,
                        candPerRow = cfg.candPerRow,
                        candUseCursor = cfg.cursorCandList)
        
        # 設定選字按鍵 (123456..., asdf.... 等)
        if self.cin.getSelection(): # CheCJ
            self.setSelKeys(self.cin.getSelection())

        # 轉換輸出成簡體中文?
        self.setOutputSimplifiedChinese(cfg.outputSimpChinese)
        
        # Shift 輸入全形標點?
        self.fullShapeSymbols = cfg.fullShapeSymbols
        
        # Shift 快速輸入符號?
        self.easySymbolsWithShift = cfg.easySymbolsWithShift
        
        # 支援 CIN 碼表中以符號字元所定義的編碼?
        self.supportSymbolCoding = cfg.supportSymbolCoding
        
        # 支援以萬用字元代替組字字根?
        self.supportWildcard = cfg.supportWildcard
        
        # 使用的萬用字元?
        if cfg.selWildcardType == 0:
            self.selWildcardChar = 'z'
        elif cfg.selWildcardType == 1:
            self.selWildcardChar = '*'

        # 最大候選字個數?
        self.candMaxItems = cfg.candMaxItems
        
    # 初始化新酷音輸入法引擎
    def initChecjContext(self):
        cfg = ChecjConfig # 所有 CheCJTextService 共享一份設定物件
        # syspath 參數可包含多個路徑，用 ; 分隔
        # 此處把 user 設定檔目錄插入到 system-wide 資料檔路徑前
        # 如此使用者變更設定後，可以比系統預設值有優先權
        user_phrase = cfg.getUserPhrase().encode("UTF-8")

        # 預設英數 or 中文模式
        self.langMode = ENGLISH_MODE if cfg.defaultEnglish else CHINESE_MODE

        # 預設全形 or 半形
        self.shapeMode = FULLSHAPE_MODE if cfg.defaultFullSpace else HALFSHAPE_MODE
        
        # 所有 CheCJTextService 共享一份輸入法碼表
        self.selCinType = cfg.selCinType
        self.cin = cfg.cin

        datadirs = (cfg.getConfigDir(), cfg.getDataDir())
        swkbPath = cfg.findFile(datadirs, "swkb.dat")
        with io.open(swkbPath, encoding='utf-8') as fs:
            self.swkb = swkb(fs)
            
        symbolsPath = cfg.findFile(datadirs, "symbols.dat")
        with io.open(symbolsPath, encoding='utf-8') as fs:
            self.symbols = symbols(fs)
            
        fsymbolsPath = cfg.findFile(datadirs, "fsymbols.dat")
        with io.open(fsymbolsPath, encoding='utf-8') as fs:
            self.fsymbols = fsymbols(fs)
            
        flangsPath = cfg.findFile(datadirs, "flangs.dat")
        with io.open(flangsPath, encoding='utf-8') as fs:
            self.flangs = flangs(fs)

        self.applyConfig() # 套用其餘的使用者設定
            
    # 輸入法被使用者啟用
    def onActivate(self):
        cfg = ChecjConfig # globally shared config object
        TextService.onActivate(self)
        self.initChecjContext()
        
        # 向系統宣告 Shift + Space 這個組合為特殊用途 (全半形切換)
        # 當 Shift + Space 被按下的時候，onPreservedKey() 會被呼叫
        self.addPreservedKey(VK_SPACE, TF_MOD_SHIFT, SHIFT_SPACE_GUID); # shift + space

        # 切換中英文
        icon_name = "chi.ico" if self.langMode == CHINESE_MODE else "eng.ico"
        self.addButton("switch-lang",
            icon=os.path.join(self.icon_dir, icon_name),
            tooltip="中英文切換",
            commandId=ID_SWITCH_LANG
        )

        # Windows 8 以上已取消語言列功能，改用 systray IME mode icon
        if self.client.isWindows8Above:
            self.addButton("windows-mode-icon",
                icon=os.path.join(self.icon_dir, icon_name),
                tooltip="中英文切換",
                commandId=ID_MODE_ICON
            )
            
        # 切換全半形
        icon_name = "full.ico" if self.shapeMode == FULLSHAPE_MODE else "half.ico"
        self.addButton("switch-shape",
            icon = os.path.join(self.icon_dir, icon_name),
            tooltip = "全形/半形切換",
            commandId = ID_SWITCH_SHAPE
        )
        
        # 設定
        # FIXME: popup menu is not yet implemented
        self.addButton("settings",
            icon = os.path.join(self.icon_dir, "config.ico"),
            tooltip = "設定",
            type = "menu"
        )

    # 使用者離開輸入法
    def onDeactivate(self):
        TextService.onDeactivate(self)
        self.lastKeyDownCode = 0
        
        # 向系統宣告移除 Shift + Space 這個組合鍵用途 (全半形切換)
        self.removePreservedKey(SHIFT_SPACE_GUID); # shift + space
        
        self.removeButton("switch-lang")
        self.removeButton("switch-shape")
        self.removeButton("settings")
        if self.client.isWindows8Above:
            self.removeButton("windows-mode-icon")
            
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
        cfg = ChecjConfig
        
        # 紀錄最後一次按下的鍵和按下的時間，在 filterKeyUp() 中要用
        self.lastKeyDownCode = keyEvent.keyCode
        if self.lastKeyDownTime == 0.0:
            self.lastKeyDownTime = time.time()

        # 使用者開始輸入，還沒送出前的編輯區內容稱 composition string
        # isComposing() 是 False，表示目前編輯區是空的
        # 若正在編輯中文，則任何按鍵我們都需要送給輸入法處理，直接 return True
        # 另外，若使用 "`" key 輸入特殊符號，可能會有編輯區是空的
        # 但選字清單開啟，輸入法需要處理的情況
        if self.isComposing() or self.showCandidates:
            return True
        # --------------   以下都是「沒有」正在輸入中文的狀況   --------------

        # 如果按下 Alt，可能是應用程式熱鍵，輸入法不做處理
        if keyEvent.isKeyDown(VK_MENU):
            return False

        # 如果按下 Ctrl 鍵
        if keyEvent.isKeyDown(VK_CONTROL):
            return False

        # 若按下 Shift 鍵
        if keyEvent.isKeyDown(VK_SHIFT):
            # 若開啟 Shift 快速輸入符號，輸入法需要處理此按鍵
            if self.easySymbolsWithShift and keyEvent.isPrintableChar() and self.langMode == CHINESE_MODE:
                return True
            # 若開啟 Shift 輸入全形標點，輸入法需要處理此按鍵
            if self.fullShapeSymbols and keyEvent.isPrintableChar() and self.langMode == CHINESE_MODE:
                return True
            # 若萬用字元使用*，輸入法需要處理*按鍵
            if self.selWildcardChar == '*' and keyEvent.keyCode == 0x38 and self.langMode == CHINESE_MODE:
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

        # CheCJ
        # 中文模式下，當中文編輯區是空的，輸入法只需處理倉頡字根
        # 檢查按下的鍵是否為倉頡字根
        if self.cin.isInKeyName(chr(keyEvent.charCode).lower()):
            return True
            
        # 中文模式下，若按下 ` 鍵，讓輸入法進行處理
        if keyEvent.isKeyDown(VK_OEM_3):
            return True
        
        # 其餘狀況一律不處理，原按鍵輸入直接送還給應用程式
        return False

    def onKeyDown(self, keyEvent):
        cfg = ChecjConfig
        charCode = keyEvent.charCode
        keyCode = keyEvent.keyCode
        charStr = chr(charCode)
        
        # CheCJ
        candidates = []
        charStrLow = charStr.lower()
        self.isWildcardChardefs = False
        self.showMessage("", 0)
        
        # 功能選單 ----------------------------------------------------------------
        if self.langMode == CHINESE_MODE and len(self.compositionChar) == 0:
            menu_OutputSimpChinese = "輸出繁體" if self.outputSimpChinese else "輸出簡體"
            menu_fullShapeSymbols = "停用 Shift 輸入全形標點" if self.fullShapeSymbols else "啟用 Shift 輸入全形標點"
            menu_easySymbolsWithShift = "停用 Shift 快速輸入符號" if self.easySymbolsWithShift else "啟用 Shift 快速輸入符號"
            menu_supportSymbolCoding = "停用 Cin 碼表的符號編碼" if self.supportSymbolCoding else "啟用 Cin 碼表的符號編碼"
            menu_supportWildcard = "停用以萬用字元代替組字字根" if self.supportWildcard else "啟用以萬用字元代替組字字根"
            
            if not keyEvent.isKeyDown(VK_SHIFT) and keyEvent.isKeyDown(VK_OEM_3):
                self.menutype = 0
                menu = ["設定酷倉", menu_OutputSimpChinese, "功能開關", "特殊符號", "注音符號", "外語文字"]
                self.setCandidateCursor(0)
                self.setCandidatePage(0)
                self.setCandidateList(menu)
                self.candidates = self.candidateList
                self.showmenu = True
                self.closemenu = False
                
            if self.showmenu:
                self.closemenu = False
                candidates = self.candidates
                candCursor = self.candidateCursor  # 目前的游標位置
                candCount = len(self.candidateList)  # 目前選字清單項目數
                currentCandPageCount = math.ceil(len(candidates) / self.candPerPage) # 目前的選字清單總頁數
                currentCandPage = self.currentCandPage # 目前的選字清單頁數
                
                # 候選清單分頁
                pagecandidates = list(self.chunks(candidates, self.candPerPage))
                self.setCandidateList(pagecandidates[currentCandPage])
                self.setShowCandidates(True)
                
                # 使用數字鍵輸出候選字
                if keyCode >= ord('0') and keyCode <= ord('9') and not keyEvent.isKeyDown(VK_SHIFT):
                    i = keyCode - ord('1')
                    if self.menutype == 0 and i == 2: # 切至功能開關頁面
                        candCursor = 0
                        currentCandPage = 0
                        self.candidates = [menu_fullShapeSymbols, menu_easySymbolsWithShift, menu_supportSymbolCoding, menu_supportWildcard]
                        pagecandidates = list(self.chunks(self.candidates, self.candPerPage))
                        self.menutype = 1
                    elif self.menutype == 0 and i == 3: # 切至特殊符號頁面
                        candCursor = 0
                        currentCandPage = 0
                        self.candidates = self.symbols.getKeyNames()
                        pagecandidates = list(self.chunks(self.candidates, self.candPerPage))
                        self.menutype = 2
                    elif self.menutype == 0 and i == 4: # 切至注音符號頁面
                        candCursor = 0
                        currentCandPage = 0
                        bopomofolist = []
                        for i in range(0x3105,0x312A):
                            bopomofolist.append(chr(i))
                        self.candidates = bopomofolist
                        pagecandidates = list(self.chunks(self.candidates, self.candPerPage))
                        self.menutype = 4
                    elif self.menutype == 0 and i == 5: # 切至外語文字頁面
                        candCursor = 0
                        currentCandPage = 0
                        self.candidates = self.flangs.getKeyNames()
                        pagecandidates = list(self.chunks(self.candidates, self.candPerPage))
                        self.menutype = 5
                    elif self.menutype == 0: # 執行主頁面其它項目
                        self.onMenuCommand(i, 0)
                        candCursor = 0
                        currentCandPage = 0
                        self.showmenu = False
                        self.resetComposition()
                    elif self.menutype == 1: # 執行功能開關頁面項目
                        self.onMenuCommand(i, 1)
                        candCursor = 0
                        currentCandPage = 0
                        self.showmenu = False
                        self.menutype = 0
                        self.resetComposition()
                    elif self.menutype == 2: # 切至特殊符號子頁面
                        candCursor = 0
                        currentCandPage = 0
                        self.candidates = self.symbols.getCharDef(self.candidateList[i])
                        pagecandidates = list(self.chunks(self.candidates, self.candPerPage))
                        self.menutype = 3
                    elif self.menutype == 3: # 執行特殊符號子頁面項目
                        self.menutype = 0
                        candCursor = 0
                        currentCandPage = 0
                        self.showmenu = False
                        self.setCommitString(self.candidateList[i])
                        self.resetComposition()
                    elif self.menutype == 4: # 執行注音符號頁面項目
                        self.menutype = 0
                        candCursor = 0
                        currentCandPage = 0
                        self.showmenu = False
                        self.setCommitString(self.candidateList[i])
                        self.resetComposition()
                    elif self.menutype == 5: # 切至外語文字子頁面
                        candCursor = 0
                        currentCandPage = 0
                        self.candidates = self.flangs.getCharDef(self.candidateList[i])
                        pagecandidates = list(self.chunks(self.candidates, self.candPerPage))
                        self.menutype = 6
                    elif self.menutype == 6: # 執行外語文字子頁面項目
                        self.menutype = 0
                        candCursor = 0
                        currentCandPage = 0
                        self.showmenu = False
                        self.setCommitString(self.candidateList[i])
                        self.resetComposition()
                elif keyCode == VK_UP:  # 游標上移
                    if (candCursor - self.candPerRow) < 0:
                        if currentCandPage > 0:
                            currentCandPage -= 1
                            candCursor = 0
                    else:
                        if (candCursor - self.candPerRow) >= 0:
                            candCursor = candCursor - self.candPerRow
                elif keyCode == VK_DOWN:  # 游標下移
                    if (candCursor + self.candPerRow) >= self.candPerPage:
                        if (currentCandPage + 1) < currentCandPageCount:
                            currentCandPage += 1
                            candCursor = 0
                    else:
                        if (candCursor + self.candPerRow) < len(pagecandidates[currentCandPage]):
                            candCursor = candCursor + self.candPerRow
                elif keyCode == VK_LEFT:  # 游標左移
                    if candCursor > 0:
                        candCursor -= 1
                elif keyCode == VK_RIGHT:  # 游標右移
                    if (candCursor + 1) < candCount:
                        candCursor += 1
                elif keyCode == VK_HOME:  # Home 鍵
                    currentCandPage = 0
                    candCursor = 0
                elif keyCode == VK_END:  # End 鍵
                    currentCandPage = currentCandPageCount - 1
                    candCursor = 0
                elif keyCode == VK_PRIOR:  # Page UP 鍵
                    if currentCandPage > 0:
                        currentCandPage -= 1
                        candCursor = 0
                elif keyCode == VK_NEXT:  # Page Down 鍵
                    if (currentCandPage + 1) < currentCandPageCount:
                        currentCandPage += 1
                        candCursor = 0
                elif keyCode == VK_RETURN or keyCode == VK_SPACE:  # 按下 Enter 鍵或空白鍵
                    i = candCursor
                    if self.menutype == 0 and i == 2: # 切至功能開關頁面
                        candCursor = 0
                        currentCandPage = 0
                        self.candidates = [menu_fullShapeSymbols, menu_easySymbolsWithShift, menu_supportSymbolCoding, menu_supportWildcard]
                        pagecandidates = list(self.chunks(self.candidates, self.candPerPage))
                        self.menutype = 1
                    elif self.menutype == 0 and i == 3: # 切至特殊符號頁面
                        candCursor = 0
                        currentCandPage = 0
                        self.candidates = self.symbols.getKeyNames()
                        pagecandidates = list(self.chunks(self.candidates, self.candPerPage))
                        self.menutype = 2
                    elif self.menutype == 0 and i == 4: # 切至注音符號頁面
                        candCursor = 0
                        currentCandPage = 0
                        bopomofolist = []
                        for i in range(0x3105,0x312A):
                            bopomofolist.append(chr(i))
                        self.candidates = bopomofolist
                        pagecandidates = list(self.chunks(self.candidates, self.candPerPage))
                        self.menutype = 4
                    elif self.menutype == 0 and i == 5: # 切至外語文字頁面
                        candCursor = 0
                        currentCandPage = 0
                        self.candidates = self.flangs.getKeyNames()
                        pagecandidates = list(self.chunks(self.candidates, self.candPerPage))
                        self.menutype = 5
                    elif self.menutype == 0: # 執行主頁面其它項目
                        self.onMenuCommand(i, 0)
                        candCursor = 0
                        currentCandPage = 0
                        self.showmenu = False
                        self.resetComposition()
                    elif self.menutype == 1: # 執行功能開關頁面項目
                        self.onMenuCommand(i, 1)
                        candCursor = 0
                        currentCandPage = 0
                        self.showmenu = False
                        self.menutype = 0
                        self.resetComposition()
                    elif self.menutype == 2: # 切至特殊符號子頁面
                        candCursor = 0
                        currentCandPage = 0
                        self.candidates = self.symbols.getCharDef(self.candidateList[i])
                        pagecandidates = list(self.chunks(self.candidates, self.candPerPage))
                        self.menutype = 3
                    elif self.menutype == 3: # 執行特殊符號子頁面項目
                        self.menutype = 0
                        candCursor = 0
                        currentCandPage = 0
                        self.showmenu = False
                        self.setCommitString(self.candidateList[i])
                        self.resetComposition()
                    elif self.menutype == 4: # 執行注音符號頁面項目
                        self.menutype = 0
                        candCursor = 0
                        currentCandPage = 0
                        self.showmenu = False
                        self.setCommitString(self.candidateList[i])
                        self.resetComposition()
                    elif self.menutype == 5: # 切至外語文字子頁面
                        candCursor = 0
                        currentCandPage = 0
                        self.candidates = self.flangs.getCharDef(self.candidateList[i])
                        pagecandidates = list(self.chunks(self.candidates, self.candPerPage))
                        self.menutype = 6
                    elif self.menutype == 6: # 執行外語文字子頁面項目
                        self.menutype = 0
                        candCursor = 0
                        currentCandPage = 0
                        self.showmenu = False
                        self.setCommitString(self.candidateList[i])
                        self.resetComposition()
                elif keyCode == VK_ESCAPE:
                    candCursor = 0
                    currentCandPage = 0
                    self.showmenu = False
                    self.menutype = 0
                    self.resetComposition()
                # 更新選字視窗游標位置
                self.setCandidateCursor(candCursor)
                self.setCandidatePage(currentCandPage)
                self.setCandidateList(pagecandidates[currentCandPage])
        
        
        # 某些狀況須要特別處理或忽略
        # 如果字根空白且選單未開啟過，不處理 Enter 及 Backspace 鍵
        if not self.isComposing() and self.closemenu:
            if keyCode == VK_RETURN or keyCode == VK_BACK:
                return False

        # 若按下 Shift 鍵,且沒有按下其它的按鍵
        if keyEvent.isKeyDown(VK_SHIFT) and not keyEvent.isPrintableChar():
            return False
            
        # 按下的鍵為 CIN 內有定義的字根
        if self.cin.isInKeyName(charStrLow) and self.closemenu:
            # 若按下 Shift 鍵
            if keyEvent.isKeyDown(VK_SHIFT) and self.langMode == CHINESE_MODE:
                CommitStr = charStr
                # 使用 Shift 鍵做全形輸入 (easy symbol input)
                # 這裡的 easy symbol input，是定義在 swkb.dat 設定檔中的符號
                if self.easySymbolsWithShift and self.isLetterChar(keyCode):
                    if self.swkb.isInCharDef(charStr.upper()):
                        candidates = self.swkb.getCharDef(charStr.upper())
                        CommitStr = candidates[0]
                        candidates = []
                    else: # 不在快速符號表裡
                        if self.shapeMode == FULLSHAPE_MODE: # 全形模式
                            CommitStr = self.charCodeToFullshape(charCode)
                    self.setCommitString(CommitStr)
                    self.resetComposition()
                # 如果啟用 Shift 輸入全形標點
                elif self.fullShapeSymbols:
                    if charStr == '*' and self.selWildcardChar == charStr: # 如果按鍵及萬用字元為*
                        if not '*' in self.compositionChar:
                            self.compositionChar += '*'
                            keyname = '＊'
                            self.setCompositionString(self.compositionString + keyname)
                    # 如果是符號或數字，將字串轉為全形再輸出
                    elif self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode):
                        if self.fsymbols.isInCharDef(charStr):
                            self.compositionChar = charStr
                            fullShapeSymbolsList = self.fsymbols.getCharDef(self.compositionChar)
                            self.setCompositionString(fullShapeSymbolsList[0])
                            self.setCompositionCursor(len(self.compositionString))
                        else:
                            if self.cin.isInKeyName(charStrLow): # 如果是 CIN 所定義的字根
                                self.compositionChar = charStrLow
                                keyname = self.cin.getKeyName(charStrLow)
                                self.setCompositionString(keyname)
                                self.setCompositionCursor(len(self.compositionString))
                            else:
                                if self.shapeMode == FULLSHAPE_MODE: # 全形模式
                                    CommitStr = self.SymbolscharCodeToFullshape(charCode)
                                self.setCommitString(CommitStr)
                                self.resetComposition()
                    else: #如果是字母
                        if self.shapeMode == FULLSHAPE_MODE: # 全形模式
                            CommitStr = self.charCodeToFullshape(charCode)
                        self.setCommitString(CommitStr)
                        self.resetComposition()
                else: # 如果未使用 SHIFT 輸入快速符號或全形標點
                    if charStr == '*' and self.selWildcardChar == charStr: # 如果按鍵及萬用字元為*
                        if not '*' in self.compositionChar:
                            self.compositionChar += '*'
                            keyname = '＊'
                            self.setCompositionString(self.compositionString + keyname)
                    else:
                        if self.cin.isInKeyName(charStrLow) and (self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode)): # 如果是 CIN 所定義的字根
                            self.compositionChar = charStrLow
                            keyname = self.cin.getKeyName(charStrLow)
                            self.setCompositionString(keyname)
                            self.setCompositionCursor(len(self.compositionString))
                        else:
                            if self.shapeMode == FULLSHAPE_MODE: # 全形模式
                                # 如果是符號或數字，將字串轉為全形再輸出
                                if self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode):
                                    CommitStr = self.SymbolscharCodeToFullshape(charCode)
                                else:
                                    CommitStr = self.charCodeToFullshape(charCode)
                            self.setCommitString(CommitStr)
                            self.resetComposition()
            else: # 若沒按下 Shift 鍵
                # 如果是英文全形模式，將字串轉為全形再輸出
                if self.shapeMode == FULLSHAPE_MODE and self.langMode == ENGLISH_MODE:
                    # 如果是符號或數字，將字串轉為全形再輸出
                    if self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode):
                        CommitStr = self.SymbolscharCodeToFullshape(charCode)
                    else:
                        CommitStr = self.charCodeToFullshape(charCode)
                    self.setCommitString(CommitStr)
                    self.resetComposition()
                else: # 送出 CIN 所定義的字根
                    self.compositionChar += charStrLow
                    keyname = self.cin.getKeyName(charStrLow)
                    self.setCompositionString(self.compositionString + keyname)
                    self.setCompositionCursor(len(self.compositionString))
        # 按下的鍵不存在於 CIN 所定義的字根
        elif not self.cin.isInKeyName(charStrLow) and self.closemenu:
            # 若按下 Shift 鍵
            if keyEvent.isKeyDown(VK_SHIFT) and self.langMode == CHINESE_MODE:
                # 如果停用 Shift 輸入全形標點
                if not self.fullShapeSymbols:
                    # 如果是全形模式，將字串轉為全形再輸出
                    if self.shapeMode == FULLSHAPE_MODE:
                        if charStr == '*' and self.selWildcardChar == charStr: # 如果按鍵及萬用字元為*
                            if not '*' in self.compositionChar:
                                self.compositionChar += '*'
                                keyname = '＊'
                                self.setCompositionString(self.compositionString + keyname)
                        else:
                            # 如果是符號或數字，將字串轉為全形再輸出
                            if self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode):
                                CommitStr = self.SymbolscharCodeToFullshape(charCode)
                            else:
                                CommitStr = self.charCodeToFullshape(charCode)
                            self.setCommitString(CommitStr)
                            self.resetComposition()
                    else: # 半形模式直接輸出不作處理
                        if charStr == '*' and self.selWildcardChar == charStr: # 如果按鍵及萬用字元為*
                            if not '*' in self.compositionChar:
                                self.compositionChar += '*'
                                keyname = '＊'
                                self.setCompositionString(self.compositionString + keyname)
                        else:
                            CommitStr = charStr
                            self.setCommitString(CommitStr)
                            self.resetComposition()
                else: # 如果啟用 Shift 輸入全形標點
                    # 如果是符號或數字鍵，將字串轉為全形再輸出
                    if self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode):
                        # 如果該鍵有定義在 fsymbols
                        if self.fsymbols.isInCharDef(charStr):
                            if charStr == '*' and self.selWildcardChar == charStr: # 如果按鍵及萬用字元為*
                                if not '*' in self.compositionChar:
                                    self.compositionChar += '*'
                                    keyname = '＊'
                                    self.setCompositionString(self.compositionString + keyname)
                            else:
                                self.compositionChar = charStr
                                fullShapeSymbolsList = self.fsymbols.getCharDef(self.compositionChar)
                                self.setCompositionString(fullShapeSymbolsList[0])
                                self.setCompositionCursor(len(self.compositionString))
                        else: # 沒有定義在 fsymbols 裡
                            if charStr == '*' and self.selWildcardChar == charStr: # 如果按鍵及萬用字元為*
                                if not '*' in self.compositionChar:
                                    self.compositionChar += '*'
                                    keyname = '＊'
                                    self.setCompositionString(self.compositionString + keyname)
                            else:
                                if self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode):
                                    CommitStr = self.SymbolscharCodeToFullshape(charCode)
                                else:
                                    CommitStr = self.charCodeToFullshape(charCode)
                                self.setCommitString(CommitStr)
                                self.resetComposition()
                                
            else: # 若沒按下 Shift 鍵
                # 如果是全形模式，將字串轉為全形再輸出
                if self.shapeMode == FULLSHAPE_MODE and len(self.compositionChar) == 0:
                    if self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode):
                        CommitStr = self.SymbolscharCodeToFullshape(charCode)
                    else:
                        CommitStr = self.charCodeToFullshape(charCode)
                    self.setCommitString(CommitStr)
                    self.resetComposition()

        if self.langMode == CHINESE_MODE and len(self.compositionChar) >= 1:
            self.showmenu = False
            
            if keyCode == VK_ESCAPE and (self.showCandidates or len(self.compositionChar) > 0):
                self.resetComposition()
                
            # 刪掉一個字根
            if keyCode == VK_BACK:
                if self.compositionString != "":
                    self.setCompositionString(self.compositionString[:-1])
                    self.compositionChar = self.compositionChar[:-1]
                    self.setCandidateCursor(0)
                    self.setCandidatePage(0)
                    self.wildcardcandidates = []
                    self.wildcardpagecandidates = []

            # 組字字根超過5個
            if len(self.compositionChar) > MAX_CHAR_LENGTH:
                self.setCompositionString(self.compositionString[:-1])
                self.compositionChar = self.compositionChar[:-1]

            if self.cin.isInCharDef(self.compositionChar) and self.closemenu:
                candidates = self.cin.getCharDef(self.compositionChar)
            elif self.fullShapeSymbols and self.fsymbols.isInCharDef(self.compositionChar) and self.closemenu:
                candidates = self.fsymbols.getCharDef(self.compositionChar)
            elif self.supportWildcard and self.selWildcardChar in self.compositionChar and self.closemenu:
                if self.wildcardcandidates and self.wildcardcompositionChar == self.compositionChar:
                    candidates = self.wildcardcandidates
                else:
                    self.setCandidateCursor(0)
                    self.setCandidatePage(0)
                    self.wildcardcandidates = self.cin.getWildcardCharDefs(self.compositionChar, self.selWildcardChar, self.candMaxItems)
                    self.wildcardpagecandidates = []
                    self.wildcardcompositionChar = self.compositionChar
                    candidates = self.wildcardcandidates
                self.isWildcardChardefs = True
            
            # 候選清單處理
            if candidates:
                candCursor = self.candidateCursor  # 目前的游標位置
                candCount = len(self.candidateList)  # 目前選字清單項目數
                currentCandPageCount = math.ceil(len(candidates) / self.candPerPage) # 目前的選字清單總頁數
                currentCandPage = self.currentCandPage # 目前的選字清單頁數
                
                # 候選清單分頁
                if self.isWildcardChardefs:
                    if self.wildcardpagecandidates:
                        pagecandidates = self.wildcardpagecandidates
                    else:
                        self.wildcardpagecandidates = list(self.chunks(candidates, self.candPerPage))
                        pagecandidates = self.wildcardpagecandidates
                else:
                    pagecandidates = list(self.chunks(candidates, self.candPerPage))
                self.setCandidateList(pagecandidates[currentCandPage])
                self.setShowCandidates(True)
                
                # 如果字根首字是符號就直接輸出
                if (self.isSymbolsChar(keyCode) or self.isNumberChar(keyCode)) and len(self.compositionChar) == 1 and charStrLow == self.compositionChar:
                    directout = True
                    if self.cin.isInCharDef(self.compositionChar) and self.supportSymbolCoding and len(self.cin.haveNextCharDef(self.compositionChar)) > 1:
                        directout = False
                    
                    if len(candidates) == 1 and directout and self.selWildcardChar != self.compositionChar:
                        cand = candidates[0]
                        self.setCommitString(cand)
                        self.resetComposition()
                        candCursor = 0
                        currentCandPage = 0
                
                # 使用數字鍵輸出候選字
                if keyCode >= ord('0') and keyCode <= ord('9') and not keyEvent.isKeyDown(VK_SHIFT):
                    i = keyCode - ord('1')
                    if i < len(candidates):
                        commitStr = self.candidateList[i]
                    
                        # 如果使用萬用字元解碼
                        if self.isWildcardChardefs:
                            messagestr = self.cin.getCharEncode(commitStr)
                            self.showMessage(messagestr, 5)
                            self.wildcardcandidates = []
                            self.wildcardpagecandidates = []
                            self.isWildcardChardefs = False
                    
                        # 如果使用打繁出簡，就轉成簡體中文
                        if self.outputSimpChinese:
                            commitStr = self.opencc.convert(commitStr)
                        
                        self.setCommitString(commitStr)
                        self.resetComposition()
                        candCursor = 0
                        currentCandPage = 0
                elif keyCode == VK_UP:  # 游標上移
                    if (candCursor - self.candPerRow) < 0:
                        if currentCandPage > 0:
                            currentCandPage -= 1
                            candCursor = 0
                    else:
                        if (candCursor - self.candPerRow) >= 0:
                            candCursor = candCursor - self.candPerRow
                elif keyCode == VK_DOWN:  # 游標下移
                    if (candCursor + self.candPerRow) >= self.candPerPage:
                        if (currentCandPage + 1) < currentCandPageCount:
                            currentCandPage += 1
                            candCursor = 0
                    else:
                        if (candCursor + self.candPerRow) < len(pagecandidates[currentCandPage]):
                            candCursor = candCursor + self.candPerRow
                elif keyCode == VK_LEFT:  # 游標左移
                    if candCursor > 0:
                        candCursor -= 1
                elif keyCode == VK_RIGHT:  # 游標右移
                    if (candCursor + 1) < candCount:
                        candCursor += 1
                elif keyCode == VK_HOME:  # Home 鍵
                    currentCandPage = 0
                    candCursor = 0
                elif keyCode == VK_END:  # End 鍵
                    currentCandPage = currentCandPageCount - 1
                    candCursor = 0
                elif keyCode == VK_PRIOR:  # Page UP 鍵
                    if currentCandPage > 0:
                        currentCandPage -= 1
                        candCursor = 0
                elif keyCode == VK_NEXT:  # Page Down 鍵
                    if (currentCandPage + 1) < currentCandPageCount:
                        currentCandPage += 1
                        candCursor = 0
                elif keyCode == VK_RETURN or keyCode == VK_SPACE:  # 按下 Enter 鍵或空白鍵
                    # 找出目前游標位置的選字鍵 (1234..., asdf...等等)
                    commitStr = self.candidateList[candCursor]
                    
                    # 如果使用萬用字元解碼
                    if self.isWildcardChardefs:
                        messagestr = self.cin.getCharEncode(commitStr)
                        self.showMessage(messagestr, 5)
                        self.wildcardcandidates = []
                        self.wildcardpagecandidates = []
                        self.isWildcardChardefs = False
                    
                    # 如果使用打繁出簡，就轉成簡體中文
                    if self.outputSimpChinese:
                        commitStr = self.opencc.convert(commitStr)
                    
                    self.setCommitString(commitStr)
                    self.resetComposition()
                    candCursor = 0
                    currentCandPage = 0
                else: # 按下其它鍵，先將候選字游標位址及目前頁數歸零
                    candCursor = 0
                    currentCandPage = 0
                # 更新選字視窗游標位置及頁數
                self.setCandidateCursor(candCursor)
                self.setCandidatePage(currentCandPage)
                self.setCandidateList(pagecandidates[currentCandPage])
            else: # 沒有候選字
                # 按下空白鍵或 Enter 鍵
                if keyCode == VK_SPACE or keyCode == VK_RETURN:
                    if len(candidates) == 0:
                        self.showMessage("查無字根...", 3)
                self.setShowCandidates(False)

        if not self.closemenu:
            self.closemenu = True
        return True

    # 使用者放開按鍵，在 app 收到前先過濾那些鍵是輸入法需要的。
    # return True，系統會呼叫 onKeyUp() 進一步處理這個按鍵
    # return False，表示我們不需要這個鍵，系統會原封不動把按鍵傳給應用程式
    def filterKeyUp(self, keyEvent):
        # 如果按下 Alt，可能是應用程式熱鍵，輸入法不做處理
        if keyEvent.isKeyDown(VK_MENU):
            return False

        # 如果按下 Ctrl 鍵
        if keyEvent.isKeyDown(VK_CONTROL):
            return False
    
        # 若啟用使用 Shift 鍵切換中英文模式
        if ChecjConfig.switchLangWithShift:
            # 剛才最後一個按下的鍵，和現在放開的鍵，都是 Shift
            if self.lastKeyDownCode == VK_SHIFT and keyEvent.keyCode == VK_SHIFT:
                pressedDuration = time.time() - self.lastKeyDownTime
                # 按下和放開的時間相隔 < 0.5 秒
                if pressedDuration < 0.5:
                    self.isLangModeChanged = True
                    return True
        
        # 若切換全形/半形模式
        if self.isShapeModeChanged:
            return True
            
        self.lastKeyDownCode = 0
        self.lastKeyDownTime = 0.0
        return False

    def onKeyUp(self, keyEvent):
        cfg = ChecjConfig # 所有 CheCJTextService 共享一份設定物件
        charCode = keyEvent.charCode
        keyCode = keyEvent.keyCode
        
        self.lastKeyDownCode = 0
        self.lastKeyDownTime = 0.0
        
        # 若按下 Shift 鍵,且觸發中英文切換
        if self.isLangModeChanged and keyCode == VK_SHIFT:
            self.toggleLanguageMode()  # 切換中英文模式
            self.isLangModeChanged = False
            self.showmenu = False
            self.resetComposition()
            message = '中文模式' if self.langMode == CHINESE_MODE else '英數模式'
            self.showMessage(message, 3)
            
        if self.isShapeModeChanged:
            self.isShapeModeChanged = False
            message = '半形模式' if self.shapeMode == HALFSHAPE_MODE else '全形模式'
            self.showMessage(message, 3)
    
    def onPreservedKey(self, guid):
        self.lastKeyDownCode = 0;
        # some preserved keys registered are pressed
        if guid == SHIFT_SPACE_GUID: # 使用者按下 shift + space
            self.isShapeModeChanged = True
            self.toggleShapeMode()  # 切換全半形
            return True
        return False

    def onCommand(self, commandId, commandType):
        print("onCommand", commandId, commandType)
        # FIXME: We should distinguish left and right click using commandType

        if commandId == ID_SWITCH_LANG:  # 切換中英文模式
            self.toggleLanguageMode()
        elif commandId == ID_SWITCH_SHAPE:  # 切換全形/半形
            self.toggleShapeMode()
        elif commandId == ID_SETTINGS:  # 開啟設定工具
            config_tool = os.path.join(self.curdir, "config", "config.hta")
            os.startfile(config_tool)
        elif commandId == ID_MODE_ICON: # windows 8 mode icon
            self.toggleLanguageMode()  # 切換中英文模式
        elif commandId == ID_ABOUT: # 關於新酷音輸入法
            pass
        elif commandId == ID_WEBSITE: # visit chewing website
            os.startfile("https://github.com/EasyIME/PIME")
        elif commandId == ID_GROUP: # visit chewing google groups website
            os.startfile("http://groups.google.com/group/chewing-devel")
        elif commandId == ID_BUGREPORT: # visit bug tracker page
            os.startfile("https://github.com/EasyIME/PIME/issues")
        elif commandId == ID_DICT_BUGREPORT:
            os.startfile("https://github.com/KenLuoTW/PIME/issues")
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
                {"text": "參觀 PIME 官方網站(&W)", "id": ID_WEBSITE},
                # {"text": "新酷音線上討論區(&G)", "id": ID_GROUP},
                {},
                {"text": "軟體本身的建議及錯誤回報(&B)", "id": ID_BUGREPORT},
                {"text": "酷倉輸入法模組錯誤回報 (&P)", "id": ID_DICT_BUGREPORT},
                {},
                # {"text": "新酷音使用說明 (&H)", "id": ID_CHEWING_HELP},
                # {"text": "編輯使用者詞庫 (&E)", "id": ID_HASHED},
                {"text": "設定酷倉輸入法(&C)", "id": ID_SETTINGS},
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

    # 按下「`」鍵的選單命令
    def onMenuCommand(self, commandId, commandType):
        cfg = ChecjConfig
        if commandType == 0:
            if commandId == 0:
                config_tool = os.path.join(self.curdir, "config", "config.hta")
                os.startfile(config_tool)
            elif commandId == 1:
                self.setOutputSimplifiedChinese(not self.outputSimpChinese)
        elif commandType == 1: # 功能開關
            if commandId == 0:
                self.fullShapeSymbols = not self.fullShapeSymbols
            elif commandId == 1:
                self.easySymbolsWithShift = not self.easySymbolsWithShift
            elif commandId == 2:
                self.supportSymbolCoding = not self.supportSymbolCoding
            elif commandId == 3:
                self.supportWildcard = not self.supportWildcard
        
    # 依照目前輸入法狀態，更新語言列顯示
    def updateLangButtons(self):
        # 如果中英文模式發生改變
        icon_name = "chi.ico" if self.langMode == CHINESE_MODE else "eng.ico"
        icon_path = os.path.join(self.icon_dir, icon_name)
        self.changeButton("switch-lang", icon=icon_path)

        if self.client.isWindows8Above:  # windows 8 mode icon
            # FIXME: we need a better set of icons to meet the
            #        WIndows 8 IME guideline and UX guidelines.
            self.changeButton("windows-mode-icon", icon=icon_path)
        
        # 如果全形半形模式改變
        icon_name = "full.ico" if self.shapeMode == FULLSHAPE_MODE else "half.ico"
        icon_path = os.path.join(self.icon_dir, icon_name)
        self.changeButton("switch-shape", icon=icon_path)

    # 切換中英文模式
    def toggleLanguageMode(self):
        if self.langMode == CHINESE_MODE:
            self.langMode = ENGLISH_MODE
        elif self.langMode == ENGLISH_MODE:
            self.langMode = CHINESE_MODE
        self.updateLangButtons()

    # 切換全形/半形
    def toggleShapeMode(self):
        if self.shapeMode == HALFSHAPE_MODE:
            self.shapeMode = FULLSHAPE_MODE
        elif self.shapeMode == FULLSHAPE_MODE:
            self.shapeMode = HALFSHAPE_MODE
        self.updateLangButtons()

    # 鍵盤開啟/關閉時會被呼叫 (在 Windows 10 Ctrl+Space 時)
    def onKeyboardStatusChanged(self, opened):
        TextService.onKeyboardStatusChanged(self, opened)
        if opened: # 鍵盤開啟
            self.resetComposition()
        else: # 鍵盤關閉，輸入法停用
            self.resetComposition()

        # Windows 8 systray IME mode icon
        if self.client.isWindows8Above:
            # 若鍵盤關閉，我們需要把 widnows 8 mode icon 設定為 disabled
            self.changeButton("windows-mode-icon", enable=opened)
            self.changeButton("switch-lang", enable=opened)
        # FIXME: 是否需要同時 disable 其他語言列按鈕？
        
    # 當中文編輯結束時會被呼叫。若中文編輯不是正常結束，而是因為使用者
    # 切換到其他應用程式或其他原因，導致我們的輸入法被強制關閉，此時
    # forced 參數會是 True，在這種狀況下，要清除一些 buffer
    def onCompositionTerminated(self, forced):
        TextService.onCompositionTerminated(self, forced)
        if forced:
            self.resetComposition()
            
    # 重置輸入的字根
    def resetComposition(self):
        self.compositionChar = ''
        self.setCompositionString('')
        self.setShowCandidates(False)
        self.setCandidateCursor(0)
        self.setCandidatePage(0)
        self.wildcardcandidates = []
        self.wildcardpagecandidates = []
    
    # 設定候選字頁數
    def setCandidatePage(self, page):
        self.currentCandPage = page
    
    # 判斷數字鍵?
    def isNumberChar(self, keyCode):
        return keyCode >= 0x30 and keyCode <= 0x39

    # 判斷符號鍵?
    def isSymbolsChar(self, keyCode):
        return keyCode >= 0xBA and keyCode <= 0xDF
        
    # 判斷字母鍵?
    def isLetterChar(self, keyCode):
        return keyCode >= 0x41 and keyCode <= 0x5A

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
        
    # List 分段
    def chunks(self, l, n):
        for i in range(0, len(l), n):
            yield l[i:i+n]