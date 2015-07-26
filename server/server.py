from win32api import *
from win32pipe import *
from win32security import *
from win32event import *
from win32file import *
from winerror import *
import threading
import json
import sys


class ImeEngine:
    def __init__(self, client):
        self.client = client

    def onActivate(self):
        pass

    def onDeactivate(self):
        pass

    def filterKeyDown(self):
        pass

    def onKeyDown(self):
        pass

    def filterKeyUp(self):
        pass

    def onKeyUp(self):
        pass

    def onCommand(self):
        pass

    def onCompartmentChanged(self):
        pass

    def onKeyboardStatusChanged(self):
        pass

    def onLangProfileActivated(self):
        pass

    def onLangProfileDeactivated(self):
        pass


class Client:
    def __init__(self, server, pipe):
        self.pipe= pipe
        self.server = server
        self.engine = ImeEngine(self)


    def handle_request(self, msg): # msg is a json object
        ret = dict()
        method = msg["method"]
        print("handle message: ", method)
        engine = self.engine
        if method == "onActivate":
            engine.onActivate()
        elif method == "onDeactivate":
            engine.onDeactivate()
        elif method == "filterKeyDown":
            engine.filterKeyDown()
        elif method == "onKeyDown":
            engine.onKeyDown()
        elif method == "filterKeyUp":
            engine.filterKeyUp()
        elif method == "onKeyUp":
            engine.onKeyUp()
        elif method == "onPreservedKey":
            engine.onPreservedKey()
        elif method == "onCommand":
            engine.onCommand()
        elif method == "onCompartmentChanged":
            engine.onCompartmentChanged()
        elif method == "onKeyboardStatusChanged":
            engine.onKeyboardStatusChanged()
        elif method == "onCompositionTerminated":
            engine.onCompositionTerminated()
        elif method == "onLangProfileActivated":
            engine.onLangProfileActivated()
        elif method == "onLangProfileDeactivated":
            engine.onLangProfileDeactivated()
        return ret


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
                    print("data: ", data)
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
