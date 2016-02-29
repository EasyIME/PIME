#! python3
# copyright (c) 2015 - 2016 hong jen yee (pcman) <pcman.tw@gmail.com>
#
# this library is free software; you can redistribute it and/or
# modify it under the terms of the gnu lesser general public
# license as published by the free software foundation; either
# version 2.1 of the license, or (at your option) any later version.
#
# this library is distributed in the hope that it will be useful,
# but without any warranty; without even the implied warranty of
# merchantability or fitness for a particular purpose.  see the gnu
# lesser general public license for more details.
#
# you should have received a copy of the gnu lesser general public
# license along with this library; if not, write to the free software
# foundation, inc., 51 franklin street, fifth floor, boston, ma  02110-1301  usa

from keycodes import * # for vk_xxx constants
from textservice import *
from cin import cin
import os.path

class liutextservice(textservice):
    def __init__(self, client):
        textservice.__init__(self, client)

        base_dir = os.path.abspath(os.path.dirname(__file__))

        self.icon_dir = base_path

        input_table_path = os.path.join(base_dir, 'liu.cin')
        with open(input_table_path) as f:
            self.cin = cin(f)


    def onactivate(self):
        textservice.onactivate(self)
        # windows 8 systray ime mode icon
        self.addbutton("windows-mode-icon",
            icon = os.path.join(self.icon_dir, "chi.ico"),
            tooltip = "liu !",
            commandid = 1
        )
        self.customizeui(candfontsize = 20, candperrow = 1)

        if self.cin.getselection():
            self.setselkeys(self.cin.getselection())

    def ondeactivate(self):
        textservice.ondeactivate(self)
        self.removebutton("test-btn")

    # return true，系統會呼叫 onkeydown() 進一步處理這個按鍵
    # return false，表示我們不需要這個鍵，系統會原封不動把按鍵傳給應用程式
    def filterkeydown(self, keyevent):

        if not self.iscomposing():
            if keyevent.keycode == vk_return or keyevent.keycode == vk_back:
                return false

        # 如果按下 alt，可能是應用程式熱鍵，輸入法不做處理
        if keyevent.iskeydown(vk_menu):
            return false

        # 如果按下 ctrl 鍵
        if keyevent.iskeydown(vk_control):
            return false

        return true

    def onkeydown(self, keyevent):

        # handle normal keyboard input
        if not self.iscomposing():
            if keyevent.keycode == vk_return or keyevent.keycode == vk_back:
                return false

        if keyevent.keycode == vk_return or keyevent.keycode == vk_space or len(self.compositionstring) > 10:
            self.setcommitstring(self.compositionstring)
            self.setcompositionstring("")

        elif keyevent.keycode == vk_back and self.compositionstring != "":
            self.setcompositionstring(self.compositionstring[:-1])

        elif keyevent.keycode == vk_left:
            i = self.compositioncursor - 1
            if i >= 0:
                self.setcompositioncursor(i)
        elif keyevent.keycode == vk_right:
            i = self.compositioncursor + 1
            if i <= len(self.compositionstring):
                self.setcompositioncursor(i)
        else:

            char_code = keyevent.charcode
            new_character = chr(char_code)

            self.setcompositionstring(self.compositionstring + new_character)
            self.setcompositioncursor(len(self.compositionstring))

        return true

    def oncommand(self, commandid, commandtype):
        print("oncommand", commandid, commandtype)
