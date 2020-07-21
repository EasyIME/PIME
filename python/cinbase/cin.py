from __future__ import print_function
from __future__ import unicode_literals

import json
import os


class Cin(object):
    # TODO check the possiblility if the encoding is not utf-8
    encoding = 'utf-8'

    def __init__(self, fs, imeDirName, ignorePrivateUseArea):
        self.imeDirName = imeDirName
        self.ignorePrivateUseArea = ignorePrivateUseArea
        self.curdir = os.path.abspath(os.path.dirname(__file__))

        self.ename = ""
        self.cname = ""
        self.selkey = ""
        self.keynames = {}
        self.chardefs = {}
        self.privateuse = {}
        self.dupchardefs = {}

        self.__dict__.update(json.load(fs))

        if self.ignorePrivateUseArea:
            for key in self.privateuse:
                newvalue = list(self.chardefs[key])
                for value in self.privateuse[key]:
                    if value in newvalue:
                        newvalue.remove(value)
                self.chardefs[key] = newvalue

    def __del__(self):
        del self.keynames
        del self.chardefs
        del self.privateuse
        del self.dupchardefs

        self.keynames = {}
        self.chardefs = {}
        self.privateuse = {}
        self.dupchardefs = {}

    def getEname(self):
        return self.ename

    def getCname(self):
        return self.cname

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

    def getCharDef(self, key):
        """
        will return a list containing all possible result
        """
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

    def updateCinTable(self, userExtendTable, priorityExtendTable, extendtable):
        if userExtendTable:
            for key in extendtable.chardefs:
                for root in extendtable.chardefs[key]:
                    if priorityExtendTable:
                        i = extendtable.chardefs[key].index(root)
                        try:
                            self.chardefs[key].insert(i, root)
                        except KeyError:
                            self.chardefs[key] = [root]
                    else:
                        try:
                            self.chardefs[key].append(root)
                        except KeyError:
                            self.chardefs[key] = [root]

__all__ = ["Cin"]
