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

import os.path

import copy

from input_methods.arabic import CinBase
from input_methods.arabic import LoadCinTable
from input_methods.arabic.config import CinBaseConfig
from textService import *


class ArabicTextService(TextService):
    compositionChar = ''

    def __init__(self, client):
        TextService.__init__(self, client)

        # Input method module customization area
        self.imeDirName = "arabic"
        self.maxCharLength = 26  # Maximum number of encoding characters for input method
        self.cinFile = "arabic.json"

        self.cinbase = CinBase
        self.curdir = os.path.abspath(os.path.dirname(__file__))

        # Initialize input behavior settings
        self.cinbase.initTextService(self, TextService)

        # Load user settings
        CinBaseConfig.__init__()
        self.configVersion = CinBaseConfig.getVersion()
        self.cfg = copy.deepcopy(CinBaseConfig)
        self.cfg.imeDirName = self.imeDirName
        self.cfg.cinFile = self.cinFile
        self.cfg.load()
        self.jsondir = self.cfg.getJsonDir()
        self.cinbase.initCinBaseContext(self)

        # Load input method code table
        if not CinTable.loading:
            loadCinFile = LoadCinTable(self, CinTable)
            loadCinFile.start()
        else:
            while CinTable.loading:
                continue
            self.cin = CinTable.cin

    # Check whether the configuration file has been changed and whether the new settings need to be applied
    def checkConfigChange(self):
        self.cinbase.checkConfigChange(self, CinTable)

    # Input method is activated by user
    def onActivate(self):
        TextService.onActivate(self)
        self.cinbase.onActivate(self)

    # User leaves the input method
    def onDeactivate(self):
        TextService.onDeactivate(self)
        self.cinbase.onDeactivate(self)

    # The user presses the keys and filters those keys before the app receives them,
    # which is required by the input method.
    # return True, the system will call onKeyDown() to further process the button
    # return False， means that we don’t need this key, the system will pass the key to the application intact
    def filterKeyDown(self, keyEvent):
        KeyState = self.cinbase.filterKeyDown(self, keyEvent, CinTable)
        return KeyState

    def onKeyDown(self, keyEvent):
        KeyState = self.cinbase.onKeyDown(self, keyEvent, CinTable)
        return KeyState

    # The user releases the keys and filters those keys before the app receives them,
    # which is required by the input method.
    # return True， the system will call onKeyUp() to further process this button
    # return False， means that we don’t need this key, the system will pass the key to the application intact
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

    # Open language bar button menu
    def onMenu(self, buttonId):
        MenuItems = self.cinbase.onMenu(self, buttonId)
        return MenuItems

    # Called when the keyboard is turned on/off (in Windows 10 Ctrl+Space)
    def onKeyboardStatusChanged(self, opened):
        TextService.onKeyboardStatusChanged(self, opened)
        self.cinbase.onKeyboardStatusChanged(self, opened)

    # It will be called when the Chinese editing is finished.
    # If Chinese editing does not end normally, but because
    # the user switches to other applications or other reasons,
    # our input method is forcibly closed, then the forced parameter will be True.
    # In this case, some buffers should be cleared.
    def onCompositionTerminated(self, forced):
        TextService.onCompositionTerminated(self, forced)
        self.cinbase.onCompositionTerminated(self, forced)

    # Set the number of candidate pages
    def setCandidatePage(self, page):
        self.currentCandPage = page


class CinTable:
    loading = False

    def __init__(self):
        self.cin = None
        self.curCinType = None


CinTable = CinTable()
