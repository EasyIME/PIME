import os
import copy
import time
import json
from cinbase.tools import cpuinfo

class Debug:
    def __init__(self, imeDirName):
        self.info = cpuinfo.get_cpu_info()
        self.debugLog = {}
        self.startTime = {}
        self.endTime = {}
        self.imeDirName = imeDirName
        self.jsonNameDict = ({"checj.json": "酷倉", "mscj3.json": "倉頡", "mscj3-ext.json": "倉頡(大字集)", "cj-ext.json": "雅虎倉頡", "cnscj.json": "中標倉頡",
                        "thcj.json": "泰瑞倉頡", "newcj3.json": "亂倉打鳥", "cj5.json": "倉頡五代", "newcj.json": "自由大新倉頡", "scj6.json": "快倉六代",
                        "thphonetic.json": "泰瑞注音", "CnsPhonetic.json": "中標注音", "bpmf.json": "傳統注音", "tharray.json": "泰瑞行列30", "array30.json": "行列30",
                        "ar30-big.json": "行列30大字集", "array40.json": "行列40", "thdayi.json": "泰瑞大易四碼", "dayi4.json": "大易四碼", "dayi3.json": "大易三碼",
                        "ez.json": "輕鬆", "ezsmall.json": "輕鬆小詞庫", "ezmid.json": "輕鬆中詞庫", "ezbig.json": "輕鬆大詞庫", "thpinyin.json": "泰瑞拼音",
                        "pinyin.json": "正體拼音", "roman.json": "羅馬拼音", "simplecj.json": "正體簡易", "simplex.json": "速成", "simplex5.json": "簡易五代",
                        "liu.json": "嘸蝦米"})

    def getConfigDir(self):
        config_dir = os.path.join(os.path.expandvars("%APPDATA%"), "PIME", self.imeDirName)
        os.makedirs(config_dir, mode=0o700, exist_ok=True)
        return config_dir

    def getConfigFile(self, name="debug.json"):
        return os.path.join(self.getConfigDir(), name)

    def loadDebugLog(self):
        jsondata = {}
        filename = self.getConfigFile()
        if os.path.isfile(filename):
            try:
                with open(filename, 'r', encoding='utf8') as f:
                    jsondata = json.load(f)
            except Exception:
                pass # FIXME: handle I/O errors?
        self.debugLog = copy.deepcopy(jsondata)
        return jsondata

    def setStartTimer(self, timerName):
        self.startTime[timerName] = time.time()

    def setEndTimer(self, timerName):
        self.endTime[timerName] = time.time()

    def getDurationTime(self, timerName):
        durationTime = round(self.endTime[timerName] - self.startTime[timerName], 2)
        return str(durationTime)

    def saveDebugLog(self, debugLog):
        filename = self.getConfigFile()
        try:
            with open(filename, 'w', encoding='utf8') as f:
                js = json.dump(debugLog, f, ensure_ascii=False, sort_keys=True, indent=4)
            self.debugLog = copy.deepcopy(debugLog)
        except Exception:
            pass # FIXME: handle I/O errors?

__all__ = ["Debug"]
