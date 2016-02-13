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

# button style constants used by language buttons (from ctfutb.h of Windows SDK)
TF_LBI_STYLE_HIDDENSTATUSCONTROL = 0x00000001
TF_LBI_STYLE_SHOWNINTRAY         = 0x00000002
TF_LBI_STYLE_HIDEONNOOTHERITEMS  = 0x00000004
TF_LBI_STYLE_SHOWNINTRAYONLY     = 0x00000008
TF_LBI_STYLE_HIDDENBYDEFAULT     = 0x00000010
TF_LBI_STYLE_TEXTCOLORICON       = 0x00000020
TF_LBI_STYLE_BTN_BUTTON          = 0x00010000
TF_LBI_STYLE_BTN_MENU            = 0x00020000
TF_LBI_STYLE_BTN_TOGGLE          = 0x00040000

# keyboard modifiers used by TSF (from msctf.h of Windows SDK)
TF_MOD_ALT                       = 0x0001
TF_MOD_CONTROL                   = 0x0002
TF_MOD_SHIFT                     = 0x0004
TF_MOD_RALT                      = 0x0008
TF_MOD_RCONTROL                  = 0x0010
TF_MOD_RSHIFT                    = 0x0020
TF_MOD_LALT                      = 0x0040
TF_MOD_LCONTROL                  = 0x0080
TF_MOD_LSHIFT                    = 0x0100
TF_MOD_ON_KEYUP                  = 0x0200
TF_MOD_IGNORE_ALL_MODIFIER       = 0x0400

# command type parameter of TextService.onCommand
COMMAND_LEFT_CLICK  = 0
COMMAND_RIGHT_CLICK = 1
COMMAND_MENU        = 2

class KeyEvent:
    def __init__(self, msg):
        self.charCode = msg["charCode"]
        self.keyCode = msg["keyCode"]
        self.repeatCount = msg["repeatCount"]
        self.scanCode = msg["scanCode"]
        self.isExtended = msg["isExtended"]
        self.keyStates = msg["keyStates"]

    def isKeyDown(self, code):
        return (self.keyStates[code] & (1 << 7)) != 0

    def isKeyToggled(self, code):
        return (self.keyStates[code] & 1) != 0

    def isChar(self):
        return (self.charCode != 0)

    def isPrintableChar(self, includingSpace = False):
        if includingSpace and self.charCode == ord(' '):
            return True
        return self.charCode > 0x1f and self.charCode != 0x7f


class TextService:
    def __init__(self, client):
        self.client = client

        self.keyboardOpen = False
        self.showCandidates = False

        self.reply = {} # reply to the events
        self.compositionString = ""
        self.commitString = ""
        self.candidateList = []
        self.compositionCursor = 0
        self.candCursor = 0

    def updateStatus(self, msg):
        pass

    # encode current status into an json object
    def getReply(self):
        reply = self.reply
        self.reply = {}
        return reply

    # This should be implemented in the derived class
    def checkConfigChange(self):
        pass

    def handleRequest(self, method, msg): # msg is a json object
        success = True # if the method is successfully handled
        ret = None # the return value of the method, if any

        self.checkConfigChange() # check if configurations are changed

        self.updateStatus(msg)
        if method == "filterKeyDown":
            keyEvent = KeyEvent(msg)
            ret = self.filterKeyDown(keyEvent)
        elif method == "onKeyDown":
            keyEvent = KeyEvent(msg)
            ret = self.onKeyDown(keyEvent)
        elif method == "filterKeyUp":
            keyEvent = KeyEvent(msg)
            ret = self.filterKeyUp(keyEvent)
        elif method == "onKeyUp":
            keyEvent = KeyEvent(msg)
            ret = self.onKeyUp(keyEvent)
        elif method == "onPreservedKey":
            guid = msg["guid"].lower()
            ret = self.onPreservedKey(guid)
        elif method == "onCommand":
            commandId = msg["id"]
            commandType = msg["type"]
            self.onCommand(commandId, commandType)
        elif method == "onCompartmentChanged":
            guid = msg["guid"].lower()
            self.onCompartmentChanged(guid)
        elif method == "onKeyboardStatusChanged":
            opened = msg["opened"]
            self.onKeyboardStatusChanged(opened)
        elif method == "onCompositionTerminated":
            forced = msg["forced"]
            self.onCompositionTerminated(forced)
        else:
            success = False

        return success, ret
        
    # methods that should be implemented by derived classes
    def onActivate(self):
        pass

    def onDeactivate(self):
        pass

    def filterKeyDown(self, keyEvent):
        return False

    def onKeyDown(self, keyEvent):
        return False

    def filterKeyUp(self, keyEvent):
        return False

    def onKeyUp(self, keyEvent):
        return False

    def onPreservedKey(self, guid):
        print("onPreservedKey", guid)
        return False

    def onCommand(self, commandId, commandType):
        pass

    def onCompartmentChanged(self, guid):
        pass

    def onCompositionTerminated(self, forced):
        self.commitString = ""

    def onKeyboardStatusChanged(self, opened):
        pass

    # public methods that should not be touched

    # language bar buttons
    """
    allowed arguments:
    @icon: full path to a *.ico file
    @commandId: an integer ID which will be passed to onCommand()
        when the button is clicked.
    @text: text on the button (optional)
    @tooltip: (optional)
    @enable: if the button is enabled (optional)
    """
    def addButton(self, button_id, **kwargs):
        buttons = self.reply.setdefault("addButton", [])
        info = kwargs
        info["id"] = button_id
        buttons.append(info)

    def removeButton(self, button_id):
        buttons = self.reply.setdefault("removeButton", [])
        buttons.append(button_id)

    """
    See addButton() for allowed arguments.
    """
    def changeButton(self, button_id, **kwargs):
        buttons = self.reply.setdefault("changeButton", [])
        info = kwargs
        info["id"] = button_id
        buttons.append(info)

    # preserved keys
    def addPreservedKey(self, keyCode, modifiers, guid):
        keys = self.reply.setdefault("addPreservedKey", [])
        keys.append({
            "keyCode" : keyCode,
            "modifiers": modifiers,
            "guid": guid.lower()})

    def removePreservedKey(self, guid):
        keys = self.reply.setdefault("removePreservedKey", [])
        keys.append(guid.lower())

    # composition string
    def setCompositionString(self, s):
        self.compositionString = s
        self.reply["compositionString"] = s

    def setCompositionCursor(self, pos):
        self.compositionCursor = pos
        self.reply["compositionCursor"] = pos

    def setCommitString(self, s):
        self.commitString = s
        self.reply["commitString"] = s

    def setCandidateList(self, cand):
        self.candidateList = cand
        self.reply["candidateList"] = cand

    def setCandidateCursor(self, pos):
        self.candidateCursor = pos
        self.reply["candCursorPos"] = pos

    def setShowCandidates(self, show):
        self.showCandidates = show
        self.reply["showCandidates"] = show

    def setSelKeys(self, keys):
        self.reply["setSelKeys"] = keys

    '''
    Valid arguments:
    candFontName, cadFontSize, candPerRow, candUseCursor
    '''
    def customizeUI(self, **kwargs):
        data = self.reply.setdefault("customizeUI", {})
        data.update(kwargs)

    def isComposing(self):
        return (self.compositionString != "")
