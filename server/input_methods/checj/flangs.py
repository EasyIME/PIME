from __future__ import print_function
from __future__ import unicode_literals

class flangs(object):

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
            
            for rootstr in root:
                try:
                    self.chardefs[key].append(rootstr)
                except KeyError:
                    self.chardefs[key] = [rootstr]

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


def safeSplit(line):
    if '=' in line:
        return line.split('=', 1)
    elif ' ' in line:
        return line.split(' ', 1)
    elif '\t' in line:
        return line.split('\t', 1)
    else:
        return line, line

__all__ = ["flangs"]
