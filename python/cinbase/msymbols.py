from __future__ import print_function
from __future__ import unicode_literals

class msymbols(object):

    # TODO check the possiblility if the encoding is not utf-8
    encoding = 'utf-8'

    def __init__(self, fs):

        self.keynames = []
        self.chardefs = {}

        for line in fs:

            line = line.strip()

            key, root = safeSplit(line)
            key = key.strip()
            root = root.strip()
            
            if len(key) <= 1:
                for rootstr in root:
                    try:
                        self.chardefs[key].append(rootstr)
                    except KeyError:
                        self.chardefs[key] = [rootstr]
            else:
                try:
                    self.chardefs[key].append(root)
                except KeyError:
                    self.chardefs[key] = [root]

            if key not in self.keynames:
                self.keynames.append(key)

    def isInCharDef(self, key):
        return key in self.chardefs

    def getCharDef(self, key):
        """ 
        will return a list conaining all possible result
        """
        return self.chardefs[key]

    def getKeyNames(self):
        return self.keynames

    def isHaveKey(self, val):
        return True if [key for key, value in self.chardefs.items() if val in value] else False

    def getKey(self, val):
        return [key for key, value in self.chardefs.items() if val in value][0]


def safeSplit(line):
    if '=' in line:
        if line[:2] == '==':
            return line[:1], line[2:]
        else:
            return line.split('=', 1)
    elif ' ' in line:
        return line.split(' ', 1)
    elif '\t' in line:
        return line.split('\t', 1)
    else:
        return line, line

__all__ = ["msymbols"]
