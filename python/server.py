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

import json
import sys
import traceback
import os

if __name__ == "__main__":
    sys.path.append('python3')

sys.path.append(os.path.dirname(__file__))    


from serviceManager import textServiceMgr


def append_error_log(message):
    try:
        log_dir = os.path.join(os.path.expandvars("%LOCALAPPDATA%"), "PIME", "Logs")
        os.makedirs(log_dir, mode=0o700, exist_ok=True)
        with open(os.path.join(log_dir, "python_backend.log"), "a", encoding="utf-8") as log_file:
            log_file.write(message)
            if not message.endswith("\n"):
                log_file.write("\n")
    except Exception:
        pass


class Client(object):
    def __init__(self, server):
        self.server = server
        self.service = None

    def init(self, msg):
        self.guid = msg["id"]
        self.isWindows8Above = msg["isWindows8Above"]
        self.isMetroApp = msg["isMetroApp"]
        self.isUiLess = msg["isUiLess"]
        self.isConsole = msg["isConsole"]
        # create the text service
        self.service = textServiceMgr.createService(self, self.guid)
        return (self.service is not None)

    def handleRequest(self, msg): # msg is a json object
        method = msg.get("method")
        seqNum = msg.get("seqNum", 0)
        # print("handle message: ", str(id(self)), method, seqNum)
        service = self.service
        if service:
            # let the text service handle the message
            reply = service.handleRequest(msg)
        else:  # the text service is not yet initialized
            reply = {"seqNum": seqNum}
            success = False
            if method == "init": # initialize the text service
                success = self.init(msg)
            reply["success"] = success
        # print(reply)
        return reply


class Server(object):
    def __init__(self):
        self.clients = {}

    def run(self):
        while True:
            line = ""
            client_id = ""
            try:
                line = input().strip()
                if not line:
                    continue
                # parse PIME requests (one request per line):
                # request format: "<client_id>|<JSON string>\n"
                # response format: "PIME_MSG|<client_id>|<JSON string>\n"
                parts = line.split('|', maxsplit=1)
                if len(parts) != 2:
                    print("ERROR: malformed request:", line, file=sys.stderr)
                    append_error_log("ERROR: malformed request: {0}\n".format(line))
                    continue
                client_id, msg_text = parts
                msg = json.loads(msg_text)
                client = self.clients.get(client_id)
                if not client:
                    # create a Client instance for the client
                    client = Client(self)
                    self.clients[client_id] = client
                    print("new client:", client_id, file=sys.stderr)
                if msg.get("method") == "close":  # special handling for closing a client
                    self.remove_client(client_id)
                else:
                    ret = client.handleRequest(msg)
                    # Send the response to the client via stdout
                    # one response per line in the format "PIME_MSG|<client_id>|<json reply>"
                    reply_line = '|'.join(["PIME_MSG", client_id, json.dumps(ret, ensure_ascii=False)])
                    print(reply_line, flush=True)
            except EOFError:
                # stop the server
                break
            except Exception as e:
                print("ERROR:", e, line, file=sys.stderr)
                # print the exception traceback for ease of debugging
                traceback.print_exc()
                append_error_log("ERROR: {0}\nREQUEST: {1}\n{2}\n".format(e, line, traceback.format_exc()))
                # generate an empty output containing {success: False} to prevent the client from being blocked
                reply_line = '|'.join(["PIME_MSG", client_id, '{"success":false}'])
                print(reply_line, flush=True)
                # Keep the backend alive after one bad request; tearing down an
                # active TSF session can destabilize the foreground application.
                continue

    def remove_client(self, client_id):
        print("client disconnected:", client_id, file=sys.stderr)
        try:
            del self.clients[client_id]
        except KeyError:
            pass


def main():
    server = Server()
    server.run()


if __name__ == "__main__":
    main()
