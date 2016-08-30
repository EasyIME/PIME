from __future__ import print_function
from __future__ import unicode_literals
import os
import re
import json

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

    def __init__(self, fs):

        state = PARSING_HEAD_STATE

        self.keynames = {}
        self.chardefs = {}
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
        self.curdir = os.path.abspath(os.path.dirname(__file__))

        for line in fs:
            line = re.sub('^ | $', '', line)
            if not line or (line[0] == '#' and state == PARSING_HEAD_STATE):
                continue

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

            if state is PARSE_CHARDEF_STATE:

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

                if re.match('[\u3100-\u312F]|[\u02D9]|[\u02CA]|[\u02C7]|[\u02CB]', matchstr): # Bopomofo 區域
                    try:
                        self.bopomofochardefs[key].append(root) # 注音符號
                    except KeyError:
                        self.bopomofochardefs[key] = [root]
                    self.cincount['bopomofochardefs'] += 1
                elif re.match('[\u4E00-\u9FD5]', matchstr): # CJK Unified Ideographs 區域
                    try:
                        big5code = matchstr.encode('big5')

                        if int(big5code.hex(), 16) in range(int('0xA440', 16), int('0xC67F', 16)): # Big5 常用字
                            try:
                                self.big5Fchardefs[key].append(root)
                            except KeyError:
                                self.big5Fchardefs[key] = [root]
                            self.cincount['big5Fchardefs'] += 1
                        elif int(big5code.hex(), 16) in range(int('0xC940', 16), int('0xF9D6', 16)): # Big5 次常用字
                            try:
                                self.big5LFchardefs[key].append(root)
                            except KeyError:
                                self.big5LFchardefs[key] = [root]
                            self.cincount['big5LFchardefs'] += 1
                        else: # Big5 其它漢字
                            try:
                                self.big5Otherchardefs[key].append(root)
                            except KeyError:
                                self.big5Otherchardefs[key] = [root]
                            self.cincount['big5Otherchardefs'] += 1
                    except: # CJK Unified Ideographs 漢字
                        try:
                            self.cjkchardefs[key].append(root)
                        except KeyError:
                            self.cjkchardefs[key] = [root]
                        self.cincount['cjkchardefs'] += 1
                elif re.match('[\u3400-\u4DB5]', matchstr): # CJK Unified Ideographs Extension A 區域
                    try:
                        self.cjkExtAchardefs[key].append(root) # CJK 擴展 A 區
                    except KeyError:
                        self.cjkExtAchardefs[key] = [root]
                    self.cincount['cjkExtAchardefs'] += 1
                elif re.match('[𠀀-𪛖]', matchstr): # CJK Unified Ideographs Extension B 區域
                    try:
                        self.cjkExtBchardefs[key].append(root) # CJK 擴展 B 區
                    except KeyError:
                        self.cjkExtBchardefs[key] = [root]
                    self.cincount['cjkExtBchardefs'] += 1
                elif re.match('[𪜀-𫜴]', matchstr): # CJK Unified Ideographs Extension C 區域
                    try:
                        self.cjkExtCchardefs[key].append(root) # CJK 擴展 C 區
                    except KeyError:
                        self.cjkExtCchardefs[key] = [root]
                    self.cincount['cjkExtCchardefs'] += 1
                elif re.match('[𫝀-𫠝]', matchstr): # CJK Unified Ideographs Extension D 區域
                    try:
                        self.cjkExtDchardefs[key].append(root) # CJK 擴展 D 區
                    except KeyError:
                        self.cjkExtDchardefs[key] = [root]
                    self.cincount['cjkExtDchardefs'] += 1
                elif re.match('[𫠠-𬺡]', matchstr): # CJK Unified Ideographs Extension E 區域
                    try:
                        self.cjkExtEchardefs[key].append(root) # CJK 擴展 E 區
                    except KeyError:
                        self.cjkExtEchardefs[key] = [root]
                    self.cincount['cjkExtEchardefs'] += 1
                else: # 不在 CJK Unified Ideographs 區域
                    try:
                        self.cjkOtherchardefs[key].append(root) # CJK 其它漢字或其它字集字元
                    except KeyError:
                        self.cjkOtherchardefs[key] = [root]
                    self.cincount['cjkOtherchardefs'] += 1
        self.mergeDicts(self.bopomofochardefs, self.big5Fchardefs, self.big5LFchardefs, self.big5Otherchardefs, self.cjkchardefs, self.cjkExtAchardefs, self.cjkExtBchardefs, self.cjkExtCchardefs, self.cjkExtDchardefs, self.cjkExtEchardefs, self.cjkOtherchardefs)

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
        matchchardefs = [self.chardefs[key] for key in self.chardefs if re.match('^' + matchstring + '$', key) and len(key) == keyLength]

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
                    elif re.match('[𠀀-𪛖]', matchstr): # CJK Unified Ideographs Extension B 區域
                        if not matchstr in cjkextchardefs[6]:
                            cjkextchardefs[6].append(matchstr)
                            lowFrequencyWordCount += 1
                    elif re.match('[𪜀-𫜴]', matchstr): # CJK Unified Ideographs Extension C 區域
                        if not matchstr in cjkextchardefs[7]:
                            cjkextchardefs[7].append(matchstr)
                            lowFrequencyWordCount += 1
                    elif re.match('[𫝀-𫠝]', matchstr): # CJK Unified Ideographs Extension D 區域
                        if not matchstr in cjkextchardefs[8]:
                            cjkextchardefs[8].append(matchstr)
                            lowFrequencyWordCount += 1
                    elif re.match('[𫠠-𬺡]', matchstr): # CJK Unified Ideographs Extension E 區域
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
        self.saveCountFile()

    def saveCountFile(self):
        filename = self.getCountFile()
        try:
            with open(filename, "w") as f:
                js = json.dump(self.cincount, f, indent=4)
        except Exception:
            pass # FIXME: handle I/O errors?

    def getCountDir(self):
        dirname = os.path.basename(self.curdir)
        count_dir = os.path.join(os.path.expandvars("%APPDATA%"), "PIME", dirname)
        os.makedirs(count_dir, mode=0o700, exist_ok=True)
        return count_dir

    def getCountFile(self, name="cincount.json"):
        return os.path.join(self.getCountDir(), name)

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
