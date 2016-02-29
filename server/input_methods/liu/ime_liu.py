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
from cin import Cin
import os.path

class LiuTextService(TextService):
    def __init__(self, client):
        TextService.__init__(self, client)

	base_dir = os.path.abspath(os.path.dirname(__file__))

        self.icon_dir = base_path

        input_table_path = os.path.join(base_dir, 'liu.cin')
        with open(input_table_path) as f:
            self.cin = Cin(f)
	

    def onActivate(self):
        TextService.onActivate(self)
        # Windows 8 systray IME mode icon
        self.addButton("windows-mode-icon",
            icon = os.path.join(self.icon_dir, "chi.ico"),
            tooltip = "Liu !",
            commandId = 1
        )
        self.customizeUI(candFontSize = 20, candPerRow = 1)
        
        if self.cin.getSelection():
            self.setSelKeys(self.cin.getSelection())

    def onDeactivate(self):
        TextService.onDeactivate(self)
        self.removeButton("test-btn")

    # return True，系統會呼叫 onKeyDown() 進一步處理這個按鍵
    # return False，表示我們不需要這個鍵，系統會原封不動把按鍵傳給應用程式
    def filterKeyDown(self, keyEvent):

        if not self.isComposing():
            if keyEvent.keyCode == VK_RETURN or keyEvent.keyCode == VK_BACK:
                return False

        # 如果按下 Alt，可能是應用程式熱鍵，輸入法不做處理
        if keyEvent.isKeyDown(VK_MENU):
            return False

        # 如果按下 Ctrl 鍵
        if keyEvent.isKeyDown(VK_CONTROL):
            else: # 否則可能是應用程式熱鍵，輸入法不做處理
                return False

        return True

    def onKeyDown(self, keyEvent):

        # handle normal keyboard input
        if not self.isComposing():
            if keyEvent.keyCode == VK_RETURN or keyEvent.keyCode == VK_BACK:
                return False

        if keyEvent.keyCode == VK_RETURN or keyEvent.keyCode == VK_SPACE or len(self.compositionString) > 10:
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

            char_code = keyEvent.charCode
            new_character = chr(char_code)

            self.setCompositionString(self.compositionString + new_character)
            self.setCompositionCursor(len(self.compositionString))

        return True

    def onCommand(self, commandId, commandType):
        print("onCommand", commandId, commandType)
