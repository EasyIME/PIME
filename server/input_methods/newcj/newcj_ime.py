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
import os.path
from .libnewcj import NewCJContext

class NewCJTextService(TextService):
    # compositionChar 是a, b, c, d...
    # compositionString是日, 月, 金, 木, 水, 火, 土...
    compositionChar = ""
    def __init__(self, client):
        TextService.__init__(self, client)
        self.icon_dir = os.path.abspath(os.path.dirname(__file__))
        self.newCJContext = None

    def onActivate(self):
        TextService.onActivate(self)
        self.initNewCJContext()
        # Windows 8 systray IME mode icon
        self.addButton("windows-mode-icon",
            icon = os.path.join(self.icon_dir, "chi.ico"),
            tooltip = "Test Button!",
            commandId = 1
        )
        self.customizeUI(candFontSize = 20, candPerRow = 1)
        self.setSelKeys("1234567890")
        # self.setSelKeys("asdfjkl;")

    def onDeactivate(self):
        TextService.onDeactivate(self)
        self.removeButton("test-btn")

    def filterKeyDown(self, keyEvent):
		# 看不見的符號通通不處理
        if not keyEvent.isPrintableChar():
            return False
		# 選字單出現時，需要處理0~9按鍵
        if self.isComposing() and self.isNumberChar(keyEvent.keyCode):
            return True
        return True

    def onKeyDown(self, keyEvent):
        candidates = self.newCJContext.chardef[self.compositionChar]
        commitString = ''
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
            if self.commitString == '':
                self.commitString = self.newCJContext.chardef[self.compositionChar][0]
            self.setCommitString(self.commitString)
            self.setCompositionString("")
            self.compositionChar = ""
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
            keyname = self.newCJContext.keyname[char]
            self.setCompositionString(self.compositionString + keyname)
            self.setCompositionCursor(len(self.compositionString))
        return True

    def onCommand(self, commandId, commandType):
        print("onCommand", commandId, commandType)

    def isNumberChar(self, keyCode):
        return self.charCode >= 0x30 and self.charCode <= 0x39

    def initNewCJContext(self):
        self.newCJContext = NewCJContext()
        self.newCJContext.loadTokens()
