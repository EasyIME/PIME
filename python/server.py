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
import os
import random
import uuid

if __name__ == "__main__":
    sys.path.append('python3')

from serviceManager import textServiceMgr


class Client(object):
    def __init__(self, server):
        self.server = server
        self.service = None

    def init(self, msg):
        self.guid = msg["id"]
        self.isWindows8Above = msg["isWindows8Above"]
        self.isMetroApp = msg["isMetroApp"]
        self.isUiLess = msg["isUiLess"]
        self.isUiLess = msg["isConsole"]
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
        # FIXME: this uses the AppData/Roaming dir, but we want the local one.
        #        alternatively, use the AppData/Temp dir.
        self.config_dir = os.path.join(os.path.expandvars("%APPDATA%"), "PIME")
        os.makedirs(self.config_dir, mode=0o700, exist_ok=True)
        # self.status_dir = os.path.join(os.path.expandvars("%LOCALAPPDATA%"), "PIME", "status")  # local app data dir

    def run(self):
        print("running:")
        while True:
            try:
                line = input().strip()
                print("RECV:", line)
                client_id, msg_text = line.split('\t', maxsplit=1)
                msg = json.loads(msg_text)
                client = self.clients.get(client_id)
                if not client:
                    # create a Client instance for the client
                    client = Client(self)
                    self.clients[client_id] = client
                    print("new client:", client_id)
                if msg.get("method") == "close":  # special handling for closing a client
                    self.remove_client(client_id)
                else:
                    ret = client.handleRequest(msg)
                    # Send the response to the client via stdout
                    # one response per line, prefixed with PIME_MSG:
                    print("PIME_MSG:{}\t{}".format(client_id, json.dumps(ret)))
            except Exception as e:
                print("ERROR:", e)

    def remove_client(self, client_id):
        print("client disconnected:", client_id)
        try:
            del self.clients[client_id]
        except KeyError:
            pass


def main():
    server = Server()
    server.run()


if __name__ == "__main__":
    main()
