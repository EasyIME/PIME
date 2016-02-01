#! python3
from ..keycodes import * # for VK_XXX constants
from ..textService import *
import os.path

class MeowTextService(TextService):
    def __init__(self, client):
        TextService.__init__(self, client)
        self.icon_dir = os.path.abspath(os.path.dirname(__file__))

    def onActivate(self):
        TextService.onActivate(self)
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
        if not self.isComposing():
            if keyEvent.keyCode == VK_RETURN or keyEvent.keyCode == VK_BACK:
                return False
        return True

    def onKeyDown(self, keyEvent):
        candidates = ["喵", "描", "秒", "妙"]
        # handle candidate list
        if self.showCandidates:
            if keyEvent.keyCode == VK_UP or keyEvent.keyCode == VK_ESCAPE:
                self.setShowCandidates(False)
            elif keyEvent.keyCode >= ord('1') and keyEvent.keyCode <= ord('4'):
                i = keyEvent.keyCode - ord('1')
                cand = candidates[i]
                i = self.compositionCursor - 1
                if i < 0:
                    i = 0
                s = self.compositionString[0:i] + cand + self.compositionString[i + 1:]
                self.setCompositionString(s)
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
        if keyEvent.keyCode == VK_RETURN or len(self.compositionString) > 10:
            self.setCommitString(self.compositionString)
            self.setCompositionString("")
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
            self.setCompositionString(self.compositionString + "喵")
            self.setCompositionCursor(len(self.compositionString))
        return True

    def onCommand(self, commandId, commandType):
        print("onCommand", commandId, commandType)
