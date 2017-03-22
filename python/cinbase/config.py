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
import shutil

DEF_FONT_SIZE = 12

selKeys=(
    "1234567890"
)

class CinBaseConfig:

    def __init__(self):
        self.candPerRow = 3
        self.defaultEnglish = False
        self.defaultFullSpace = False
        self.switchLangWithShift = True
        self.outputSmallLetterWithShift = False
        self.switchPageWithSpace = False
        self.outputSimpChinese = False
        self.messageDurationTime = 3
        self.hidePromptMessages = True
        self.autoClearCompositionChar = False
        self.playSoundWhenNonCand = False
        self.directShowCand = False
        self.directCommitSymbol = False
        self.fontSize = DEF_FONT_SIZE
        self.selCinType = 0
        self.ignorePrivateUseArea = True
        self.selKeyType = 0
        self.candPerPage = 9
        self.cursorCandList = True
        self.fullShapeSymbols = False
        self.directOutFSymbols = False
        self.directOutMSymbols = True
        self.easySymbolsWithShift = False
        self.showPhrase = False
        self.sortByPhrase = True
        self.supportWildcard = True
        self.compositionBufferMode = False
        self.autoMoveCursorInBrackets = False
        self.selWildcardType = 0
        self.imeReverseLookup = False
        self.homophoneQuery = False
        self.selHCinType = 0
        self.userExtendTable = False
        self.reLoadTable = False
        self.priorityExtendTable = False
        self.selRCinType = 0
        self.rcinFileList = []
        self.candMaxItems = 100
        self.messageDurationTime = 3
        self.keyboardType = 0
        self.selDayiSymbolCharType = 0

        self.ignoreSaveList = ["ignoreSaveList", "curdir", "cinFileList", "selCinFile", "imeDirName", "_version", "_lastUpdateTime"]
        self.curdir = os.path.abspath(os.path.dirname(__file__))
        self.cinFileList = []
        self.selCinFile = ""
        self.imeDirName = ""

        # version: last modified time of (config.json, symbols.dat, swkb.dat, fsymbols.dat, flangs.dat, userphrase.dat)
        self._version = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        self._lastUpdateTime = 0.0

    def getConfigDir(self):
        config_dir = os.path.join(os.path.expandvars("%APPDATA%"), "PIME", self.imeDirName)
        os.makedirs(config_dir, mode=0o700, exist_ok=True)
        return config_dir

    def getConfigFile(self, name="config.json"):
        return os.path.join(self.getConfigDir(), name)

    def getSelKeys(self):
        return selKeys[self.selKeyType]

    def getLastTime(self):
        return self._lastTime

    def load(self):
        filename = self.getConfigFile()
        try:
            if not os.path.exists(filename) or os.stat(filename).st_size == 0:
                filename = os.path.join(os.path.expanduser("~"), "PIME", self.imeDirName, "config.json")

                if not os.path.exists(filename) or os.stat(filename).st_size == 0:
                    filename = os.path.join(self.getDefaultConfigDir(), "config.json")
                else:
                    src_dir = os.path.join(os.path.expanduser("~"), "PIME", self.imeDirName)
                    dst_dir = self.getConfigDir()
                    self.copytree(src_dir, dst_dir)
                    filename = self.getConfigFile()

            with open(filename, "r") as f:
                self.__dict__.update(json.load(f))
        except Exception:
            self.save()
        self.update()

    def toJson(self):
        return {key: value for key, value in self.__dict__.items() if not key.startswith("_") and not key in self.ignoreSaveList}

    def save(self):
        filename = self.getConfigFile()
        try:
            with open(filename, "w") as f:
                jsondata = {key: value for key, value in self.__dict__.items() if not key in self.ignoreSaveList}
                js = json.dump(jsondata, f, sort_keys=True, indent=4)
            self.update()
        except Exception:
            pass # FIXME: handle I/O errors?

    def getDataDir(self):
        return os.path.join(os.path.dirname(__file__), "data")

    def getCinDir(self):
        return os.path.join(os.path.dirname(__file__), "cin")

    def getJsonDir(self):
        return os.path.join(os.path.dirname(__file__), "json")

    def getDefaultConfigDir(self):
        return os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, "input_methods", self.imeDirName, "config"))

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

        userphraseTime = 0.0
        userphraseFile = self.findFile(datadirs, "userphrase.dat")
        if userphraseFile:
            try:
                userphraseTime = os.path.getmtime(userphraseFile)
            except Exception:
                pass

        extendtableTime = 0.0
        extendtableFile = self.findFile(datadirs, "extendtable.dat")
        if extendtableFile:
            try:
                extendtableTime = os.path.getmtime(extendtableFile)
            except Exception:
                pass

        lastConfigTime = self._version[0]
        self._version = (configTime, symbolsTime, ezSymbolsTime, fsymbolsTime, flangsTime, userphraseTime)

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


# globally shared config object
# load configurations from a user-specific config file
CinBaseConfig = CinBaseConfig()
