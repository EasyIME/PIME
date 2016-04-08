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
import io
import time
from .cin import Cin

DEF_FONT_SIZE = 16

# from libchewing/include/internal/userphrase-private.h
DB_NAME	= "checj.sqlite3"

selKeys=(
    "1234567890"
)

class ChecjConfig:

    def __init__(self):
        self.candPerRow = 3
        self.defaultEnglish = False
        self.defaultFullSpace = False
        self.switchLangWithShift = True
        self.outputSimpChinese = False
        self.addPhraseForward = True
        self.colorCandWnd = True
        self.advanceAfterSelection = True
        self.fontSize = DEF_FONT_SIZE
        self.selCinType = 0
        self.selCinFile = "cin/checj.cin"
        self.selKeyType = 0
        self.candPerPage = 9
        self.cursorCandList = True
        self.enableCapsLock = True
        self.fullShapeSymbols = True
        # self.phraseMark = True
        self.escCleanAllBuf = True
        self.easySymbolsWithShift = True
        # self.easySymbolsWithCtrl = False
        self.upperCaseWithShift = True
        self.supportSymbolCoding = False
        self.supportWildcard = True
        self.selWildcardType = 0
        self.candMaxItems = 500
        self.curdir = os.path.abspath(os.path.dirname(__file__))
        
        # version: last modified time of (config.json, symbols.dat, swkb.dat)
        self._version = (0.0, 0.0, 0.0)
        self._lastUpdateTime = 0.0
        self.load() # try to load from the config file
        self.loadCinFile()

    def getConfigDir(self):
        config_dir = os.path.join(os.path.expanduser("~"), "PIME", "checj")
        os.makedirs(config_dir, mode=0o700, exist_ok=True)
        return config_dir

    def getConfigFile(self, name="config.json"):
        return os.path.join(self.getConfigDir(), name)

    def getUserPhrase(self):
        return os.path.join(self.getConfigDir(), DB_NAME)

    def getSelKeys(self):
        return selKeys[self.selKeyType]

    def getLastTime(self):
        return self._lastTime

    def load(self):
        filename = self.getConfigFile()
        try:
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    self.__dict__.update(json.load(f))
            else:
                self.save()
        except Exception:
            self.save()
        self.update()

    def save(self):
        filename = self.getConfigFile()
        try:
            with open(filename, "w") as f:
                json = {key: value for key, value in self.__dict__.items() if not key.startswith("_")}
                js = json.dump(json, f, indent=4)
            self.update()
        except Exception:
            pass # FIXME: handle I/O errors?

    def getDataDir(self):
        return os.path.join(os.path.dirname(__file__), "data")

    def findFile(self, dirs, name):
        for dirname in dirs:
            path = os.path.join(dirname, name)
            if os.path.exists(path):
                return path
        return None

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
                
        fsymbolsTime = 0.0
        fsymbolsFile = self.findFile(datadirs, "fsymbols.dat")
        if fsymbolsFile:
            try:
                fsymbolsTime = os.path.getmtime(fsymbolsFile)
            except Exception:
                pass
                
        flangsTime = 0.0
        flangsFile = self.findFile(datadirs, "flangs.dat")
        if flangsFile:
            try:
                flangsTime = os.path.getmtime(flangsFile)
            except Exception:
                pass

        lastConfigTime = self._version[0]
        self._version = (configTime, symbolsTime, ezSymbolsTime, fsymbolsTime, flangsTime)

        # the main config file is changed, reload it
        if lastConfigTime != configTime:
            if not hasattr(self, "_in_update"): # avoid recursion
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

    def loadCinFile(self):
        if self.selCinType == 0: 
            self.selCinFile = "cin/checj.cin"
        elif self.selCinType == 1: 
            self.selCinFile = "cin/mscj3.cin"
        elif self.selCinType == 2: 
            self.selCinFile = "cin/cj-ext.cin"
        elif self.selCinType == 3: 
            self.selCinFile = "cin/cnscj.cin"
        elif self.selCinType == 4: 
            self.selCinFile = "cin/thcj.cin"
        elif self.selCinType == 5: 
            self.selCinFile = "cin/newcj3.cin"
        elif self.selCinType == 6: 
            self.selCinFile = "cin/cj5.cin"

        CinPath = os.path.join(self.curdir, self.selCinFile)
        with io.open(CinPath, encoding='utf-8') as fs:
            self.cin = Cin(fs)

# globally shared config object
# load configurations from a user-specific config file
ChecjConfig = ChecjConfig()
