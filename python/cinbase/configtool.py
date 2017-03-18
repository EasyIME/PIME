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
import io
import os
import uuid  # use to generate a random auth token
import random
import json
import threading

from config import CinBaseConfig
from cin import Cin
from ctypes import c_uint, byref, create_string_buffer

cfg = CinBaseConfig
cfg.imeDirName = sys.argv[2]
config_dir = os.path.join(cfg.getConfigDir())
current_dir = os.path.abspath(os.path.dirname(__file__))
current_ime_dir = os.path.join(cfg.getDefaultConfigDir(), os.path.pardir)
current_ime_config_dir = os.path.join(cfg.getDefaultConfigDir())
data_dir = os.path.join(current_dir, "data")
json_dir = os.path.join(current_dir, "json")
localdata_dir = os.path.join(cfg.getConfigDir())

if len(sys.argv) >= 2 and sys.argv[1] == "user_phrase_editor":
    tool_name = "user_phrase_editor"
else:
    tool_name = "config"

COOKIE_ID = "cinbase_config_token"
SERVER_TIMEOUT = 120


# syspath 參數可包含多個路徑，用 ; 分隔
# 此處把 user 設定檔目錄插入到 system-wide 資料檔路徑前
# 如此使用者變更設定後，可以比系統預設值有優先權
search_paths = ";".join((cfg.getConfigDir(), data_dir)).encode("UTF-8")

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
            "imename": cfg.imeDirName,
            "config": self.load_config(),
            "cincount": self.load_cindata(),
            "symbols": self.load_data("symbols.dat"),
            "swkb": self.load_data("swkb.dat"),
            "fsymbols": self.load_data("fsymbols.dat"),
            "phrase": self.load_data("userphrase.dat"),
            "flangs": self.load_data("flangs.dat"),
            "extendtable": self.load_data("extendtable.dat")
        }
        self.write(data)

    @tornado.web.authenticated
    def post(self):  # save config
        data = tornado.escape.json_decode(self.request.body)
        # print(data)
        # ensure the config dir exists
        os.makedirs(config_dir, exist_ok=True)
        # write the config to files
        config = data.get("config", None)
        if config:
            self.save_file("config.json", json.dumps(config, sort_keys=True, indent=4))

        symbols = data.get("symbols", None)
        if symbols:
            self.save_file("symbols.dat", symbols)

        swkb = data.get("swkb", None)
        if swkb:
            self.save_file("swkb.dat", swkb)
        self.write('{"return":true}')

        fsymbols = data.get("fsymbols", None)
        if fsymbols:
            self.save_file("fsymbols.dat", fsymbols)
        self.write('{"return":true}')

        phrase = data.get("phrase", None)
        if phrase:
            self.save_file("userphrase.dat", phrase)
        self.write('{"return":true}')

        flangs = data.get("flangs", None)
        if flangs:
            self.save_file("flangs.dat", flangs)
        self.write('{"return":true}')

        extendtable = data.get("extendtable", None)
        if extendtable:
            self.save_file("extendtable.dat", extendtable)
        self.write('{"return":true}')

    def load_config(self):
        cfg.load()
        config = cfg.toJson()  # the current settings
        return config

    def load_cindata(self):
        cfg.load()
        CinDict ={}
        CinDict["checj"] = ["checj.json", "mscj3.json", "mscj3-ext.json", "cj-ext.json", "cnscj.json", "thcj.json", "newcj3.json", "cj5.json", "newcj.json", "scj6.json"]
        CinDict["chephonetic"] = ["thphonetic.json", "CnsPhonetic.json", "bpmf.json"]
        CinDict["chearray"] = ["tharray.json", "array30.json", "ar30-big.json", "array40.json"]
        CinDict["chedayi"] = ["thdayi.json", "dayi4.json", "dayi3.json"]
        CinDict["cheez"] = ["ez.json", "ezsmall.json", "ezmid.json", "ezbig.json"]
        CinDict["chepinyin"] = ["thpinyin.json", "pinyin.json", "roman.json"]
        CinDict["chesimplex"] = ["simplecj.json", "simplex.json", "simplex5.json"]
        CinDict["cheliu"] = ["liu.json"]
        jsonFile = CinDict[cfg.imeDirName][cfg.selCinType]

        datafile = os.path.join(json_dir, jsonFile)
        if os.path.exists(datafile):
            try:
                with open(datafile, "r", encoding="UTF-8") as f:
                    jsondata = json.load(f)
                    return jsondata['cincount']
            except Exception as e:
                print(e)

    def load_data(self, name):
        try:
            userFile = os.path.join(config_dir, name)
            with open(userFile, "r", encoding="UTF-8") as f:
                return f.read()
        except FileNotFoundError:
            with open(os.path.join(data_dir, name), "r", encoding="UTF-8") as f:
                return f.read()
        except Exception:
            return ""

    def save_file(self, filename, data):
        try:
            with open(os.path.join(config_dir, filename), "w", encoding="UTF-8") as f:
                f.write(data)
        except Exception:
            pass



class LoginHandler(BaseHandler):

    def post(self, page_name):
        token = self.get_argument("token", "")
        if token == self.settings["access_token"]:
            self.set_cookie(COOKIE_ID, token)
            if page_name != "user_phrase_editor":
                page_name = "config"
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
            (r"/(.*\.html|config.js)", tornado.web.StaticFileHandler, {"path": current_ime_config_dir}),
            (r"/(.*\.htm)", tornado.web.StaticFileHandler, {"path": os.path.join(current_dir, "config")}),
            (r"/((css|fonts|images|js)/.*)", tornado.web.StaticFileHandler, {"path": os.path.join(current_dir, "config")}),
            (r"/(icon.ico)", tornado.web.StaticFileHandler, {"path": current_ime_dir}),
            (r"/(version.txt)", tornado.web.StaticFileHandler, {"path": os.path.join(current_dir, "../../")}),
            (r"/config", ConfigHandler),  # main configuration handler
            (r"/keep_alive", KeepAliveHandler),  # keep the api server alive
            (r"/login/(.*)", LoginHandler)  # authentication
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
        filename = os.path.join(localdata_dir, "launch_{}.html".format(tool_name))
        if os.path.exists(filename):
            os.remove(filename)
        sys.exit(0)


def main():
    app = ConfigApp()
    app.run(tool_name)


if __name__ == "__main__":
    main()
