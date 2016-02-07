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

import tornado
import tornado.web
from serviceManager import textServiceMgr


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        # we only allow requests from localhost
        if self.request.remote_ip not in ("::1", "127.0.0.1"):
            return
        # FIXME: this is extremely ugly...
        self.write("PIME configurations<hr/>")
        for guid, info in textServiceMgr.services.items():
            self.write('<a href="%s/">%s</a><br/>' % (info.dirName, info.name))


# local web server used as configuration UI
class ConfigWebServer:
    def __init__(self):
        handlers = [(r"/", MainHandler)]
        for guid, info in textServiceMgr.services.items():
            if info.configHandlerClass:
                handlers.append((r"/%s/?.*" % info.dirName, info.configHandlerClass))
        self.app = tornado.web.Application(handlers)

    def run(self):
        # FIXME: We should only allow incoming connections from localhost.
        # Otherwise, this will becomes a security hole.
        self.app.listen(5043)  # ASCII 0x5043 stands for "PC"
        tornado.ioloop.IOLoop.current().start()
