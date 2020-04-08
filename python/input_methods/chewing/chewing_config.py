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
import time
import shutil

DEF_FONT_SIZE = 16

# from libchewing/include/internal/userphrase-private.h
DB_NAME = "chewing.sqlite3"

selKeys = (
    "1234567890",
    "asdfghjkl;",
    "asdfzxcv89",
    "asdfjkl789",
    "aoeuhtn789",
    "1234qweras"
)


class ChewingConfig:

    def __init__(self):
        self.addPhraseForward = True
        self.advanceAfterSelection = True
        self.candPerPage = 9
        self.candPerRow = 3
        self.defaultEnglish = False
        self.defaultFullSpace = False
        self.easySymbolsWithCtrl = False
        self.easySymbolsWithShift = True
        self.enableCapsLock = True
        self.enableShiftSpace = True
        self.enableSwitchTCSC = True
        self.escCleanAllBuf = True
        self.fontSize = DEF_FONT_SIZE
        self.fullShapeSymbols = True
        self.fullShapeSymbolsWithShift = True
        self.keyboardLayout = 0
        self.leftRightAction = 0
        self.outputSimpChinese = False
        self.selKeyType = 0
        self.shiftMoveCursor = 0
        self.spaceKeyAction = 1
        self.spaceKeyCandidatesAction = 0
        self.switchLangWithShift = True
        self.upDownAction = 0
        self.upperCaseWithShift = True
        self.disableOnStartup = False

        # version: last modified time of (config.json, symbols.dat, swkb.dat)
        self._version = (0.0, 0.0, 0.0)
        self._lastUpdateTime = 0.0
        self.load()  # try to load from the config file

    def getConfigDir(self):
        config_dir = os.path.join(
            os.path.expandvars("%APPDATA%"), "PIME", "chewing")
        os.makedirs(config_dir, mode=0o700, exist_ok=True)
        return config_dir

    def getConfigFile(self, name="config.json"):
        return os.path.join(self.getConfigDir(), name)

    def getUserPhrase(self):
        return os.path.join(self.getConfigDir(), DB_NAME)

    def getSelKeys(self):
        return selKeys[self.selKeyType]

    def getLastTime(self):
        return self._lastUpdateTime

    def load(self):
        filename = self.getConfigFile()
        try:
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    self.__dict__.update(json.load(f))
            else:
                filename = os.path.join(os.path.expanduser(
                    "~"), "PIME", "chewing", "config.json")
                if not os.path.exists(filename) or os.stat(filename).st_size == 0:
                    self.save()
                else:
                    src_dir = os.path.join(
                        os.path.expanduser("~"), "PIME", "chewing")
                    dst_dir = self.getConfigDir()
                    self.copytree(src_dir, dst_dir)
                    filename = self.getConfigFile()

        except Exception:
            self.save()
        self.update()

    def toJson(self):
        return {key: value for key, value in self.__dict__.items() if not key.startswith("_")}

    def save(self):
        filename = self.getConfigFile()
        try:
            with open(filename, "w") as f:
                json = self.toJson()
                js = json.dump(json, f, indent=4)
            self.update()
        except Exception:
            pass  # FIXME: handle I/O errors?

    def getDataDir(self):
        return os.path.join(os.path.dirname(__file__), "data")

    def findFile(self, dirs, name):
        for dirname in dirs:
            path = os.path.join(dirname, name)
            if os.path.exists(path):
                return path
        return None

    def copytree(self, src, dst, symlinks=False, ignore=None):
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
            configTime = os.path.getmtime(self.getConfigFile())
        except Exception:
            configTime = 0.0

        datadirs = (self.getConfigDir(), self.getDataDir())
        symbolsTime = 0.0
        symbolsFile = self.findFile(datadirs, "symbols.dat")
        if symbolsFile:
            try:
                symbolsTime = os.path.getmtime(symbolsFile)
            except Exception:
                pass

        ezSymbolsTime = 0.0
        ezSymbolsFile = self.findFile(datadirs, "swkb.dat")
        if ezSymbolsFile:
            try:
                ezSymbolsTime = os.path.getmtime(ezSymbolsFile)
            except Exception:
                pass

        lastConfigTime = self._version[0]
        self._version = (configTime, symbolsTime, ezSymbolsTime)

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
        return currentVersion[0] != self._version[0]

    # isFullReloadNeeded() checks whether you need to delete the
    # existing chewing context and create a new one.
    # This is often caused by change of data files, such as
    # symbols.dat and swkb.dat files.
    def isFullReloadNeeded(self, currentVersion):
        return currentVersion[1:] != self._version[1:]

# globally shared config object
# load configurations from a user-specific config file
chewingConfig = ChewingConfig()
