#! python3
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
