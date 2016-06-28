from __future__ import print_function
from __future__ import unicode_literals

class swkb(object):

    # TODO check the possiblility if the encoding is not utf-8
    encoding = 'utf-8'

    def __init__(self, fs):

        self.chardefs = {}

        for line in fs:

            line = line.strip()

            key, root = safeSplit(line)
            key = key.strip()
            root = root.strip()

            try:
                self.chardefs[key].append(root)
            except KeyError:
                self.chardefs[key] = [root]

    def isInCharDef(self, key):
        return key in self.chardefs

    def getCharDef(self, key):
        """ 
        will return a list conaining all possible result
        """
        return self.chardefs[key]


def safeSplit(line):
    if ' ' in line:
        return line.split(' ', 1)
    elif '\t' in line:
        return line.split('\t', 1)
    else:
        return line, "Error"

__all__ = ["swkb"]
