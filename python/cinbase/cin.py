from __future__ import print_function
from __future__ import unicode_literals
import os
import re
import json
import copy

CIN_HEAD = "%gen_inp"
ENAME_HEAD = "%ename"
CNAME_HEAD = "%cname"
ENCODING_HEAD = "%encoding"
SELKEY_HEAD = "%selkey"
KEYNAME_HEAD = "%keyname"
CHARDEF_HEAD = "%chardef"

PARSING_HEAD_STATE = 0
PARSE_KEYNAME_STATE = 1
PARSE_CHARDEF_STATE = 2

HEADS = [
    CIN_HEAD,
    ENAME_HEAD,
    CNAME_HEAD,
    ENCODING_HEAD,
    SELKEY_HEAD,
    KEYNAME_HEAD,
    CHARDEF_HEAD,
]


class Cin(object):

    # TODO check the possiblility if the encoding is not utf-8
    encoding = 'utf-8'

    def __init__(self, fs, imeDirName, sortByCharset, ignorePrivateUseArea):

        state = PARSING_HEAD_STATE

        self.imeDirName = imeDirName
        self.sortByCharset = sortByCharset
        self.ignorePrivateUseArea = ignorePrivateUseArea
        self.ename = ""
        self.cname = ""
        self.selkey = ""
        self.keynames = {}
        self.chardefs = {}
        self.srcchardefs = {}
        self.bopomofochardefs = {}
        self.big5Fchardefs = {}
        self.big5LFchardefs = {}
        self.big5Otherchardefs = {}
        self.cjkchardefs = {}
        self.cjkExtAchardefs = {}
        self.cjkExtBchardefs = {}
        self.cjkExtCchardefs = {}
        self.cjkExtDchardefs = {}
        self.cjkExtEchardefs = {}
        self.cjkOtherchardefs = {}
        self.privateusechardefs = {}
        self.cincount = {}
        self.cincount['bopomofochardefs'] = 0
        self.cincount['big5Fchardefs'] = 0
        self.cincount['big5LFchardefs'] = 0
        self.cincount['big5Otherchardefs'] = 0
        self.cincount['cjkchardefs'] = 0
        self.cincount['cjkExtAchardefs'] = 0
        self.cincount['cjkExtBchardefs'] = 0
        self.cincount['cjkExtCchardefs'] = 0
        self.cincount['cjkExtDchardefs'] = 0
        self.cincount['cjkExtEchardefs'] = 0
        self.cincount['cjkOtherchardefs'] = 0
        self.cincount['cjkTotalchardefs'] = 0
        self.cincount['privateusechardefs'] = 0

        self.charsetRange = {}
        self.charsetRange['bopomofo'] = [int('0x3100', 16), int('0x3130', 16)]
        self.charsetRange['bopomofoTone'] = [int('0x02D9', 16), int('0x02CA', 16), int('0x02C7', 16), int('0x02CB', 16)]
        self.charsetRange['cjk'] = [int('0x4E00', 16), int('0x9FD6', 16)]
        self.charsetRange['big5F'] = [int('0xA440', 16), int('0xC67F', 16)]
        self.charsetRange['big5LF'] = [int('0xC940', 16), int('0xF9D6', 16)]
        self.charsetRange['cjkExtA'] = [int('0x3400', 16), int('0x4DB6', 16)]
        self.charsetRange['cjkExtB'] = [int('0x20000', 16), int('0x2A6DF', 16)]
        self.charsetRange['cjkExtC'] = [int('0x2A700', 16), int('0x2B73F', 16)]
        self.charsetRange['cjkExtD'] = [int('0x2B740', 16), int('0x2B81F', 16)]
        self.charsetRange['cjkExtE'] = [int('0x2B820', 16), int('0x2CEAF', 16)]
        self.charsetRange['pua'] = [int('0xE000', 16), int('0xF900', 16)]
        self.charsetRange['puaA'] = [int('0xF0000', 16), int('0xFFFFE', 16)]
        self.charsetRange['puaB'] = [int('0x100000', 16), int('0x10FFFE', 16)]
        self.charsetRange['cjkS'] = [int('0x2F800', 16), int('0x2FA20', 16)]
        self.curdir = os.path.abspath(os.path.dirname(__file__))

        for line in fs:
            line = re.sub('^ | $', '', line)
            if self.imeDirName == "cheez":
                if not line or (line[0] == '#' and state == PARSING_HEAD_STATE):
                    continue
            else:
                if not line or line[0] == '#':
                    continue

            if state is not PARSE_CHARDEF_STATE:
                if CIN_HEAD in line:
                    continue

                if ENAME_HEAD in line:
                    self.ename = head_rest(ENAME_HEAD, line)

                if CNAME_HEAD in line:
                    self.cname = head_rest(CNAME_HEAD, line)

                if ENCODING_HEAD in line:
                    continue

                if SELKEY_HEAD in line:
                    self.selkey = head_rest(SELKEY_HEAD, line)

                if CHARDEF_HEAD in line:
                    if 'begin' in line:
                        state = PARSE_CHARDEF_STATE
                    else:
                        state = PARSING_HEAD_STATE
                    continue

                if KEYNAME_HEAD in line:
                    if 'begin' in line:
                        state = PARSE_KEYNAME_STATE
                    else:
                        state = PARSING_HEAD_STATE
                    continue

                if state is PARSE_KEYNAME_STATE:
                    key, root = safeSplit(line)
                    key = key.strip().lower()

                    if '　' in root:
                        root = '\u3000'
                    else:
                        root = root.strip()

                    self.keynames[key] = root
                    continue
            else:
                if CHARDEF_HEAD in line:
                    continue

                if self.cname == "中標倉頡":
                    if '#' in line:
                        line = re.sub('#.+', '', line)

                key, root = safeSplit(line)
                key = key.strip().lower()

                if '　' in root:
                    root = '\u3000'
                else:
                    root = root.strip()

                matchstr = ''
                if len(root) > 1:
                    matchstr = root[0]
                else:
                    matchstr = root
                matchint = ord(matchstr)

                charset = self.getCharSet(matchstr, matchint, self.sortByCharset, True, key, root)

                if not self.sortByCharset:
                    if self.ignorePrivateUseArea and charset == "pua":
                        continue
                    try:
                        self.chardefs[key].append(root)
                    except KeyError:
                        self.chardefs[key] = [root]
                    self.cincount['cjkTotalchardefs'] += 1

        if self.sortByCharset:
            self.mergeDicts(self.big5Fchardefs, self.big5LFchardefs, self.big5Otherchardefs, self.bopomofochardefs, self.cjkchardefs, self.cjkExtAchardefs, self.cjkExtBchardefs, self.cjkExtCchardefs, self.cjkExtDchardefs, self.cjkExtEchardefs, self.cjkOtherchardefs)
        self.saveCountFile()

    def __del__(self):
        del self.keynames
        del self.chardefs
        del self.srcchardefs
        del self.bopomofochardefs
        del self.big5Fchardefs
        del self.big5LFchardefs
        del self.big5Otherchardefs
        del self.cjkchardefs
        del self.cjkExtAchardefs
        del self.cjkExtBchardefs
        del self.cjkExtCchardefs
        del self.cjkExtDchardefs
        del self.cjkExtEchardefs
        del self.cjkOtherchardefs
        del self.privateusechardefs
        del self.cincount

        self.keynames = {}
        self.chardefs = {}
        self.srcchardefs = {}
        self.bopomofochardefs = {}
        self.big5Fchardefs = {}
        self.big5LFchardefs = {}
        self.big5Otherchardefs = {}
        self.cjkchardefs = {}
        self.cjkExtAchardefs = {}
        self.cjkExtBchardefs = {}
        self.cjkExtCchardefs = {}
        self.cjkExtDchardefs = {}
        self.cjkExtEchardefs = {}
        self.cjkOtherchardefs = {}
        self.privateusechardefs = {}
        self.cincount = {}

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

    def mergeDicts(self, *chardefsdicts):
        for chardefsdict in chardefsdicts:
            for key in chardefsdict:
                for root in chardefsdict[key]:
                    try:
                        self.chardefs[key].append(root)
                    except KeyError:
                        self.chardefs[key] = [root]
                    self.cincount['cjkTotalchardefs'] += 1

    def updateCinTable(self, userExtendTable, priorityExtendTable, extendtable, ignorePrivateUseArea):
        chardefsdicts = [self.big5Fchardefs, self.big5LFchardefs, self.big5Otherchardefs, self.bopomofochardefs, self.cjkchardefs, self.cjkExtAchardefs, self.cjkExtBchardefs, self.cjkExtCchardefs, self.cjkExtDchardefs, self.cjkExtEchardefs, self.cjkOtherchardefs]
        if not ignorePrivateUseArea:
            chardefsdicts.append(self.privateusechardefs)

        if self.sortByCharset:
            del self.chardefs
            self.chardefs = {}
            for chardefsdict in chardefsdicts:
                for key in chardefsdict:
                    for root in chardefsdict[key]:
                        try:
                            self.chardefs[key].append(root)
                        except KeyError:
                            self.chardefs[key] = [root]

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
                    js = json.dump(self.cincount, f, indent=4)
            except Exception:
                pass # FIXME: handle I/O errors?

    def getCountDir(self):
        count_dir = os.path.join(os.path.expandvars("%APPDATA%"), "PIME", self.imeDirName)
        os.makedirs(count_dir, mode=0o700, exist_ok=True)
        return count_dir

    def getCountFile(self, name="cincount.json"):
        return os.path.join(self.getCountDir(), name)

    def getCharSet(self, matchstr, matchint, addchardefs, addcincount, key, root):
        if matchint <= self.charsetRange['cjk'][1]:
            if (matchint in range(self.charsetRange['bopomofo'][0], self.charsetRange['bopomofo'][1]) or # Bopomofo 區域
                matchint in self.charsetRange['bopomofoTone']): 
                if addchardefs:
                    try:
                        self.bopomofochardefs[key].append(root) # 注音符號
                    except KeyError:
                        self.bopomofochardefs[key] = [root]
                if addcincount:
                    self.cincount['bopomofochardefs'] += 1
                return "bopomofo"
            elif matchint in range(self.charsetRange['cjk'][0], self.charsetRange['cjk'][1]): # CJK Unified Ideographs 區域
                try:
                    big5code = matchstr.encode('big5')
                    big5codeint = int(big5code.hex(), 16)

                    if big5codeint in range(self.charsetRange['big5F'][0], self.charsetRange['big5F'][1]): # Big5 常用字
                        if addchardefs:
                            try:
                                self.big5Fchardefs[key].append(root)
                            except KeyError:
                                self.big5Fchardefs[key] = [root]
                        if addcincount:
                            self.cincount['big5Fchardefs'] += 1
                        return "big5F"
                    elif big5codeint in range(self.charsetRange['big5LF'][0], self.charsetRange['big5LF'][1]): # Big5 次常用字
                        if addchardefs:
                            try:
                                self.big5LFchardefs[key].append(root)
                            except KeyError:
                                self.big5LFchardefs[key] = [root]
                        if addcincount:
                            self.cincount['big5LFchardefs'] += 1
                        return "big5LF"
                    else: # Big5 其它漢字
                        if addchardefs:
                            try:
                                self.big5Otherchardefs[key].append(root)
                            except KeyError:
                                self.big5Otherchardefs[key] = [root]
                        if addcincount:
                            self.cincount['big5Otherchardefs'] += 1
                        return "big5Other"
                except: # CJK Unified Ideographs 漢字
                    if addchardefs:
                        try:
                            self.cjkchardefs[key].append(root)
                        except KeyError:
                            self.cjkchardefs[key] = [root]
                    if addcincount:
                        self.cincount['cjkchardefs'] += 1
                    return "cjk"
            elif matchint in range(self.charsetRange['cjkExtA'][0], self.charsetRange['cjkExtA'][1]): # CJK Unified Ideographs Extension A 區域
                if addchardefs:
                    try:
                        self.cjkExtAchardefs[key].append(root) # CJK 擴展 A 區
                    except KeyError:
                        self.cjkExtAchardefs[key] = [root]
                if addcincount:
                    self.cincount['cjkExtAchardefs'] += 1
                return "cjkExtA"
        else:
            if matchint in range(self.charsetRange['cjkExtB'][0], self.charsetRange['cjkExtB'][1]): # CJK Unified Ideographs Extension B 區域
                if addchardefs:
                    try:
                        self.cjkExtBchardefs[key].append(root) # CJK 擴展 B 區
                    except KeyError:
                        self.cjkExtBchardefs[key] = [root]
                if addcincount:
                    self.cincount['cjkExtBchardefs'] += 1
                return "cjkExtB"
            elif matchint in range(self.charsetRange['cjkExtC'][0], self.charsetRange['cjkExtC'][1]): # CJK Unified Ideographs Extension C 區域
                if addchardefs:
                    try:
                        self.cjkExtCchardefs[key].append(root) # CJK 擴展 C 區
                    except KeyError:
                        self.cjkExtCchardefs[key] = [root]
                if addcincount:
                    self.cincount['cjkExtCchardefs'] += 1
                return "cjkExtC"
            elif matchint in range(self.charsetRange['cjkExtD'][0], self.charsetRange['cjkExtD'][1]): # CJK Unified Ideographs Extension D 區域
                if addchardefs:
                    try:
                        self.cjkExtDchardefs[key].append(root) # CJK 擴展 D 區
                    except KeyError:
                        self.cjkExtDchardefs[key] = [root]
                if addcincount:
                    self.cincount['cjkExtDchardefs'] += 1
                return "cjkExtD"
            elif matchint in range(self.charsetRange['cjkExtE'][0], self.charsetRange['cjkExtE'][1]): # CJK Unified Ideographs Extension E 區域
                if addchardefs:
                    try:
                        self.cjkExtEchardefs[key].append(root) # CJK 擴展 E 區
                    except KeyError:
                        self.cjkExtEchardefs[key] = [root]
                if addcincount:
                    self.cincount['cjkExtEchardefs'] += 1
                return "cjkExtE"
            elif (matchint in range(self.charsetRange['pua'][0], self.charsetRange['pua'][1]) or # Unicode Private Use 區域
                matchint in range(self.charsetRange['puaA'][0], self.charsetRange['puaA'][1]) or
                matchint in range(self.charsetRange['puaB'][0], self.charsetRange['puaB'][1])):
                if addchardefs:
                    try:
                        self.privateusechardefs[key].append(root) # Unicode 私用區
                    except KeyError:
                        self.privateusechardefs[key] = [root]
                if addcincount:
                    self.cincount['privateusechardefs'] += 1
                return "pua"
            elif matchint in range(self.charsetRange['cjkS'][0], self.charsetRange['cjkS'][1]): # cjk compatibility ideographs supplement 區域
                if addchardefs:
                    try:
                        self.privateusechardefs[key].append(root) # CJK 相容字集補充區
                    except KeyError:
                        self.privateusechardefs[key] = [root]
                if addcincount:
                    self.cincount['privateusechardefs'] += 1
                return "pua"
        # 不在 CJK Unified Ideographs 區域
        if addchardefs:
            try:
                self.cjkOtherchardefs[key].append(root) # CJK 其它漢字或其它字集字元
            except KeyError:
                self.cjkOtherchardefs[key] = [root]
        if addcincount:
            self.cincount['cjkOtherchardefs'] += 1
        return "cjkOther"


def head_rest(head, line):
    return line[len(head):].strip()

def safeSplit(line):
    if ' ' in line:
        return line.split(' ', 1)
    elif '\t' in line:
        return line.split('\t', 1)
    else:
        return line, "Error"

__all__ = ["Cin"]
