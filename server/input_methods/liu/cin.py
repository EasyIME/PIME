from __future__ import print_function
from __future__ import unicode_literals

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

            line = line.strip()
            if not line:
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
                key, root = line.split()
                key = key.strip()
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

    def getKeyName(self, key):
        return self.keynames[key]

    def getCharDef(self, key):
        """ 
        will return a list conaining all possible result
        """
        return self.chardefs[key]


def head_rest(head, line):
    return line[len(head):].strip()


__all__ = ["Cin"]
