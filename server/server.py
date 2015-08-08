#! python3
from win32api import *
from win32pipe import *
from win32security import *
from win32event import *
from win32file import *
from winerror import *
from win32con import *
import threading
import json
import sys

from input_methods.serviceManager import textServiceMgr

class Client:
    def __init__(self, server, pipe):
        self.pipe= pipe
        self.server = server
        self.service = None

    def init(self, msg):
        self.isWindows8Above = msg["isWindows8Above"]
        self.isMetroApp = msg["isMetroApp"]
        self.isUiLess = msg["isUiLess"]
        self.isUiLess = msg["isConsole"]

    def onActivate(self):
        pass

    def onDeactivate(self):
        pass

    def onLangProfileActivated(self, guid):
        service = self.service
        # deactivate the current text service
        if service:
            service.onDeactivate()
        service = textServiceMgr.createService(self, guid)
        self.service = service
        # activate the new text service
        if service:
            service.onActivate()

    def onLangProfileDeactivated(self, guid):
        pass

    def handleRequest(self, msg): # msg is a json object
        success = True
        ret = None
        method = msg.get("method", None)
        seqNum = msg.get("seqNum", 0)
        print("handle message: ", threading.current_thread().name, method, seqNum)

        # these are messages handled by Client
        if method == "init":
            self.init(msg)
        elif method == "onActivate":
            self.onActivate()
        elif method == "onDeactivate":
            self.onDeactivate()
        elif method == "onLangProfileActivated":
            guid = msg["guid"]
            self.onLangProfileActivated(guid)
        elif method == "onLangProfileDeactivated":
            guid = msg["guid"]
            self.onLangProfileDeactivated(guid)

        reply = {}
        # these are messages handled by the text service
        service = self.service
        if service:
            (success, ret) = service.handleRequest(method, msg)
            if success:
                reply = service.getReply()
                print(reply)
            if ret != None:
                reply["return"] = ret
        reply["success"] = success
        reply["seqNum"] = seqNum # reply with sequence number added
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
                msg = ""
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
                import traceback
                # print callstatck to know where the exceptions is
                traceback.print_exc()

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
    # See this article for details: https://msdn.microsoft.com/en-us/library/windows/desktop/hh448493(v=vs.85).aspx
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
        username = GetUserName()
        # add username to the pipe path so it will not clash with other users' pipes.
        name = "\\\\.\\pipe\\%s\\PIME_pipe" % username
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

            # client connected
            if connected:
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
