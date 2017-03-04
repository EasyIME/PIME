from __future__ import print_function
from __future__ import unicode_literals
import os
import re
import json
import copy


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
        self.cincount = {}
        self.chardefs = {}
        self.privateuse = {}

        self.__dict__.update(json.load(fs))

        if self.ignorePrivateUseArea:
            for key in self.privateuse:
                newvalue = list(self.chardefs[key])
                for value in self.privateuse[key]:
                   newvalue.remove(value) 
                self.chardefs[key] = newvalue

        self.saveCountFile()


    def __del__(self):
        del self.keynames
        del self.cincount
        del self.chardefs
        del self.privateuse

        self.keynames = {}
        self.cincount = {}
        self.chardefs = {}
        self.privateuse = {}


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


    def getCharDef(self, key):
        """ 
        will return a list conaining all possible result
        """
        return self.chardefs[key]


    def haveNextCharDef(self, key):
        chardefslist = []
        for chardef in self.chardefs:
            if key == chardef[:1]:
                chardefslist.append(chardef)
                if len(chardefslist) >= 2:
                    break
        return chardefslist


    def getWildcardCharDefs(self, CompositionChar, WildcardChar, candMaxItems):
        wildcardchardefs = []
        cjkextchardefs = {}
        matchchardefs = {}
        highFrequencyWordCount = 0
        lowFrequencyWordCount = 0

        for i in range(11):
            cjkextchardefs[i] = []

        keyLength = len(CompositionChar)

        matchstring = CompositionChar
        for char in ['\\', '.', '*', '?', '+', '[', '{', '|', '(', ')', '^', '$']:
            if char in matchstring:
                if not char == WildcardChar:
                    matchstring = matchstring.replace(char, '\\' + char)

        matchstring = matchstring.replace(WildcardChar, '(.)')
        matchchardefs = [self.chardefs[key] for key in sorted(self.chardefs.keys()) if re.match('^' + matchstring + '$', key) and len(key) == keyLength]

        if matchchardefs:
            for chardef in matchchardefs:
                for matchstr in chardef:
                    if re.match('[\u3100-\u312F]|[\u02D9]|[\u02CA]|[\u02C7]|[\u02CB]', matchstr): # Bopomofo 區域
                        if not matchstr in cjkextchardefs[0]:
                            cjkextchardefs[0].append(matchstr)
                            highFrequencyWordCount += 1
                    elif re.match('[\u4E00-\u9FD5]', matchstr): # CJK Unified Ideographs 區域
                        try:
                            big5code = matchstr.encode('big5')

                            if int(big5code.hex(), 16) in range(int('0xA440', 16), int('0xC67F', 16)): # Big5 常用字
                                if not matchstr in cjkextchardefs[1]:
                                    cjkextchardefs[1].append(matchstr)
                                    highFrequencyWordCount += 1
                            elif int(big5code.hex(), 16) in range(int('0xC940', 16), int('0xF9D6', 16)): # Big5 次常用字
                                if not matchstr in cjkextchardefs[2]:
                                    cjkextchardefs[2].append(matchstr)
                                    highFrequencyWordCount += 1
                            else: # Big5 其它漢字
                                if not matchstr in cjkextchardefs[3]:
                                    cjkextchardefs[3].append(matchstr)
                                    highFrequencyWordCount += 1
                        except: # CJK Unified Ideographs 漢字
                            if not matchstr in cjkextchardefs[4]:
                                cjkextchardefs[4].append(matchstr)
                                highFrequencyWordCount += 1
                    elif re.match('[\u3400-\u4DB5]', matchstr): # CJK Unified Ideographs Extension A 區域
                        if not matchstr in cjkextchardefs[5]:
                            cjkextchardefs[5].append(matchstr)
                            lowFrequencyWordCount += 1
                    elif ord(matchstr) in range(int('0x20000', 16), int('0x2A6DF', 16)): # CJK Unified Ideographs Extension B 區域
                        if not matchstr in cjkextchardefs[6]:
                            cjkextchardefs[6].append(matchstr)
                            lowFrequencyWordCount += 1
                    elif ord(matchstr) in range(int('0x2A700', 16), int('0x2B73F', 16)): # CJK Unified Ideographs Extension C 區域
                        if not matchstr in cjkextchardefs[7]:
                            cjkextchardefs[7].append(matchstr)
                            lowFrequencyWordCount += 1
                    elif ord(matchstr) in range(int('0x2B740', 16), int('0x2B81F', 16)): # CJK Unified Ideographs Extension D 區域
                        if not matchstr in cjkextchardefs[8]:
                            cjkextchardefs[8].append(matchstr)
                            lowFrequencyWordCount += 1
                    elif ord(matchstr) in range(int('0x2B820', 16), int('0x2CEAF', 16)): # CJK Unified Ideographs Extension E 區域
                        if not matchstr in cjkextchardefs[9]:
                            cjkextchardefs[9].append(matchstr)
                            lowFrequencyWordCount += 1
                    else: # 不在 CJK Unified Ideographs 區域
                        if not matchstr in cjkextchardefs[10]:
                            cjkextchardefs[10].append(matchstr)
                            lowFrequencyWordCount += 1

                    if highFrequencyWordCount + lowFrequencyWordCount >= candMaxItems:
                        for key in cjkextchardefs:
                            for char in cjkextchardefs[key]:
                                if not char in wildcardchardefs:
                                    wildcardchardefs.append(char)
                                if len(wildcardchardefs) >= candMaxItems:
                                    return wildcardchardefs

            for key in cjkextchardefs:
                for char in cjkextchardefs[key]:
                    if not char in wildcardchardefs:
                        wildcardchardefs.append(char)
                    if len(wildcardchardefs) >= candMaxItems:
                        return wildcardchardefs
        return wildcardchardefs


    def getCharEncode(self, root):
        nunbers = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩']
        i = 0
        result = root + ':'
        for chardef in self.chardefs:
            for char in self.chardefs[chardef]:
                if char == root:
                    result += '　' + nunbers[i]
                    if i < 9:
                        i = i + 1
                    for str in chardef:
                        result += self.getKeyName(str)

        if result == root + ':':
            result = '查無字根...'
        return result


    def updateCinTable(self, userExtendTable, priorityExtendTable, extendtable, ignorePrivateUseArea):
        if userExtendTable:
            for key in extendtable.chardefs:
                for root in extendtable.chardefs[key]:
                    if priorityExtendTable:
                        i = extendtable.chardefs[key].index(root)
                        try:
                            self.chardefs[key.lower()].insert(i, root)
                        except KeyError:
                            self.chardefs[key.lower()] = [root]
                    else:
                        try:
                            self.chardefs[key.lower()].append(root)
                        except KeyError:
                            self.chardefs[key.lower()] = [root]


    def saveCountFile(self):
        filename = self.getCountFile()
        tempcincount = {}

        if os.path.exists(filename) and not os.stat(filename).st_size == 0:
            with open(filename, "r") as f:
                tempcincount.update(json.load(f))

        if not tempcincount == self.cincount:
            try:
                with open(filename, "w") as f:
                    js = json.dump(self.cincount, f, sort_keys=True, indent=4)
            except Exception:
                pass # FIXME: handle I/O errors?


    def getCountDir(self):
        count_dir = os.path.join(os.path.expandvars("%APPDATA%"), "PIME", self.imeDirName)
        os.makedirs(count_dir, mode=0o700, exist_ok=True)
        return count_dir


    def getCountFile(self, name="cincount.json"):
        return os.path.join(self.getCountDir(), name)


__all__ = ["Cin"]
