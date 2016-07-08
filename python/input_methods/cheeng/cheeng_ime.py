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

class CheEngTextService(TextService):
    def __init__(self, client):
        TextService.__init__(self, client)
        self.icon_dir = os.path.abspath(os.path.dirname(__file__))

    def onActivate(self):
        TextService.onActivate(self)
        
        icon_name = "eng.ico"
        # Windows 8 以上已取消語言列功能，改用 systray IME mode icon
        if self.client.isWindows8Above:
            self.addButton("windows-mode-icon",
                icon=os.path.join(self.icon_dir, icon_name),
                tooltip="英數模式"
            )

    def onDeactivate(self):
        TextService.onDeactivate(self)
        if self.client.isWindows8Above:
            self.removeButton("windows-mode-icon")

