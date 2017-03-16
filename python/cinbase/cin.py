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
        self.dupchardefs = {}

        self.charsetRange = {}
        self.charsetRange['bopomofo'] = [int('0x3100', 16), int('0x3130', 16)]
        self.charsetRange['bopomofoTone'] = [int('0x02D9', 16), int('0x02CA', 16), int('0x02C7', 16), int('0x02CB', 16)]
        self.charsetRange['cjk'] = [int('0x4E00', 16), int('0x9FD6', 16)]
        self.charsetRange['big5F'] = [int('0xA440', 16), int('0xC67F', 16)]
        self.charsetRange['big5LF'] = [int('0xC940', 16), int('0xF9D6', 16)]
        self.charsetRange['big5S'] = [int('0xA140', 16), int('0xA3C0', 16)]
        self.charsetRange['cjkExtA'] = [int('0x3400', 16), int('0x4DB6', 16)]
        self.charsetRange['cjkExtB'] = [int('0x20000', 16), int('0x2A6DF', 16)]
        self.charsetRange['cjkExtC'] = [int('0x2A700', 16), int('0x2B73F', 16)]
        self.charsetRange['cjkExtD'] = [int('0x2B740', 16), int('0x2B81F', 16)]
        self.charsetRange['cjkExtE'] = [int('0x2B820', 16), int('0x2CEAF', 16)]
        self.charsetRange['pua'] = [int('0xE000', 16), int('0xF900', 16)]
        self.charsetRange['puaA'] = [int('0xF0000', 16), int('0xFFFFE', 16)]
        self.charsetRange['puaB'] = [int('0x100000', 16), int('0x10FFFE', 16)]
        self.charsetRange['cjkCIS'] = [int('0x2F800', 16), int('0x2FA20', 16)]

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
        del self.dupchardefs

        self.keynames = {}
        self.cincount = {}
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
        matchchardefs = {}
        lowFrequencyChardefs = {}
        highFrequencyCharSetList = ["bopomofo", "bopomofoTone", "cjk", "big5F", "big5LF", "big5S"]
        lowFrequencyCharSetList = ["cjkExtA", "cjkExtB", "cjkExtC", "cjkExtD", "cjkExtE", "pua", "cjkOther"]

        highFrequencyWordCount = 0
        lowFrequencyWordCount = 0

        for i in range(7):
            lowFrequencyChardefs[i] = []

        keyLength = len(CompositionChar)

        matchstring = CompositionChar
        for char in ['\\', '.', '*', '?', '+', '[', '{', '|', '(', ')', '^', '$']:
            if char in matchstring:
                if not char == WildcardChar:
                    matchstring = matchstring.replace(char, '\\' + char)

        matchstring = matchstring.replace(WildcardChar, '(.)')
        sortedchardefs = sorted(self.chardefs.keys())
        matchchardefs = [self.chardefs[key] for key in sortedchardefs if re.match('^' + matchstring + '$', key) and len(key) == keyLength]

        if matchchardefs:
            for chardef in matchchardefs:
                for matchstr in chardef:
                    charSet = self.getCharSet(matchstr)
                    if charSet in highFrequencyCharSetList:
                        wildcardchardefs.append(matchstr)
                        highFrequencyWordCount += 1
                    else:
                        i = lowFrequencyCharSetList.index(charSet)
                        if not matchstr in lowFrequencyChardefs[i]:
                            lowFrequencyChardefs[i].append(matchstr)
                            lowFrequencyWordCount += 1

            for key in lowFrequencyChardefs:
                for char in lowFrequencyChardefs[key]:
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


    def getCharSet(self, root):
        matchstr = root
        matchint = ord(matchstr)

        if matchint <= self.charsetRange['cjk'][1]:
            if (matchint in range(self.charsetRange['bopomofo'][0], self.charsetRange['bopomofo'][1]) or # Bopomofo 區域
                matchint in self.charsetRange['bopomofoTone']): 
                return "bopomofo"
            elif matchint in range(self.charsetRange['cjk'][0], self.charsetRange['cjk'][1]): # CJK Unified Ideographs 區域
                try:
                    big5code = matchstr.encode('big5')
                    big5codeint = int(big5code.hex(), 16)

                    if big5codeint in range(self.charsetRange['big5F'][0], self.charsetRange['big5F'][1]): # Big5 常用字
                        return "big5F"
                    elif big5codeint in range(self.charsetRange['big5LF'][0], self.charsetRange['big5LF'][1]): # Big5 次常用字
                        return "big5LF"
                    elif big5codeint in range(self.charsetRange['big5S'][0], self.charsetRange['big5S'][1]): # Big5 符號
                        return "big5LF"
                    else: # Big5 其它漢字
                        return "big5Other"
                except: # CJK Unified Ideographs 漢字
                    return "cjk"
            elif matchint in range(self.charsetRange['cjkExtA'][0], self.charsetRange['cjkExtA'][1]): # CJK Unified Ideographs Extension A 區域
                return "cjkExtA"
        else:
            if matchint in range(self.charsetRange['cjkExtB'][0], self.charsetRange['cjkExtB'][1]): # CJK Unified Ideographs Extension B 區域
                return "cjkExtB"
            elif matchint in range(self.charsetRange['cjkExtC'][0], self.charsetRange['cjkExtC'][1]): # CJK Unified Ideographs Extension C 區域
                return "cjkExtC"
            elif matchint in range(self.charsetRange['cjkExtD'][0], self.charsetRange['cjkExtD'][1]): # CJK Unified Ideographs Extension D 區域
                return "cjkExtD"
            elif matchint in range(self.charsetRange['cjkExtE'][0], self.charsetRange['cjkExtE'][1]): # CJK Unified Ideographs Extension E 區域
                return "cjkExtE"
            elif (matchint in range(self.charsetRange['pua'][0], self.charsetRange['pua'][1]) or # Unicode Private Use 區域
                matchint in range(self.charsetRange['puaA'][0], self.charsetRange['puaA'][1]) or
                matchint in range(self.charsetRange['puaB'][0], self.charsetRange['puaB'][1])):
                return "pua"
            elif matchint in range(self.charsetRange['cjkCIS'][0], self.charsetRange['cjkCIS'][1]): # cjk compatibility ideographs supplement 區域
                return "pua"
        # 不在 CJK Unified Ideographs 區域
        return "cjkOther"


__all__ = ["Cin"]
