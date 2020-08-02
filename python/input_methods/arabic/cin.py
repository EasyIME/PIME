from __future__ import print_function
from __future__ import unicode_literals

import json
import os


class Cin(object):
    # TODO check the possiblility if the encoding is not utf-8
    encoding = 'utf-8'

    def __init__(self, fs, imeDirName):
        self.imeDirName = imeDirName
        self.curdir = os.path.abspath(os.path.dirname(__file__))

        self.name = ""
        self.selkey = ""
        self.keynames = {}
        self.chardefs = {}
        self.dupchardefs = {}

        self.__dict__.update(json.load(fs))

    def __del__(self):
        del self.keynames
        del self.chardefs
        del self.dupchardefs

        self.keynames = {}
        self.chardefs = {}
        self.dupchardefs = {}

    def getName(self):
        return self.name

    def getSelection(self):
        return self.selkey

    def isInKeyName(self, key):
        return key in self.keynames

    def getKeyName(self, key):
        return self.keynames[key]

    def isHaveKey(self, val):
        return True if [key for key, value in self.chardefs.items() if val in value] else False

    def getKey(self, val):
        return [key for key, value in self.chardefs.items() if val in value][0]

    def isInCharDef(self, key):
        return key in self.chardefs

    def isCharactersInKeyName(self, characters):
        for character in characters:
            if not self.isInKeyName(character):
                return False
        return True

    # Will return a list containing all possible result
    def getCharDef(self, key):
        try:
            return self.chardefs[key]
        except:
            return []

    def haveNextCharDef(self, key):
        chardefslist = []
        for chardef in self.chardefs:
            if key == chardef[:1]:
                chardefslist.append(chardef)
                if len(chardefslist) >= 2:
                    break
        return chardefslist


__all__ = ["Cin"]
