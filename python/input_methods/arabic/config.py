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

import json
import os
import shutil
import time

DEF_FONT_SIZE = 12

selKeys = (
    "1234567890"
)


class CinBaseConfig:

    def __init__(self):
        self.candPerRow = 1
        self.defaultLatin = False
        self.messageDurationTime = 3
        self.fontSize = DEF_FONT_SIZE
        self.candPerPage = 9
        self.cursorCandList = True
        self.messageDurationTime = 3

        self.ignoreSaveList = ["ignoreSaveList", "curdir", "cinFile", "selCinFile", "imeDirName", "_version", "_lastUpdateTime"]
        self.curdir = os.path.abspath(os.path.dirname(__file__))
        self.cinFile = ""
        self.selCinFile = ""
        self.imeDirName = ""

        # version: last modified time of (config.json, symbols.dat)
        self._version = 0.0
        self._lastUpdateTime = 0.0

    def load(self):
        filename = os.path.join(self.getDefaultConfigDir(), "config.json")
        with open(filename, "r") as f:
            self.__dict__.update(json.load(f))
        self.update()

    def getJsonDir(self):
        return os.path.join(os.path.dirname(__file__), "json")

    def getDefaultConfigDir(self):
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "config"))

    def findFile(self, dirs, name):
        for dirname in dirs:
            path = os.path.join(dirname, name)
            if os.path.exists(path):
                return path
        return None

    def copytree(slef, src, dst, symlinks=False, ignore=None):
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, symlinks, ignore)
            else:
                shutil.copy2(s, d)

    # check if the config files are changed and relaod as needed
    def update(self):
        # avoid checking mtime of files too frequently
        if (time.time() - self._lastUpdateTime) < 3.0:
            return

        try:
            configTime = os.path.getmtime(self.getDefaultConfigDir())
        except Exception:
            configTime = 0.0

        lastConfigTime = self._version
        self._version = configTime

        # the main config file is changed, reload it
        if lastConfigTime != configTime:
            if not hasattr(self, "_in_update"):  # avoid recursion
                self._in_update = True  # avoid recursion since update() will be called by load
                self.load()
                del self._in_update

        self._lastUpdateTime = time.time()

    def getVersion(self):
        return self._version

    def isConfigChanged(self, currentVersion):
        return currentVersion != self._version


# globally shared config object
# load configurations from a user-specific config file
CinBaseConfig = CinBaseConfig()
