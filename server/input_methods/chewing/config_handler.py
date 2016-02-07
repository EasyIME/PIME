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
from .chewing_config import chewingConfig

class ConfigHandler(tornado.web.RequestHandler):
    def get(self):
        # we only allow requests from localhost
        if self.request.remote_ip not in ("::1", "127.0.0.1"):
            return
        self.render("config.html", cfg=chewingConfig)

    def post(self):
        # we only allow requests from localhost
        if self.request.remote_ip not in ("::1", "127.0.0.1"):
            return
        # TODO: save configurations
        # TODO: ask existing instances of text services to apply the new config values.
        self.write("Confuguration saved!")
