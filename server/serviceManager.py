#! python3
import os
import threading
import json
import importlib

class TextServiceInfo:
    def __init__(self):
        self.moduleName = ""
        self.serviceName = ""
        self.guid = ""
        self.ctor = None

    def loadFromJson(self, jsonFile):
        # Read the moduleName(xxx.py) & serviceName(class name) from JSON
        jsonData = None
        with open(jsonFile, encoding = "UTF-8") as dataFile:
            jsonData = json.load(dataFile)
        if jsonData:
            moduleName = jsonData.get("moduleName", "")
            if moduleName:
                relpath = os.path.relpath(os.path.dirname(jsonFile)).replace(os.sep, ".")
                self.moduleName = "%s.%s" % (relpath, moduleName)
                print(self.moduleName)
            self.serviceName = jsonData.get("serviceName", "")
            self.guid = jsonData.get("guid", "").lower()

    def createInstance(self, client):
        if not self.moduleName or not self.serviceName or not self.guid:
            return None
        if not self.ctor: # constructor is not yet imported
            # import the module
            mod = importlib.import_module(self.moduleName)
            self.ctor = getattr(mod, self.serviceName)
            if not self.ctor:
                return None
        return self.ctor(client) # create a new instance for this text service


        
class TextServiceManager:
    def __init__(self):
        self.__lock = threading.Lock()
        self.services = {}
        self.enumerateServices()

    def enumerateServices(self):
        # To enumerate currently installed Input Method
        currentDir = os.path.dirname(os.path.abspath(__file__))
        input_methods_dir = os.path.join(currentDir, "input_methods")
        for subdir in os.listdir(input_methods_dir):
            filename = os.path.join(input_methods_dir, subdir, "ime.json")
            if os.path.exists(filename):
                info = TextServiceInfo()
                info.loadFromJson(filename)
                print(info.guid)
                if info.guid:
                    self.services[info.guid] = info

    def createService(self, client, guid):
        guid = guid.lower()
        if guid in self.services:
            info = self.services[guid]
            return info.createInstance(client)
        return None


textServiceMgr = TextServiceManager()
