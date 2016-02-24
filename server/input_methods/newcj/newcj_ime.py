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

from keycodes import * # for VK_XXX constants
from textService import *
from .libnewcj import NewCJContext
import os.path

CHINESE_MODE = 1
ENGLISH_MODE = 0
FULLSHAPE_MODE = 1
HALFSHAPE_MODE = 0

ID_SWITCH_LANG = 1
ID_SWITCH_SHAPE = 2
ID_SETTINGS = 3
ID_MODE_ICON = 4

class NewCJTextService(TextService):
    # compositionChar: a, b, c, d...
    # compositionString: 日, 月, 金, 木, 水, 火, 土...
    compositionChar = ''
    def __init__(self, client):
        TextService.__init__(self, client)
        self.curdir = os.path.abspath(os.path.dirname(__file__))
        self.icon_dir = self.curdir

        self.langMode = -1
        self.shapeMode = -1
        self.newCJContext = None

    # 輸入法被使用者啟用
    def onActivate(self):
        TextService.onActivate(self)
        self.initNewCJContext()

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
        # FIXME: popup menu is not yet implemented
        self.addButton("settings",
            icon = os.path.join(self.icon_dir, "config.ico"),
            tooltip = "設定",
            commandId = ID_SETTINGS
        )

        self.customizeUI(candFontSize = 20, candPerRow = 1)
        self.setSelKeys("1234567890")

    def onDeactivate(self):
        TextService.onDeactivate(self)
        self.newCJContext = None
        self.removeButton("switch-lang")
        self.removeButton("switch-shape")
        self.removeButton("settings")
        if self.client.isWindows8Above:
            self.removeButton("windows-mode-icon")

    def filterKeyDown(self, keyEvent):
		# 使用者開始輸入，還沒送出前的編輯區內容稱 composition string
        # isComposing() 是 False，表示目前編輯區是空的
        # 若正在編輯中文，則任何按鍵我們都需要送給輸入法處理，直接 return True
        # 另外，若使用 "`" key 輸入特殊符號，可能會有編輯區是空的
        # 但選字清單開啟，輸入法需要處理的情況
		# TODO: 是否讓Ctrl+A, Ctrl+C, Ctrl+V 在這時可以用？
        if self.isComposing() or self.showCandidates:
            return True
        # --------------   以下都是「沒有」正在輸入中文的狀況   --------------

        # 如果按下 Alt, Ctrl, Shift 鍵
        if keyEvent.isKeyDown(VK_MENU) or keyEvent.isKeyDown(VK_CONTROL) or keyEvent.isKeyDown(VK_SHIFT):
            return False

        # 不論中英文模式，NumPad 都允許直接輸入數字，輸入法不處理
        if keyEvent.isKeyToggled(VK_NUMLOCK): # NumLock is on
            # if this key is Num pad 0-9, +, -, *, /, pass it back to the system
            if keyEvent.keyCode >= VK_NUMPAD0 and keyEvent.keyCode <= VK_DIVIDE:
                return False # bypass IME

        # 不管中英文模式，只要是全形，輸入法都需要進一步處理(英數字從半形轉為全形)
        if self.shapeMode == FULLSHAPE_MODE:
            return True
        # --------------   以下皆為半形模式   --------------

        # 如果是英文半形模式，輸入法不做任何處理
        if self.langMode == ENGLISH_MODE:
            return False
        # --------------   以下皆為中文模式   --------------

        # 中文模式下開啟 Capslock，須切換成英文
        if keyEvent.isKeyToggled(VK_CAPITAL):
            # 如果此按鍵是英文字母，中文模式下要從大寫轉小寫，需要輸入法處理
            if keyEvent.isChar() and chr(keyEvent.charCode).isalpha():
                return True
            # 是其他符號或數字，則視同英文模式，不用處理
            else:
                return False

        # 檢查按下的鍵是否為自由大新定義的符號
        if self.isNewCJChardef(keyEvent.charCode):
            print('isNewCJChardef')
            return True

        # 其餘狀況一律不處理，原按鍵輸入直接送還給應用程式
        return False

    def onKeyDown(self, keyEvent):
        newCJContext = self.newCJContext
        charCode = keyEvent.charCode
        keyCode = keyEvent.keyCode
        charStr = chr(charCode)

        candidates = []
        if self.compositionChar in self.newCJContext.chardef:
            candidates = self.newCJContext.chardef[self.compositionChar]
        else:
            self.resetComposition()
        print('candidates: ', end='')
        print(candidates, sep=' ')
        print('compositionString: ' + self.compositionString)
        print('compositionChar: ' + self.compositionChar)
        # handle candidate list
        if self.showCandidates:
            candLengthStr = str(len(candidates))
            if len(candidates) > 9:
                print('length of candidates > 9 !!!')
            if keyCode == VK_UP or keyCode == VK_ESCAPE:
                self.setShowCandidates(False)
            elif keyCode >= ord('1') and keyCode <= ord('9'):
                i = keyCode - ord('1')
                cand = candidates[i]
                i = self.compositionCursor - 1
                if i < 0:
                    i = 0
                self.commitString = self.compositionString[0:i] + cand + self.compositionString[i + 1:]
                self.setCompositionString(self.commitString)
                self.setShowCandidates(False)
            return True
        else:
            if keyCode == VK_DOWN:
                self.setCandidateList(candidates)
                self.setShowCandidates(True)
                return True
        # handle normal keyboard input
        if not self.isComposing():
            if keyCode == VK_RETURN or keyCode == VK_BACK:
                return False
        if keyCode == VK_SPACE or keyCode == VK_RETURN or len(self.compositionString) > 5:
            if self.commitString == '' and len(self.newCJContext.chardef[self.compositionChar]) >= 1:
                self.commitString = self.newCJContext.chardef[self.compositionChar][0]
            self.setCommitString(self.commitString)
            print('commitString: ' + self.commitString)
            self.resetComposition()
        elif keyCode == VK_BACK and self.compositionString != "":
            self.setCompositionString(self.compositionString[:-1])
        elif keyCode == VK_LEFT:
            i = self.compositionCursor - 1
            if i >= 0:
                self.setCompositionCursor(i)
        elif keyCode == VK_RIGHT:
            i = self.compositionCursor + 1
            if i <= len(self.compositionString):
                self.setCompositionCursor(i)
        else:
            char = charStr.lower()
            self.compositionChar += char
            if char in self.newCJContext.keyname:
                keyname = self.newCJContext.keyname[char]
                self.setCompositionString(self.compositionString + keyname)
                self.setCompositionCursor(len(self.compositionString))
                return True
            return False

    def onCommand(self, commandId, commandType):
        print("onCommand", commandId, commandType)

    def isNumberChar(self, keyCode):
        return keyCode >= 0x30 and keyCode <= 0x39

    def resetComposition(self):
        self.compositionChar = ''
        self.setCompositionString('')

    def initNewCJContext(self):
        self.newCJContext = NewCJContext()
        self.newCJContext.loadTokens()
        print('load tokens')

    def isNewCJChardef(self, charCode):
        if charCode < 33:
            return False
        h = hex(charCode).split('x')[1]
        charStr = bytearray.fromhex(str(h)).decode()
        return charStr in self.newCJContext.chardef
