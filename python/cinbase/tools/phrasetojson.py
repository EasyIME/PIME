from __future__ import print_function
from __future__ import unicode_literals
import io
import os
import re
import sys
import json
import copy

class PhraseToJson(object):

    # TODO check the possiblility if the encoding is not utf-8
    encoding = 'utf-8'

    def __init__(self):
        self.keynames = []
        self.chardefs = {}
        self.saveList = ["keynames", "chardefs"]
        self.curdir = os.path.abspath(os.path.dirname(__file__))

    def __del__(self):
        del self.keynames
        del self.chardefs
        self.keynames = []
        self.chardefs = {}

    def run(self, file, filePath):
        self.jsonFile = re.sub('\.dat$', '', file) + '.json'
        
        with io.open(filePath, encoding='utf-8') as fs:
            for line in fs:
                line = re.sub('^ | $|\\n$', '', line)
    
                key, root = safeSplit(line)
                key = key.strip()
                rootlist = rootSplit(root)
                
                if len(rootlist) > 0:
                    for rootstr in rootlist:
                        stripstr = rootstr.strip()
                        try:
                            self.chardefs[key].append(stripstr)
                        except KeyError:
                            self.chardefs[key] = [stripstr]
    
                    if key not in self.keynames:
                        self.keynames.append(key)
        self.saveJsonFile(self.jsonFile)


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
        json_dir = os.path.join(self.curdir, os.pardir, "data")
        os.makedirs(json_dir, mode=0o700, exist_ok=True)
        return json_dir


    def getJsonFile(self, name):
        return os.path.join(self.getJsonDir(), name)


def safeSplit(line):
    if '=' in line:
        return line.split('=', 1)
    elif ' ' in line:
        return line.split(' ', 1)
    elif '\t' in line:
        return line.split('\t', 1)
    else:
        return line, line

def rootSplit(line):
    if ',' in line:
        return line.split(',')
    else:
        return [line]


def main():
    app = PhraseToJson()
    if len(sys.argv) >= 2:
        dataFile = os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, "data", sys.argv[1])
        if os.path.exists(dataFile):
            app.run(sys.argv[1], dataFile)
    else:
        print('檔案不存在!')


if __name__ == "__main__":
    main()
