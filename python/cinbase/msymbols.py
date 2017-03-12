from __future__ import print_function
from __future__ import unicode_literals
import os
import re
import json

class msymbols(object):

    # TODO check the possiblility if the encoding is not utf-8
    encoding = 'utf-8'

    def __init__(self, fs):
        self.keynames = []
        self.chardefs = {}
        self.__dict__.update(json.load(fs))


    def __del__(self):
        del self.keynames
        del self.chardefs
        self.keynames = []
        self.chardefs = {}


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
