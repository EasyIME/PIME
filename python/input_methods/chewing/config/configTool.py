#! python3
# Copyright (C) 2016 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
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

import tornado.ioloop
import tornado.web
import sys
import os
from ctypes import windll  # for calling Windows api
import uuid  # use to generate a random auth token
import random

configDir = os.path.join(os.path.expandvars("%APPDATA%"), "PIME", "chewing")
dataDir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

SERVER_TIMEOUT = 120
timeout_handler = None
auth_token = ""
authenticated = False


class LoadHandler(tornado.web.RequestHandler):
    def get(self, file):
        global authenticated
        if not authenticated:
            return
        if file == "config":
            self.load_config()
        elif file == "symbols":
            self.load_data("symbols.dat")
        elif file == "swkb":
            self.load_data("swkb.dat")
        else:
            self.write("")

    def load_config(self):
        try:
            with open(os.path.join(configDir, "config.json"), "r", encoding="UTF-8") as f:
                content = f.read()
                if not content:
                    content = "{}"
                self.write(content)
        except Exception:
            self.write("{}")

    def load_data(self, name):
        try:
            userFile = os.path.join(configDir, name)
            with open(userFile, "r", encoding="UTF-8") as f:
                self.write(f.read())
        except FileNotFoundError:
            with open(os.path.join(dataDir, name), "r", encoding="UTF-8") as f:
                self.write(f.read())
        except Exception:
            self.write("")


class SaveHandler(tornado.web.RequestHandler):
    def post(self, file):
        global authenticated
        if not authenticated:
            return
        data = self.get_argument("data", '')
        if file == "config":
            filename = "config.json"
        elif file == "symbols":
            filename = "symbols.dat"
        elif file == "swkb":
            filename = "swkb.dat"
        else:
            return
        os.makedirs(configDir, exist_ok=True)
        filename = os.path.join(configDir, filename)
        try:
            # print(filename, data)
            with open(filename, "w", encoding="UTF-8") as f:
                f.write(data)
                if file == "symbols":
                    f.write("\n")
            self.write("ok")
        except Exception:
            self.write("failed")


def quit_server():
    # terminate the server process
    tornado.ioloop.IOLoop.current().close()
    sys.exit(0)


class KeepAliveHandler(tornado.web.RequestHandler):
    def get(self):
        global authenticated
        if not authenticated:
            return
        global timeout_handler
        loop = tornado.ioloop.IOLoop.current()
        if timeout_handler:
            loop.remove_timeout(timeout_handler)
            timeout_handler = loop.call_later(SERVER_TIMEOUT, quit_server)
        self.write("ok")


class AuthHandler(tornado.web.RequestHandler):
    def post(self):
        token = self.get_argument("token", '')
        if token == auth_token:
            global authenticated
            authenticated = True
        self.write("ok" if authenticated else "failed")


class QuitHandler(tornado.web.RequestHandler):
    def get(self):
        global authenticated
        if authenticated:
            loop = tornado.ioloop.IOLoop.current()
            loop.call_later(0, quit_server)
            self.write("ok")


# Launch the HTA browser-based UI
def launch_browser(port):
    dirname = os.path.dirname(__file__)
    hta_file = os.path.join(dirname, "configUI.hta")
    # os.startfile(hta_file)
    # launch the hta file with ShellExecute since we need to pass port number as parameter
    global auth_token
    params = "{0} {1}".format(port, auth_token)
    windll.shell32.ShellExecuteW(None, "open", hta_file, params, dirname, 1)  # SW_SHOWNORMAL = 1


def main():
    app = tornado.web.Application([
        (r"/auth", AuthHandler),  # simple authentication
        (r"/keep_alive", KeepAliveHandler),  # keep the api server alive
        (r"/load/(.+)", LoadHandler),
        (r"/save/(.+)", SaveHandler),
        (r"/quit", QuitHandler)
    ])

    # find a port number that's available
    random.seed()
    while True:
        port = random.randint(5566, 32767)
        try:
            app.listen(port, "127.0.0.1")
            break
        except OSError:  # it's possible that the port we want to use is already in use
            continue

    # generate a new auth token using UUID
    global auth_token
    auth_token = uuid.uuid4().hex
    launch_browser(port)

    # setup the main event loop
    loop = tornado.ioloop.IOLoop.current()
    global timeout_handler
    timeout_handler = loop.call_later(SERVER_TIMEOUT, quit_server)
    loop.start()


if __name__ == "__main__":
    main()
