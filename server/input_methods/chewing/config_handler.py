#! python3
import tornado
import tornado.web
from .chewing_config import chewingConfig

class ConfigHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("config.html", cfg=chewingConfig)

    def post(self):
        self.write("Confuguration saved!")
