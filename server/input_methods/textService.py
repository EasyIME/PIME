#! python3

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

    def updateStatus(self, msg):
        if "keyboardOpen" in msg:
            self.keyboardOpen = msg["keyboardOpen"]
        if "showCandidates" in msg:
            self.showCandidates = msg["showCandidates"]


    # encode current status into an json object
    def getReply(self):
        reply = self.reply
        self.reply = {}
        return reply


    def handleRequest(self, method, msg): # msg is a json object
        success = True # if the method is successfully handled
        ret = None # the return value of the method, if any

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
            ret = self.onPreservedKey()
        elif method == "onCommand":
            commandId = msg["id"]
            commandType = msg["type"]
            self.onCommand(commandId, commandType)
        elif method == "onCompartmentChanged":
            self.onCompartmentChanged()
        elif method == "onKeyboardStatusChanged":
            self.onKeyboardStatusChanged()
        elif method == "onCompositionTerminated":
            self.onCompositionTerminated()
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

    def onCommand(self, commandId, commandType):
        pass

    def onCompartmentChanged(self):
        pass

    def onCompositionTerminated(self):
        self.commitString = ""

    def onKeyboardStatusChanged(self):
        pass

    # public methods that should not be touched

    # language bar buttons
    def addButton(self, button):
        buttons = self.reply.setdefault("addButton", [])
        buttons.append(button)

    def removeButton(self, button_id):
        buttons = self.reply.setdefault("removeButton", [])
        buttons.append(button_id)

    def changeButton(self, button):
        buttons = self.reply.setdefault("changeButton", [])
        buttons.append(button)

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

    def setShowCandidates(self, show):
        self.showCandidates = show
        self.reply["showCandidates"] = show

    def isComposing(self):
        return (self.compositionString != "")
