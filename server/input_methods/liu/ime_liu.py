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
from __future__ import print_function
from __future__ import unicode_literals
from keycodes import * # for VK_XXX constants
from textService import *
import io
import os.path
from .cin import Cin

class LiuTextService(TextService):
    def __init__(self, client):
        TextService.__init__(self, client)

        self.icon_dir = base_dir = os.path.abspath(os.path.dirname(__file__))

        liu_path = os.path.join(base_dir, "liu.cin")
        with io.open(liu_path, encoding='utf-8') as fs:
            self.cin = Cin(fs)

        print("finish loading")

    def onActivate(self):
        TextService.onActivate(self)
        # Windows 8 systray IME mode icon
        self.addButton("windows-mode-icon",
            icon = os.path.join(self.icon_dir, "chi.ico"),
            tooltip = "Test Button!",
            commandId = 1
        )
        self.customizeUI(candFontSize = 20, candPerRow = 1)

        if self.cin.getSelection():
            self.setSelKeys(self.cin.getSelection())
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

        # handle normal keyboard input
        if not self.isComposing():
            if keyEvent.keyCode == VK_RETURN or keyEvent.keyCode == VK_BACK:
                return False

        if keyEvent.keyCode == VK_SPACE or len(self.compositionString) > 10:

            candidates = self.cin.getCharDef(self.compositionString)

            self.setCommitString(candidates[0])
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

            charCode = keyEvent.charCode
            keyCode = keyEvent.keyCode
            charStr = chr(charCode)

            self.setCompositionString(self.compositionString + charStr)

            candidates = self.cin.getCharDef(self.compositionString)

            if candidates:
                print("candidates are {}".format(",".join(candidates)))
                self.setCandidateList(candidates)
                self.setShowCandidates(True)
            else:
                print("no candidates")

            self.setCompositionCursor(len(self.compositionString))

        return True

    def onCommand(self, commandId, commandType):
        print("onCommand", commandId, commandType)


