import os
import time
import json
from cinbase.cpuinfo import cpuinfo

class Debug:

    # TODO check the possiblility if the encoding is not utf-8
    encoding = 'utf-8'

    def __init__(self):
        self.info = cpuinfo.get_cpu_info()
        self.startTime = {}
        self.endTime = {}
        self.imeDirName = ""
        self.cinNameDict = ({"checj.cin": "酷倉", "mscj3.cin": "倉頡", "mscj3-ext.cin": "倉頡(大字集)", "cj-ext.cin": "雅虎倉頡", "cnscj.cin": "中標倉頡",
                        "thcj.cin": "泰瑞倉頡", "newcj3.cin": "亂倉打鳥", "cj5.cin": "倉頡五代", "newcj.cin": "自由大新倉頡", "scj6.cin": "快倉六代",
                        "thphonetic.cin": "泰瑞注音", "CnsPhonetic.cin": "中標注音", "bpmf.cin": "傳統注音", "tharray.cin": "泰瑞行列30", "array30.cin": "行列30",
                        "ar30-big.cin": "行列30大字集", "array40.cin": "行列40", "thdayi.cin": "泰瑞大易四碼", "dayi4.cin": "大易四碼", "dayi3.cin": "大易三碼",
                        "ez.cin": "輕鬆", "ezsmall.cin": "輕鬆小詞庫", "ezmid.cin": "輕鬆中詞庫", "ezbig.cin": "輕鬆大詞庫", "thpinyin.cin": "泰瑞拼音",
                        "pinyin.cin": "正體拼音", "roman.cin": "羅馬拼音", "simplecj.cin": "正體簡易", "simplex.cin": "速成", "simplex5.cin": "簡易五代",
                        "liu.cin": "嘸蝦米"})

    def setStartTimer(self, timerName):
        self.startTime[timerName] = time.time()

    def setEndTimer(self, timerName):
        self.endTime[timerName] = time.time()

    def logTimerInfo(self, timerName, imeDirName , cinfile, infoStr):
        self.imeDirName = imeDirName
        durationTime = round(self.endTime[timerName] - self.startTime[timerName], 2)
        jsondata = {}

        filename = self.getConfigFile()
        try:
            if os.path.isfile(filename):
                with open(filename) as f:
                    jsondata = json.load(f)

            jsondata[time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())] = self.info['brand'] + ":「" + self.cinNameDict[cinfile] + "」" + infoStr + "時間約為 " + str(durationTime) + " 秒"
            with open(filename, "w") as f:
                js = json.dump(jsondata, f, ensure_ascii=False, sort_keys=True, indent=4)
        except Exception:
            pass # FIXME: handle I/O errors?
        return jsondata

    def getConfigDir(self):
        config_dir = os.path.join(os.path.expandvars("%APPDATA%"), "PIME", self.imeDirName)
        os.makedirs(config_dir, mode=0o700, exist_ok=True)
        return config_dir

    def getConfigFile(self, name="debug.json"):
        return os.path.join(self.getConfigDir(), name)

Debug = Debug()
