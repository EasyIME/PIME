#! python3
from win32api import *
from win32pipe import *
from win32security import *
from win32event import *
from win32file import *
from winerror import *
from win32con import * # for VK_XXX constants
import threading
import json
import sys


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

    def init(self, msg):
        self.isWindows8Above = msg["isWindows8Above"]
        self.isMetroApp = msg["isMetroApp"]
        self.isUiLess = msg["isUiLess"]
        self.isUiLess = msg["isConsole"]
        self.keyboardOpen = False
        self.showCandidates = False

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


class DemoTextService(TextService):
    def __init__(self, client):
        TextService.__init__(self, client)

    def onActivate(self):
        TextService.onActivate(self)

    def onDeactivate(self):
        TextService.onDeactivate(self)

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
            self.setCandidateList(candidates)
            if keyEvent.keyCode == VK_DOWN:
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

    def filterKeyUp(self, keyEvent):
        return False

    def onKeyUp(self, keyEvent):
        return False

    def onKeyboardStatusChanged(self):
        TextService.onKeyboardStatusChanged(self)



class Client:
    def __init__(self, server, pipe):
        self.pipe= pipe
        self.server = server
        self.service = DemoTextService(self) # FIXME: allow different types of services here


    def handleRequest(self, msg): # msg is a json object
        success = True
        reply = dict()
        ret = None
        method = msg["method"]
        print("handle message: ", method, msg["seqNum"])

        service = self.service
        service.updateStatus(msg)

        if method == "init":
            service.init(msg)
        elif method == "onActivate":
            service.onActivate()
        elif method == "onDeactivate":
            service.onDeactivate()
        elif method == "filterKeyDown":
            keyEvent = KeyEvent(msg)
            ret = service.filterKeyDown(keyEvent)
        elif method == "onKeyDown":
            keyEvent = KeyEvent(msg)
            ret = service.onKeyDown(keyEvent)
        elif method == "filterKeyUp":
            keyEvent = KeyEvent(msg)
            ret = service.filterKeyUp(keyEvent)
        elif method == "onKeyUp":
            keyEvent = KeyEvent(msg)
            ret = service.onKeyUp(keyEvent)
        elif method == "onPreservedKey":
            ret = service.onPreservedKey()
        elif method == "onCommand":
            service.onCommand()
        elif method == "onCompartmentChanged":
            service.onCompartmentChanged()
        elif method == "onKeyboardStatusChanged":
            service.onKeyboardStatusChanged()
        elif method == "onCompositionTerminated":
            service.onCompositionTerminated()
        elif method == "onLangProfileActivated":
            pass
        elif method == "onLangProfileDeactivated":
            pass
        else:
            success = False

        reply["success"] = success
        reply["seqNum"] = msg["seqNum"] # reply with sequence number added
        if success:
            service.getStatus(reply)

        if ret != None:
            reply["return"] = ret
        return reply



class ClientThread(threading.Thread):
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.client = client
        self.buf = AllocateReadBuffer(512)

    def run(self):
        client = self.client
        pipe = client.pipe
        server = client.server

        running = True
        while running:
            # Read client requests from the pipe.
            # http://docs.activestate.com/activepython/3.3/pywin32/win32file__ReadFile_meth.html
            try:
                read_more = True
                msg = ''
                while read_more:
                    (success, data) = ReadFile(pipe, self.buf, None)
                    data = data.decode("UTF-8")
                    # print("data: ", data)
                    if success == 0: # success
                        msg += data
                        read_more = False
                    elif success == ERROR_MORE_DATA:
                        msg += data
                    elif success == ERROR_IO_PENDING:
                        pass
                    else: # the pipe is broken
                        print("broken pipe")
                        running = False

                # Process the incoming message.
                msg = json.loads(msg) # parse the json input
                # print("received msg", success, msg)

                server.acquire_lock() # acquire a lock
                reply = client.handleRequest(msg)
                server.release_lock() # release the lock

                reply = json.dumps(reply) # convert object to json
                WriteFile(pipe, bytes(reply, "UTF-8"), None)
            except:
                print("exception!", sys.exc_info())
                break

        FlushFileBuffers(pipe)
        DisconnectNamedPipe(pipe)
        CloseHandle(pipe)
        server.remove_client(client)

def createSecurityAttributes():
    # http://msdn.microsoft.com/en-us/library/windows/desktop/hh448449(v=vs.85).aspx
    # define new Win 8 app related constants
    SECURITY_APP_PACKAGE_AUTHORITY = (0,0,0,0,0,15)
    SECURITY_APP_PACKAGE_BASE_RID = 0x00000002
    SECURITY_BUILTIN_APP_PACKAGE_RID_COUNT = 2
    SECURITY_APP_PACKAGE_RID_COUNT = 8
    SECURITY_CAPABILITY_BASE_RID = 0x00000003
    SECURITY_BUILTIN_CAPABILITY_RID_COUNT = 2
    SECURITY_CAPABILITY_RID_COUNT = 5
    SECURITY_BUILTIN_PACKAGE_ANY_PACKAGE = 0x00000001

    explicit_accesses = []
    # Create a well-known SID for the Everyone group.
    # FIXME: we should limit the access to current user only
    everyoneSID = SID()
    SECURITY_WORLD_SID_AUTHORITY = (0,0,0,0,0,1)
    everyoneSID.Initialize(SECURITY_WORLD_SID_AUTHORITY, 1)
    everyoneSID.SetSubAuthority(0, SECURITY_WORLD_RID)

    # https://services.land.vic.gov.au/ArcGIS10.1/edESRIArcGIS10_01_01_3143/Python/pywin32/PLATLIB/win32/Demos/security/explicit_entries.py
    ea = {
        "AccessPermissions": GENERIC_ALL,
        "AccessMode": SET_ACCESS,
        "Inheritance": SUB_CONTAINERS_AND_OBJECTS_INHERIT,
        "Trustee": {
            "MultipleTrustee": None,
            "MultipleTrusteeOperation": 0,
            "TrusteeForm": TRUSTEE_IS_SID,
            "TrusteeType": TRUSTEE_IS_WELL_KNOWN_GROUP,
            "Identifier": everyoneSID
        }
    }
    explicit_accesses.append(ea)

    # create SID for app containers
    allAppsSID = SID()
    allAppsSID.Initialize(SECURITY_APP_PACKAGE_AUTHORITY, SECURITY_BUILTIN_APP_PACKAGE_RID_COUNT)
    allAppsSID.SetSubAuthority(0, SECURITY_APP_PACKAGE_BASE_RID)
    allAppsSID.SetSubAuthority(1, SECURITY_BUILTIN_PACKAGE_ANY_PACKAGE)

    ea = {
        "AccessPermissions": GENERIC_ALL,
        "AccessMode": SET_ACCESS,
        "Inheritance": SUB_CONTAINERS_AND_OBJECTS_INHERIT,
        "Trustee": {
            "MultipleTrustee": None,
            "MultipleTrusteeOperation": 0,
            "TrusteeForm": TRUSTEE_IS_SID,
            "TrusteeType": TRUSTEE_IS_GROUP,
            "Identifier": allAppsSID
        }
    }
    explicit_accesses.append(ea)

    # create DACL
    acl = ACL()
    acl.Initialize()
    acl.SetEntriesInAcl(explicit_accesses)

    # security descriptor
    sd = SECURITY_DESCRIPTOR()
    sd.Initialize()
    sd.SetDacl(True, acl, False)

    sa = SECURITY_ATTRIBUTES()
    sa.SECURITY_DESCRIPTOR = sd
    return sa



# https://msdn.microsoft.com/en-us/library/windows/desktop/aa365588(v=vs.85).aspx
class Server:

    def __init__(self):
        self.lock = threading.Lock()
        self.clients = []


    # This function creates a pipe instance and connects to the client.
    def create_pipe(self):
        name = "\\\\.\\pipe\\mynamedpipe"
        buffer_size = 1024
        # create the pipe
        sa = createSecurityAttributes()
        pipe = CreateNamedPipe(name,
                               PIPE_ACCESS_DUPLEX,
                               PIPE_TYPE_MESSAGE|PIPE_READMODE_MESSAGE|PIPE_WAIT,
                               PIPE_UNLIMITED_INSTANCES,
                               buffer_size,
                               buffer_size,
                               NMPWAIT_USE_DEFAULT_WAIT,
                               sa)
        # grantAppContainerAccess(pipe, SE_KERNEL_OBJECT, STANDARD_RIGHTS_ALL)
        return pipe


    def acquire_lock(self):
        self.lock.acquire()


    def release_lock(self):
        self.lock.release()


    def run(self):
        while True:
            pipe = self.create_pipe()
            if pipe == INVALID_HANDLE_VALUE:
                return False

            print("pipe created, wait for client")
            # Wait for the client to connect; if it succeeds, the function returns a nonzero value.
            # If the function returns zero, GetLastError returns ERROR_PIPE_CONNECTED.
            # According to Windows API doc, ConnectNamedPipe() returns non-zero on success.
            # However, the doc of pywin32 stated that it should return zero instead. :-(
            connected = (ConnectNamedPipe(pipe, None) == 0)
            if not connected:
                connected = (GetLastError() == ERROR_PIPE_CONNECTED)

            if connected: # client connected
                print("client connected")
                # create a Client instance for the client
                client = Client(self, pipe)
                self.lock.acquire()
                self.clients.append(client)
                self.lock.release()
                # run a separate thread for this client
                thread = ClientThread(client)
                thread.start()

        return True


    def remove_client(self, client):
        self.lock.acquire()
        self.clients.remove(client)
        print("client disconnected")
        self.lock.release()





def main():
    server = Server()
    server.run()
    server.close()

if __name__ == "__main__":
    main()
