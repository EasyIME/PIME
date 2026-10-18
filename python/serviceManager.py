#! python3
# Copyright (C) 2015 - 2016 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
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

import os
import json
import importlib

class TextServiceInfo:
    def __init__(self):
        self.dirName = ""
        self.name = ""
        self.moduleName = ""
        self.serviceName = ""
        self.guid = ""
        self.textServiceClass = None
        self.modulPrefix = ""
        self.configTool = ""

    def loadFromJson(self, jsonFile):
        dirName = os.path.dirname(jsonFile)
        self.dirName = os.path.basename(dirName)
        self.modulePrefix = os.path.relpath(dirName).replace(os.sep, ".")
        # Read the moduleName(xxx.py) & serviceName(class name) from JSON
        jsonData = None
        with open(jsonFile, encoding = "UTF-8") as dataFile:
            jsonData = json.load(dataFile)
        if jsonData:
            self.name = jsonData.get("name", "")
            # text service module
            moduleName = jsonData.get("moduleName", "")
            if moduleName:
                self.moduleName = "%s.%s" % (self.modulePrefix, moduleName)
                print(self.moduleName)
            self.serviceName = jsonData.get("serviceName", "")
            self.guid = jsonData.get("guid", "").lower()
            self.configTool = jsonData.get("configTool", "")

    def createInstance(self, client):
        if not self.moduleName or not self.serviceName or not self.guid:
            return None
        if not self.textServiceClass: # constructor is not yet imported
            # import the module
            mod = importlib.import_module(self.moduleName)
            self.textServiceClass = getattr(mod, self.serviceName)
            if not self.textServiceClass:
                return None
        return self.textServiceClass(client) # create a new instance for this text service


class TextServiceManager:
    """Manages discovery, registration, and creation of PIME text services."""

    def __init__(self):
        """Initializes an empty TextServiceManager."""
        self.services = {}

    def load(self, input_methods_dir: str):
        """Loads and registers all input methods found in subdirectories of input_methods_dir."""
        for subdir in os.listdir(input_methods_dir):
            filename = os.path.join(input_methods_dir, subdir, "ime.json")
            if os.path.exists(filename):
                info = TextServiceInfo()
                info.loadFromJson(filename)
                if info.guid:
                    self.services[info.guid] = info

    def createService(self, client, guid):
        """Creates an instance of the text service associated with the specified GUID."""
        guid = guid.lower()
        if guid in self.services:
            info = self.services[guid]
            return info.createInstance(client)
        return None
