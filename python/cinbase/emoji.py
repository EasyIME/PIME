from __future__ import print_function
from __future__ import unicode_literals
import os
import re
import json

class emoji(object):

    # TODO check the possiblility if the encoding is not utf-8
    encoding = 'utf-8'

    def __init__(self, fs):
        self.__dict__.update(json.load(fs))


    def getCharDef(self, emojitype, keyname):
        if emojitype == "dingbats":
            keyindex = self.dingbats_keynames.index(keyname)
            keys = ["miscellaneous", "crosses", "starsandsnows", "fleurons", "punctuationmarks", "brackets", "digits", "arrows", "arithmetics"] # "rockets" (Ornamental Dingbats)
            return self.dingbats[keys[keyindex]]
        elif emojitype == "emoticons":
            keyindex = self.emoticons_keynames.index(keyname)
            keys = ["faces", "catfaces", "animal", "gesture"]
            return self.emoticons[keys[keyindex]]
        elif emojitype == "miscellaneous":
            keyindex = self.miscellaneous_keynames.index(keyname)
            keys = (["weathers", "miscellaneous", "chess", "pointinghand", "warningsigns", "medical", "religiousandpolitical", "yijingtrigram", "emoticons",
                    "zodiacal", "musical", "syriaccross", "recycling", "map", "gender", "circlesandpentagram", "genealogical", "sport", "trafficsigns"])
            return self.miscellaneous[keys[keyindex]]
        elif emojitype == "pictographs":
            keyindex = self.pictographs_keynames.index(keyname)
            keys = (["portraitandrole", "animal", "plant", "romance", "heart", "comicstyle", "bubble", "weatherandlandscape", "globe", "moonsunandstar",
                    "food", "fruitandvegetable", "beverage", "celebration", "musical", "entertainment", "game", "sport", "buildingandmap", "flag",
                    "miscellaneous", "facialparts", "hand", "clothing", "personalcare", "medical", "schoolgrade", "money", "office", "communication",
                    "audioandvideo", "religious", "userinterface", "wordswitharrows", "tool", "geometricshapes", "clockface", "computer"])
            return self.pictographs[keys[keyindex]]
        elif emojitype == "transport":
            keyindex = self.transport_keynames.index(keyname)
            keys = ["vehicles", "trafficsigns", "accommodation", "miscellaneous"]
            return self.transport[keys[keyindex]]
        return []

    def getKeyNames(self, emojidict):
        return emojidict

__all__ = ["emoji"]
