from __future__ import print_function
from __future__ import unicode_literals
import os
import re
import json


class dsymbols(object):

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


__all__ = ["dsymbols"]
