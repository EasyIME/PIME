#! python3
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
