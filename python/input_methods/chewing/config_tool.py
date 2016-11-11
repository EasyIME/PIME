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
import uuid  # use to generate a random auth token
import random
import json

from chewing_config import chewingConfig
from libchewing import ChewingContext
from ctypes import c_uint, byref, create_string_buffer


configDir = os.path.join(os.path.expandvars("%APPDATA%"), "PIME", "chewing")
currentDir = os.path.dirname(__file__)
dataDir = os.path.join(currentDir, "data")
localDataDir = os.path.join(os.path.expandvars("%LOCALAPPDATA%"), "PIME", "chewing")

COOKIE_ID = "chewing_config_token"

SERVER_TIMEOUT = 120
timeout_handler = None


# syspath 參數可包含多個路徑，用 ; 分隔
# 此處把 user 設定檔目錄插入到 system-wide 資料檔路徑前
# 如此使用者變更設定後，可以比系統預設值有優先權
search_paths = ";".join((chewingConfig.getConfigDir(), dataDir)).encode("UTF-8")
user_phrase = chewingConfig.getUserPhrase().encode("UTF-8")
print(search_paths, user_phrase)
chewing_ctx = ChewingContext(syspath = search_paths, userpath = user_phrase)  # new libchewing context


def quit_server():
    # terminate the server process
    tornado.ioloop.IOLoop.current().close()
    sys.exit(0)


class BaseHandler(tornado.web.RequestHandler):

    def get_current_user(self):  # override the login check
        return self.get_cookie(COOKIE_ID)


class KeepAliveHandler(BaseHandler):


    @tornado.web.authenticated
    def get(self):
        global timeout_handler
        loop = tornado.ioloop.IOLoop.current()
        if timeout_handler:
            loop.remove_timeout(timeout_handler)
            timeout_handler = loop.call_later(SERVER_TIMEOUT, quit_server)
        self.write("ok")


class ConfigHandler(BaseHandler):

    def get_current_user(self):  # override the login check
        return self.get_cookie(COOKIE_ID)

    @tornado.web.authenticated
    def get(self):  # get config
        data = {
            "config": self.load_config(),
            "symbols": self.load_data("symbols.dat"),
            "swkb": self.load_data("swkb.dat"),
        }
        self.write(data)

    @tornado.web.authenticated
    def post(self):  # save config
        data = tornado.escape.json_decode(self.request.body)
        print(data)
        # ensure the config dir exists
        os.makedirs(configDir, exist_ok=True)
        # write the config to files
        config = data.get("config", None)
        if config:
            self.save_file("config.json", json.dumps(config, indent=2))
        symbols = data.get("symbols", None)
        if symbols:
            self.save_file("symbols.dat", symbols)
        swkb = data.get("swkb", None)
        if swkb:
            self.save_file("swkb.dat", swkb)
        self.write("ok")

    @tornado.web.authenticated
    def delete(self):  # quit
        loop = tornado.ioloop.IOLoop.current()
        loop.call_later(0, quit_server)
        self.write("ok")

    def load_config(self):
        config = chewingConfig.toJson()  # the default settings
        try:
            with open(os.path.join(configDir, "config.json"), "r", encoding="UTF-8") as f:
                # override default values with user config
                config.update(json.load(f))
        except Exception as e:
            print(e)
        return config

    def load_data(self, name):
        try:
            userFile = os.path.join(configDir, name)
            with open(userFile, "r", encoding="UTF-8") as f:
                return f.read()
        except FileNotFoundError:
            with open(os.path.join(dataDir, name), "r", encoding="UTF-8") as f:
                return f.read()
        except Exception:
            return ""

    def save_file(self, filename, data):
        try:
            with open(os.path.join(configDir, filename), "w", encoding="UTF-8") as f:
                f.write(data)
                if file == "symbols":
                    f.write("\n")
        except Exception:
            pass


class UserPhraseHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):  # get all user phrases
        phrase_len = c_uint(0)
        bopomofo_len = c_uint(0)
        phrases = []
        ret = chewing_ctx.userphrase_enumerate()
        print(chewing_ctx, ret)
        while chewing_ctx.userphrase_has_next(byref(phrase_len), byref(bopomofo_len)):
            phrase_buf = create_string_buffer(phrase_len.value)
            bopomofo_buf = create_string_buffer(bopomofo_len.value)
            chewing_ctx.userphrase_get(phrase_buf, phrase_len, bopomofo_buf, bopomofo_len)
            phrase = phrase_buf.raw.decode("utf8").strip('\x00')
            bopomofo = bopomofo_buf.raw.decode("utf8").strip('\x00')
            phrases.append({
                "phrase": phrase,
                "bopomofo": bopomofo
            })
        self.write({"data": phrases})

    @tornado.web.authenticated
    def post(self):  # add new user phrases or remove existing ones
        data = tornado.escape.json_decode(self.request.body)
        added = data.get("add", [])
        removed = data.get("remove", [])
        print("add", added, "remove", removed)
        for item in added:  # add new phrases
            phrase = item["phrase"].encode("utf8")
            bopomofo = item["bopomofo"].encode("utf8")
            ret = chewing_ctx.userphrase_add(phrase, bopomofo)

        for item in removed:  # remove existing phrases
            phrase = item["phrase"].encode("utf8")
            bopomofo = item["bopomofo"].encode("utf8")
            chewing_ctx.userphrase_remove(phrase, bopomofo)
        # FIXME: correctly report errors!
        self.write({})


class LoginHandler(BaseHandler):

    def post(self, page_name):
        token = self.get_argument("token", "")
        if token == self.settings["access_token"]:
            self.set_cookie(COOKIE_ID, token)
            if page_name != "user_phrase_editor":
                page_name = "config_tool"
            self.redirect("/{}.html".format(page_name))


def launch_browser(port, page_name, access_token):
    user_html = """<html>
<form id="auth" action="http://127.0.0.1:{PORT}/login/{PAGE_NAME}" method="POST">
    <input type="hidden" name="token" value="{TOKEN}">
</form>
<script type="text/javascript">
    document.getElementById("auth").submit();
</script>
</html>""".format(PORT=port, PAGE_NAME=page_name, TOKEN=access_token)
    # use a local html file to send access token to our service via http POST for authentication.
    os.makedirs(localDataDir, exist_ok=True)
    filename = os.path.join(localDataDir, "launch_{}.html".format(page_name))
    with open(filename, "w") as f:
        f.write(user_html)
        os.startfile(filename)


def main():
    # generate a new auth token using UUID
    access_token = uuid.uuid4().hex
    settings = {
        "access_token": access_token, # our custom setting
        "login_url": "/version",
        "debug": True
    }
 
    app = tornado.web.Application([
        (r"/(.*\.html)", tornado.web.StaticFileHandler, {"path": currentDir}),
        (r"/((css|images|js)/.*)", tornado.web.StaticFileHandler, {"path": currentDir}),
        (r"/(version.txt)", tornado.web.StaticFileHandler, {"path": os.path.relpath("../../../", currentDir)}),
        (r"/config", ConfigHandler),  # main configuration handler
        (r"/user_phrases", UserPhraseHandler),  # user phrase editor
        (r"/keep_alive", KeepAliveHandler),  # keep the api server alive
        (r"/login/(.*)", LoginHandler),  # authentication
    ], **settings)

    # find a port number that's available
    random.seed()
    while True:
        port = random.randint(1025, 65535)
        try:
            app.listen(port, "127.0.0.1")
            break
        except OSError:  # it's possible that the port we want to use is already in use
            continue

    # launch web browser
    if len(sys.argv) >= 2 and sys.argv[1] == "user_phrase_editor":
        page_name = "user_phrase_editor"
    else:
        page_name = "config_tool"

    launch_browser(port, page_name, access_token)

    # setup the main event loop
    loop = tornado.ioloop.IOLoop.current()
    global timeout_handler
    timeout_handler = loop.call_later(SERVER_TIMEOUT, quit_server)
    loop.start()


if __name__ == "__main__":
    main()
