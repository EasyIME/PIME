from __future__ import print_function
from __future__ import unicode_literals
import os
import re
import json


class phrase(object):

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


__all__ = ["phrase"]
