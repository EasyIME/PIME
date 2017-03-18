from __future__ import print_function
from __future__ import unicode_literals
import io
import os
import re
import sys
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


class CinToJson(object):

    # TODO check the possiblility if the encoding is not utf-8
    encoding = 'utf-8'

    def __init__(self):
        self.sortByCharset = False

        self.ename = ""
        self.cname = ""
        self.selkey = ""
        self.keynames = {}
        self.chardefs = {}
        self.dupchardefs = {}

        self.bopomofo = {}
        self.big5F = {}
        self.big5LF = {}
        self.big5S = {}
        self.big5Other = {}
        self.cjk = {}
        self.cjkExtA = {}
        self.cjkExtB = {}
        self.cjkExtC = {}
        self.cjkExtD = {}
        self.cjkExtE = {}
        self.cjkOther = {}
        self.phrases = {}
        self.privateuse = {}

        self.cincount = {}
        self.cincount['bopomofo'] = 0
        self.cincount['big5F'] = 0
        self.cincount['big5LF'] = 0
        self.cincount['big5S'] = 0
        self.cincount['big5Other'] = 0
        self.cincount['cjk'] = 0
        self.cincount['cjkExtA'] = 0
        self.cincount['cjkExtB'] = 0
        self.cincount['cjkExtC'] = 0
        self.cincount['cjkExtD'] = 0
        self.cincount['cjkExtE'] = 0
        self.cincount['cjkOther'] = 0
        self.cincount['phrases'] = 0
        self.cincount['cjkCIS'] = 0
        self.cincount['privateuse'] = 0
        self.cincount['totalchardefs'] = 0

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

        self.haveHashtagInKeynames = ["ez.cin", "ezsmall.cin", "ezmid.cin", "ezbig.cin"]
        self.saveList = ["ename", "cname", "selkey", "keynames", "cincount", "chardefs", "dupchardefs", "privateuse"]
        self.curdir = os.path.abspath(os.path.dirname(__file__))


    def __del__(self):
        del self.keynames
        del self.chardefs
        del self.dupchardefs
        del self.bopomofo
        del self.big5F
        del self.big5LF
        del self.big5S
        del self.big5Other
        del self.cjk
        del self.cjkExtA
        del self.cjkExtB
        del self.cjkExtC
        del self.cjkExtD
        del self.cjkExtE
        del self.cjkOther
        del self.privateuse
        del self.phrases
        del self.cincount

        self.keynames = {}
        self.chardefs = {}
        self.dupchardefs = {}
        self.bopomofo = {}
        self.big5F = {}
        self.big5LF = {}
        self.big5S = {}
        self.big5Other = {}
        self.cjk = {}
        self.cjkExtA = {}
        self.cjkExtB = {}
        self.cjkExtC = {}
        self.cjkExtD = {}
        self.cjkExtE = {}
        self.cjkOther = {}
        self.privateuse = {}
        self.phrases = {}
        self.cincount = {}


    def run(self, file, filePath, sortByCharset):
        self.jsonFile = re.sub('\.cin$', '', file) + '.json'
        self.sortByCharset = sortByCharset
        state = PARSING_HEAD_STATE

        if file in self.haveHashtagInKeynames:
            print("字根含有 # 符號!")

        with io.open(filePath, encoding='utf-8') as fs:
            for line in fs:
                line = re.sub('^ | $|\\n$', '', line)
                if file in self.haveHashtagInKeynames:
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
                    # print(line)
                    if root == "Error":
                        print("發生錯誤!")
                        break

                    if '　' in root:
                        root = '\u3000'
                    else:
                        root = root.strip()

                    charset = self.getCharSet(key, root)

                    if not self.sortByCharset:
                        if key in  self.chardefs:
                            if root in self.chardefs[key]:
                                print("含有重複資料: " + key)
                                try:
                                    self.dupchardefs[key].append(root)
                                except KeyError:
                                    self.dupchardefs[key] = [root]
                            else:
                                try:
                                    self.chardefs[key].append(root)
                                except KeyError:
                                    self.chardefs[key] = [root]
                                self.cincount['totalchardefs'] += 1
                        else:
                            try:
                                self.chardefs[key].append(root)
                            except KeyError:
                                self.chardefs[key] = [root]
                            self.cincount['totalchardefs'] += 1

        if self.sortByCharset:
            print("排序字元集!")
            self.mergeDicts(self.big5F, self.big5LF, self.big5S, self.big5Other, self.bopomofo, self.cjk, self.cjkExtA, self.cjkExtB, self.cjkExtC, self.cjkExtD, self.cjkExtE, self.cjkOther, self.phrases, self.privateuse)
        self.saveJsonFile(self.jsonFile)


    def mergeDicts(self, *chardefsdicts):
        for chardefsdict in chardefsdicts:
            for key in chardefsdict:
                for root in chardefsdict[key]:
                    if key in  self.chardefs:
                        if root in self.chardefs[key]:
                            print("含有重複資料: " + key + " = " + root)
                            try:
                                self.dupchardefs[key].append(root)
                            except KeyError:
                                self.dupchardefs[key] = [root]
                        else:
                            try:
                                self.chardefs[key].append(root)
                            except KeyError:
                                self.chardefs[key] = [root]
                            self.cincount['totalchardefs'] += 1
                    else:
                        try:
                            self.chardefs[key].append(root)
                        except KeyError:
                            self.chardefs[key] = [root]
                        self.cincount['totalchardefs'] += 1


    def toJson(self):
        return {key: value for key, value in self.__dict__.items() if key in self.saveList}


    def saveJsonFile(self, file):
        filename = self.getJsonFile(file)
        try:
            with open(filename, 'w', encoding='utf8') as f:
                js = json.dump(self.toJson(), f, ensure_ascii=False, sort_keys=True, indent=4)
        except Exception:
            pass # FIXME: handle I/O errors?


    def getJsonDir(self):
        json_dir = os.path.join(self.curdir, os.pardir, "json")
        os.makedirs(json_dir, mode=0o700, exist_ok=True)
        return json_dir


    def getJsonFile(self, name):
        return os.path.join(self.getJsonDir(), name)


    def getCharSet(self, key, root):
        matchstr = ''
        if len(root) > 1:
            try:
                self.phrases[key].append(root)
            except KeyError:
                self.phrases[key] = [root]
            self.cincount['phrases'] += 1
            return "phrases"
        else:
            matchstr = root
            matchint = ord(matchstr)

        if matchint <= self.charsetRange['cjk'][1]:
            if (matchint in range(self.charsetRange['bopomofo'][0], self.charsetRange['bopomofo'][1]) or # Bopomofo 區域
                matchint in self.charsetRange['bopomofoTone']): 
                try:
                    self.bopomofo[key].append(root) # 注音符號
                except KeyError:
                    self.bopomofo[key] = [root]
                self.cincount['bopomofo'] += 1
                return "bopomofo"
            elif matchint in range(self.charsetRange['cjk'][0], self.charsetRange['cjk'][1]): # CJK Unified Ideographs 區域
                try:
                    big5code = matchstr.encode('big5')
                    big5codeint = int(big5code.hex(), 16)

                    if big5codeint in range(self.charsetRange['big5F'][0], self.charsetRange['big5F'][1]): # Big5 常用字
                        try:
                            self.big5F[key].append(root)
                        except KeyError:
                            self.big5F[key] = [root]
                        self.cincount['big5F'] += 1
                        return "big5F"
                    elif big5codeint in range(self.charsetRange['big5LF'][0], self.charsetRange['big5LF'][1]): # Big5 次常用字
                        try:
                            self.big5LF[key].append(root)
                        except KeyError:
                            self.big5LF[key] = [root]
                        self.cincount['big5LF'] += 1
                        return "big5LF"
                    elif big5codeint in range(self.charsetRange['big5S'][0], self.charsetRange['big5S'][1]): # Big5 符號
                        try:
                            self.big5S[key].append(root)
                        except KeyError:
                            self.big5S[key] = [root]
                        self.cincount['big5S'] += 1
                        return "big5LF"
                    else: # Big5 其它漢字
                        try:
                            self.big5Other[key].append(root)
                        except KeyError:
                            self.big5Other[key] = [root]
                        self.cincount['big5Other'] += 1
                        return "big5Other"
                except: # CJK Unified Ideographs 漢字
                    try:
                        self.cjk[key].append(root)
                    except KeyError:
                        self.cjk[key] = [root]
                    self.cincount['cjk'] += 1
                    return "cjk"
            elif matchint in range(self.charsetRange['cjkExtA'][0], self.charsetRange['cjkExtA'][1]): # CJK Unified Ideographs Extension A 區域
                try:
                    self.cjkExtA[key].append(root) # CJK 擴展 A 區
                except KeyError:
                    self.cjkExtA[key] = [root]
                self.cincount['cjkExtA'] += 1
                return "cjkExtA"
        else:
            if matchint in range(self.charsetRange['cjkExtB'][0], self.charsetRange['cjkExtB'][1]): # CJK Unified Ideographs Extension B 區域
                try:
                    self.cjkExtB[key].append(root) # CJK 擴展 B 區
                except KeyError:
                    self.cjkExtB[key] = [root]
                self.cincount['cjkExtB'] += 1
                return "cjkExtB"
            elif matchint in range(self.charsetRange['cjkExtC'][0], self.charsetRange['cjkExtC'][1]): # CJK Unified Ideographs Extension C 區域
                try:
                    self.cjkExtC[key].append(root) # CJK 擴展 C 區
                except KeyError:
                    self.cjkExtC[key] = [root]
                self.cincount['cjkExtC'] += 1
                return "cjkExtC"
            elif matchint in range(self.charsetRange['cjkExtD'][0], self.charsetRange['cjkExtD'][1]): # CJK Unified Ideographs Extension D 區域
                try:
                    self.cjkExtD[key].append(root) # CJK 擴展 D 區
                except KeyError:
                    self.cjkExtD[key] = [root]
                self.cincount['cjkExtD'] += 1
                return "cjkExtD"
            elif matchint in range(self.charsetRange['cjkExtE'][0], self.charsetRange['cjkExtE'][1]): # CJK Unified Ideographs Extension E 區域
                try:
                    self.cjkExtE[key].append(root) # CJK 擴展 E 區
                except KeyError:
                    self.cjkExtE[key] = [root]
                self.cincount['cjkExtE'] += 1
                return "cjkExtE"
            elif (matchint in range(self.charsetRange['pua'][0], self.charsetRange['pua'][1]) or # Unicode Private Use 區域
                matchint in range(self.charsetRange['puaA'][0], self.charsetRange['puaA'][1]) or
                matchint in range(self.charsetRange['puaB'][0], self.charsetRange['puaB'][1])):
                try:
                    self.privateuse[key].append(root) # Unicode 私用區
                except KeyError:
                    self.privateuse[key] = [root]
                self.cincount['privateuse'] += 1
                return "pua"
            elif matchint in range(self.charsetRange['cjkCIS'][0], self.charsetRange['cjkCIS'][1]): # cjk compatibility ideographs supplement 區域
                try:
                    self.privateuse[key].append(root) # CJK 相容字集補充區
                except KeyError:
                    self.privateuse[key] = [root]
                self.cincount['cjkCIS'] += 1
                return "pua"
        # 不在 CJK Unified Ideographs 區域
        try:
            self.cjkOther[key].append(root) # CJK 其它漢字或其它字集字元
        except KeyError:
            self.cjkOther[key] = [root]
        self.cincount['cjkOther'] += 1
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


def main():
    app = CinToJson()
    if len(sys.argv) >= 2:
        cinFile = os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, "cin", sys.argv[1])
        if os.path.exists(cinFile):
            if len(sys.argv) >= 3 and sys.argv[2] == "sort":
                app.run(sys.argv[1], cinFile, True)
            else:
                app.run(sys.argv[1], cinFile, False)
    else:
        if len(sys.argv) == 1:
            sortList = ['cnscj.cin', 'CnsPhonetic.cin']
            for file in os.listdir(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, "cin")):
                if file.endswith(".cin"):
                    print('轉換 ' + file + ' 中...')
                    app.__init__()
                    cinFile = os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, "cin", file)
                    if file in sortList:
                        app.run(file, cinFile, True)
                    else:
                        app.run(file, cinFile, False)
                app.__del__()
        else:
            print('檔案不存在!')


if __name__ == "__main__":
    main()