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


class HCin(object):

    # TODO check the possiblility if the encoding is not utf-8
    encoding = 'utf-8'

    def __init__(self, fs, imeDirName):

        state = PARSING_HEAD_STATE

        self.imeDirName = imeDirName
        self.keynames = {}
        self.chardefs = {}
        self.curdir = os.path.abspath(os.path.dirname(__file__))

        for line in fs:
            line = re.sub('^ | $', '', line)
            if self.imeDirName == "cheez":
                if not line or (line[0] == '#' and state == PARSING_HEAD_STATE):
                    continue
            else:
                if not line or line[0] == '#':
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
                if not self.imeDirName == "cheez":
                    if '#' in line:
                        line = re.sub('#.+', '', line)
                key, root = safeSplit(line)
                key = key.strip().lower()

                if '　' in root:
                    root = '\u3000'
                else:
                    root = root.strip()

                try:
                    self.chardefs[key].append(root)
                except KeyError:
                    self.chardefs[key] = [root]

    def __del__(self):
        del self.keynames
        del self.chardefs
        self.keynames = {}
        self.chardefs = {}

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

    def getKeyList(self, val):
        return [key for key, value in self.chardefs.items() if val in value]

    def getKeyNameList(self, keyList):
        result = []
        for key in keyList:
            keyname = ''
            for char in key:
                keyname += self.getKeyName(char)
            result.append(keyname)
        return result

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
            result = ''
        return result

    def saveCountFile(self):
        filename = self.getCountFile()
        try:
            with open(filename, "w") as f:
                js = json.dump(self.cincount, f, indent=4)
        except Exception:
            pass # FIXME: handle I/O errors?

def head_rest(head, line):
    return line[len(head):].strip()

def safeSplit(line):
    if ' ' in line:
        return line.split(' ', 1)
    elif '\t' in line:
        return line.split('\t', 1)
    else:
        return line, "Error"

__all__ = ["HCin"]
