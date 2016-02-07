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

DEF_FONT_SIZE = 16

# from libchewing/include/internal/userphrase-private.h
DB_NAME	= "chewing.sqlite3"

selKeys=(
    "1234567890",
    "asdfghjkl;",
    "asdfzxcv89",
    "asdfjkl789",
    "aoeuhtn789",
    "1234qweras"
)

class ChewingConfig:

    def __init__(self):
        self.keyboardLayout = 0
        self.candPerRow = 3
        self.defaultEnglish = False
        self.defaultFullSpace = False
        self.showCandWithSpaceKey = False
        self.switchLangWithShift = True
        self.outputSimpChinese = False
        self.addPhraseForward = True
        self.colorCandWnd = True
        self.advanceAfterSelection = True
        self.fontSize = DEF_FONT_SIZE
        self.selKeyType = 0
        self.candPerPage = 9
        self.cursorCandList = 1
        self.enableCapsLock = 1
        self.fullShapeSymbols = 1
        self.phraseMark = 1
        self.escCleanAllBuf = 0
        self.easySymbolsWithShift = 1
        self.easySymbolsWithCtrl = 0
        self.upperCaseWithShift = 0

        self.load() # try to load from the config file

    def getConfigDir(self):
        config_dir = os.path.join(os.path.expanduser("~"), "PIME", "chewing")
        os.makedirs(config_dir, mode=0o700, exist_ok=True)
        return config_dir

    def getConfigFile(self):
        return os.path.join(self.getConfigDir(), "config.json")

    def getUserPhrase(self):
        return os.path.join(self.getConfigDir(), DB_NAME)
        
    def getSelKeys(self):
        return selKeys[self.selKeyType]

    def load(self):
        try:
            if os.path.exists(self.getConfigFile()):
                with open(self.getConfigFile(), "r") as f:
                    self.__dict__.update(json.load(f))
            else:
                self.save();
        except Exception:
            pass # FIXME: handle I/O errors?

    def save(self):
        try:
            with open(self.getConfigFile(), "w") as f:
                js = json.dump(self.__dict__, f, indent=4)
        except Exception:
            pass # FIXME: handle I/O errors?


# globally shared config object
# load configurations from a user-specific config file
# FIXME: should we share this among all ChewingTextService instances?
# FIXME: how to reload the configurations properly when they are changed?
chewingConfig = ChewingConfig()
