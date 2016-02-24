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
        if not keyEvent.isPrintableChar() and keyEvent.keyCode != VK_DOWN or keyEvent.keyCode == VK_RWIN:
            return False
		# 要處理0~9按鍵
        if self.isNumberChar(keyEvent.keyCode):
            return self.showCandidates or self.isComposing()
        return True

    def onKeyDown(self, keyEvent):
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
            if keyEvent.keyCode == VK_UP or keyEvent.keyCode == VK_ESCAPE:
                self.setShowCandidates(False)
            elif keyEvent.keyCode >= ord('1') and keyEvent.keyCode <= ord('9'):
                i = keyEvent.keyCode - ord('1')
                cand = candidates[i]
                i = self.compositionCursor - 1
                if i < 0:
                    i = 0
                self.commitString = self.compositionString[0:i] + cand + self.compositionString[i + 1:]
                self.setCompositionString(self.commitString)
                self.setShowCandidates(False)
            return True
        else:
            if keyEvent.keyCode == VK_DOWN:
                self.setCandidateList(candidates)
                self.setShowCandidates(True)
                return True
        # handle normal keyboard input
        if not self.isComposing():
            if keyEvent.keyCode == VK_RETURN or keyEvent.keyCode == VK_BACK:
                return False
        if keyEvent.keyCode == VK_SPACE or keyEvent.keyCode == VK_RETURN or len(self.compositionString) > 5:
            if self.commitString == '' and len(self.newCJContext.chardef[self.compositionChar]) >= 1:
                self.commitString = self.newCJContext.chardef[self.compositionChar][0]
            self.setCommitString(self.commitString)
            print('commitString: ' + self.commitString)
            self.resetComposition()
        elif keyEvent.keyCode == VK_BACK and self.compositionString != "":
            self.setCompositionString(self.compositionString[:-1])
        elif keyEvent.keyCode == VK_LEFT:
            i = self.compositionCursor - 1
            if i >= 0:
                self.setCompositionCursor(i)
        elif keyEvent.keyCode == VK_RIGHT:
            i = self.compositionCursor + 1
            if i <= len(self.compositionString):
                self.setCompositionCursor(i)
        else:
            char = chr(keyEvent.charCode).lower()
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
