#! python3

class TextService:
    def __init__(self, client):
        self.client = client
        self.serviceName = "Text"

        self.keyboardOpen = False
        self.showCandidates = False

        self.compositionString = ""
        self.commitString = ""
        self.candidateList = []
        self.compositionCursor = 0

    def init(self, msg):
        self.isWindows8Above = msg["isWindows8Above"]
        self.isMetroApp = msg["isMetroApp"]
        self.isUiLess = msg["isUiLess"]
        self.isUiLess = msg["isConsole"]

    def getServiceName(self):
        return self.serviceName

    def updateStatus(self, msg):
        if "keyboardOpen" in msg:
            self.keyboardOpen = msg["keyboardOpen"]
        if "showCandidates" in msg:
            self.showCandidates = msg["showCandidates"]


    # encode current status into an json object
    def getStatus(self, msg):
        msg["showCandidates"] = self.showCandidates
        msg["compositionString"] = self.compositionString
        msg["commitString"] = self.commitString
        msg["candidateList"] = self.candidateList
        msg["compositionCursor"] = self.compositionCursor


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

    def onCommand(self):
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
        pass

    def removeButton(self, button):
        pass

    # preserved keys
    def addPreservedKey(self, keyCode, modifiers, guid):
        pass

    def removePreservedKey(self, guid):
        pass

    # composition string
    def setCompositionString(self, s):
        self.compositionString = s

    def setCompositionCursor(self, pos):
        self.compositionCursor = pos

    def setCommitString(self, s):
        self.commitString = s

    def setCandidateList(self, cand):
        self.candidateList = cand

    def setShowCandidates(self, show):
        self.showCandidates = show

    def isComposing(self):
        return (self.compositionString != "")
