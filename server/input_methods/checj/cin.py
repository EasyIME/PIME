from __future__ import print_function
from __future__ import unicode_literals
import re

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

        for line in fs:
            line = re.sub('^ | $', '', line)
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

                key, root = line.split()
                key = key.strip()
                root = root.strip()

                self.keynames[key] = root
                continue

            if state is PARSE_CHARDEF_STATE:
                if '#' in line:
                    line = re.sub('#.+', '', line)
                key, root = safeSplit(line)
                
                key = key.strip()

                if '　' in root:
                    root = '\u3000'
                else:
                    root = root.strip()

                try:
                    self.chardefs[key].append(root)
                except KeyError:
                    self.chardefs[key] = [root]

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
        cjkextchardefs = []
        matchchardefs = {}

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
                for char in chardef:
                    if re.match('[\u4e00-\u9fff]', char):
                        if not char in wildcardchardefs:
                            wildcardchardefs.append(char)
                    else:
                        if not char in cjkextchardefs:
                            cjkextchardefs.append(char)

                    if len(wildcardchardefs) >= candMaxItems:
                        return wildcardchardefs
            
            if len(cjkextchardefs) > 0:
                for cjkextchar in cjkextchardefs:
                    if not cjkextchar in wildcardchardefs:
                        wildcardchardefs.append(cjkextchar)
                    
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
