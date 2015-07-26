from win32api import *
from win32pipe import *
from win32security import *
from win32event import *
from win32file import *
from winerror import *
import threading
import json
import sys


class TextService:
    def __init__(self, client):
        self.client = client

    def init(self, msg):
        self.id = msg["id"]
        self.isWindows8Above = msg["isWindows8Above"]
        self.isMetroApp = msg["isMetroApp"]
        self.isUiLess = msg["isUiLess"]
        self.isUiLess = msg["isConsole"]

    def sendRequest(self, msg):
        client.pipe

    # methods that should be implemented by derived classes
    def onActivate(self):
        pass

    def onDeactivate(self):
        pass

    def filterKeyDown(self):
        return False

    def onKeyDown(self):
        return False

    def filterKeyUp(self):
        return False

    def onKeyUp(self):
        return False

    def onCommand(self):
        pass

    def onCompartmentChanged(self):
        pass

    def onKeyboardStatusChanged(self):
        pass

    # public methods that should not be touched
    def langBarStatus(self):
        pass

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

    # text composition handling
    def isComposing(self):
        return False

    # is keyboard disabled for the context (NULL means current context)
    # bool isKeyboardDisabled(ITfContext* context = NULL);

    # is keyboard opened for the whole thread
    def isKeyboardOpened(self):
        return True

    def setKeyboardOpen(self, kb_open):
        pass

    def startComposition(self, context):
        pass

    def endComposition(self, context):
        pass

    def setCompositionString(self, cs, cs_len):
        pass

    def setCompositionCursor(self, pos):
        pass



class DemoTextService(TextService):
    def __init__(self, client):
        TextService.__init__(self, client)

    def onActivate(self):
        pass

    def onDeactivate(self):
        pass

    def filterKeyDown(self):
        return True

    def onKeyDown(self):
        return True

    def filterKeyUp(self):
        return False

    def onKeyUp(self):
        return False

    def onCommand(self):
        pass

    def onCompartmentChanged(self):
        pass

    def onKeyboardStatusChanged(self):
        pass




class Client:
    def __init__(self, server, pipe):
        self.pipe= pipe
        self.server = server
        self.service = DemoTextService(self) # FIXME: allow different types of services here


    def handle_request(self, msg): # msg is a json object
        success = True
        reply = dict()
        ret = None
        method = msg["method"]
        print("handle message: ", method)
        service = self.service
        if method == "init":
            service.init(msg)
        elif method == "onActivate":
            service.onActivate()
        elif method == "onDeactivate":
            service.onDeactivate()
        elif method == "filterKeyDown":
            ret = service.filterKeyDown()
        elif method == "onKeyDown":
            ret = service.onKeyDown()
        elif method == "filterKeyUp":
            ret = service.filterKeyUp()
        elif method == "onKeyUp":
            ret = service.onKeyUp()
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
        reply["success"] = success
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
                reply = client.handle_request(msg)
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


# https://msdn.microsoft.com/en-us/library/windows/desktop/aa365588(v=vs.85).aspx
class Server:

    def __init__(self):
        self.lock = threading.Lock()
        self.clients = []


    # This function creates a pipe instance and connects to the client.
    def create_pipe(self):
        name = "\\\\.\\pipe\\mynamedpipe"
        sa = SECURITY_ATTRIBUTES()
        buffer_size = 1024
        sa = None
        # create the pipe
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
