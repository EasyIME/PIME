import json
import os
import time

import copy

from cinbase.tools import cpuinfo


class Debug:
    def __init__(self, imeDirName):
        self.info = cpuinfo.get_cpu_info()
        self.debugLog = {}
        self.startTime = {}
        self.endTime = {}
        self.imeDirName = imeDirName
        self.jsonNameDict = ({"simplecj.json": "正體簡易"})

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
                pass  # FIXME: handle I/O errors?
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
            pass  # FIXME: handle I/O errors?


__all__ = ["Debug"]
