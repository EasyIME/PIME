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

current_dir = os.path.dirname(__file__)

# The libchewing package is not in the default python path.
# FIXME: set PYTHONPATH properly so we don't need to add this hack.
sys.path.append(os.path.dirname(os.path.dirname(current_dir)))

from chewing_config import chewingConfig
from libchewing import ChewingContext, CHEWING_DATA_DIR
from ctypes import c_uint, byref, create_string_buffer

config_dir = os.path.join(os.path.expandvars("%APPDATA%"), "PIME", "chewing")
localdata_dir = os.path.join(os.path.expandvars("%LOCALAPPDATA%"), "PIME", "chewing")

COOKIE_ID = "chewing_config_token"

SERVER_TIMEOUT = 120

# syspath 參數可包含多個路徑，用 ; 分隔
# 此處把 user 設定檔目錄插入到 system-wide 資料檔路徑前
# 如此使用者變更設定後，可以比系統預設值有優先權
search_paths = ";".join((chewingConfig.getConfigDir(), CHEWING_DATA_DIR)).encode("UTF-8")
user_phrase = chewingConfig.getUserPhrase().encode("UTF-8")
# print(search_paths, user_phrase)
chewing_ctx = ChewingContext(syspath = search_paths, userpath = user_phrase)  # new libchewing context


class BaseHandler(tornado.web.RequestHandler):

    def get_current_user(self):  # override the login check
        return self.get_cookie(COOKIE_ID)

    def prepare(self):  # called before every request
        self.application.reset_timeout()  # reset the quit server timeout


class KeepAliveHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        # the actual keep-alive is done inside BaseHandler.prepare()
        self.write('{"return":true}')


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
        #print(data)
        # ensure the config dir exists
        os.makedirs(config_dir, exist_ok=True)
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
        self.write('{"return":true}')

    def load_config(self):
        config = chewingConfig.toJson()  # the default settings
        try:
            with open(os.path.join(config_dir, "config.json"), "r", encoding="UTF-8") as f:
                # override default values with user config
                config.update(json.load(f))
        except Exception as e:
            print(e)
        return config

    def load_data(self, name):
        try:
            userFile = os.path.join(config_dir, name)
            with open(userFile, "r", encoding="UTF-8") as f:
                return f.read()
        except FileNotFoundError:
            with open(os.path.join(CHEWING_DATA_DIR, name), "r", encoding="UTF-8") as f:
                return f.read()
        except Exception:
            return ""

    def save_file(self, filename, data):
        try:
            with open(os.path.join(config_dir, filename), "w", encoding="UTF-8") as f:
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
            add_result = chewing_ctx.userphrase_add(phrase, bopomofo)

        for item in removed:  # remove existing phrases
            phrase = item["phrase"].encode("utf8")
            bopomofo = item["bopomofo"].encode("utf8")
            chewing_ctx.userphrase_remove(phrase, bopomofo)

        self.write({"add_result": add_result})


class UserPhraseFileHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):  # download user phrase file
        user_phrase_file = os.path.join(config_dir, "chewing.sqlite3")
        if not os.path.exists(user_phrase_file):
            raise HTTPError(404)
        self.set_header("Content-Type", "application/force-download")
        self.set_header("Content-Disposition", "attachment; filename=chewing.sqlite3")
        with open(user_phrase_file, "rb") as f:
            try:
                self.write(f.read())
                f.close()
                self.finish()
                return
            except:
                raise HTTPError(404)
        raise HTTPError(500)

    @tornado.web.authenticated
    def post(self):  # upload file
        try:
            temp_user_phrase = os.path.join(config_dir, "chewing_tmp.sqlite3")
            origin_user_phrase = os.path.join(config_dir, "chewing.sqlite3")
            temp_user_phrase_file = open(temp_user_phrase, "wb")
            temp_user_phrase_file.write(self.request.files["import_user_phrase"][0]["body"])
            temp_user_phrase_file.close()
            # error check
            import sqlite3
            conn = sqlite3.connect(temp_user_phrase)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM config_v1")
            conn.close()

            user_phrase_file = open(origin_user_phrase, "wb")
            user_phrase_file.write(self.request.files["import_user_phrase"][0]["body"])
            user_phrase_file.close()
            os.remove(temp_user_phrase)
            response_html = """
                <script type="text/javascript">
                    alert("匯入詞庫成功！");
                    window.location = "./user_phrase_editor.html";
                </script>
            """
            self.write(response_html)
        except:
            self.write("詞庫格式錯誤，可能檔案損毀或選到錯誤的檔案，請按上一頁返回")

class LoginHandler(BaseHandler):

    def post(self, page_name):
        token = self.get_argument("token", "")
        if token == self.settings["access_token"]:
            self.set_cookie(COOKIE_ID, token)
            if page_name != "user_phrase_editor":
                page_name = "config_tool"
            self.redirect("/{}.html".format(page_name))


class ConfigApp(tornado.web.Application):

    def __init__(self):
        # generate a new auth token using UUID
        self.access_token = uuid.uuid4().hex
        settings = {
            "access_token": self.access_token, # our custom setting
            "login_url": "/version",
            "debug": True
        }
        handlers = [
            (r"/(.*\.html)", tornado.web.StaticFileHandler, {"path": current_dir}),
            (r"/((css|images|js|fonts)/.*)", tornado.web.StaticFileHandler, {"path": current_dir}),
            (r"/(version.txt)", tornado.web.StaticFileHandler, {"path": os.path.join(current_dir, "../../../")}),
            (r"/config", ConfigHandler),  # main configuration handler
            (r"/user_phrases", UserPhraseHandler),  # user phrase editor
            (r"/user_phrase_file", UserPhraseFileHandler),  # export user phrase
            (r"/keep_alive", KeepAliveHandler),  # keep the api server alive
            (r"/login/(.*)", LoginHandler),  # authentication
        ]
        super().__init__(handlers, **settings)
        self.timeout_handler = None
        self.port = 0

    def launch_browser(self, tool_name):
        user_html = """<html>
    <form id="auth" action="http://127.0.0.1:{PORT}/login/{PAGE_NAME}" method="POST">
        <input type="hidden" name="token" value="{TOKEN}">
    </form>
    <script type="text/javascript">
        document.getElementById("auth").submit();
    </script>
    </html>""".format(PORT=self.port, PAGE_NAME=tool_name, TOKEN=self.access_token)
        # use a local html file to send access token to our service via http POST for authentication.
        os.makedirs(localdata_dir, exist_ok=True)
        filename = os.path.join(localdata_dir, "launch_{}.html".format(tool_name))
        with open(filename, "w") as f:
            f.write(user_html)
            os.startfile(filename)

    def run(self, tool_name):
        # find a port number that's available
        random.seed()
        while True:
            port = random.randint(1025, 65535)
            try:
                self.listen(port, "127.0.0.1")
                break
            except OSError:  # it's possible that the port we want to use is already in use
                continue
        self.port = port

        self.launch_browser(tool_name)

        # setup the main event loop
        loop = tornado.ioloop.IOLoop.current()
        self.timeout_handler = loop.call_later(SERVER_TIMEOUT, self.quit)
        loop.start()

    def reset_timeout(self):
        loop = tornado.ioloop.IOLoop.current()
        if self.timeout_handler:
            loop.remove_timeout(self.timeout_handler)
            self.timeout_handler = loop.call_later(SERVER_TIMEOUT, self.quit)

    def quit(self):
        # terminate the server process
        tornado.ioloop.IOLoop.current().close()
        sys.exit(0)


def main():
    app = ConfigApp()
    if len(sys.argv) >= 2 and sys.argv[1] == "user_phrase_editor":
        tool_name = "user_phrase_editor"
    else:
        tool_name = "config_tool"
    app.run(tool_name)


if __name__ == "__main__":
    main()
