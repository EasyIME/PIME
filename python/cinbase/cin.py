from __future__ import print_function
from __future__ import unicode_literals
import os
import json
import copy
import time


class Cin(object):

    # TODO check the possiblility if the encoding is not utf-8
    encoding = 'utf-8'
    MAX_CONTEXT_ENTRIES = 32
    COUNT_SAVE_INTERVAL_SECONDS = 60.0

    def __init__(self, fs, imeDirName, ignorePrivateUseArea):
        self.imeDirName = imeDirName
        self.ignorePrivateUseArea = ignorePrivateUseArea
        self.curdir = os.path.abspath(os.path.dirname(__file__))

        self.ename = ""
        self.cname = ""
        self.selkey = ""
        self.keynames = {}
        self.cincount = {}
        self._count_dirty = False
        self._last_count_save_time = 0.0
        self.chardefs = {}
        self.privateuse = {}
        self.dupchardefs = {}

        self.__dict__.update(json.load(fs))

        if self.ignorePrivateUseArea:
            for key in self.privateuse:
                newvalue = list(self.chardefs[key])
                for value in self.privateuse[key]:
                    if value in newvalue:
                        newvalue.remove(value)
                self.chardefs[key] = newvalue

        self.loadCountFile()


    def __del__(self):
        try:
            self.saveCountFile(force=True)
        except Exception:
            pass
        for name in ("keynames", "cincount", "chardefs", "privateuse", "dupchardefs"):
            if hasattr(self, name):
                delattr(self, name)

        self.keynames = {}
        self.cincount = {}
        self.chardefs = {}
        self.privateuse = {}
        self.dupchardefs = {}


    def getEname(self):
        return self.ename


    def getCname(self):
        return self.cname


    def getSelection(self):
        return self.selkey


    def isInKeyName(self, key):
        return key in self.keynames


    def getKeyName(self, key):
        return self.keynames[key]


    def isHaveKey(self, val):
        return True if [key for key, value in self.chardefs.items() if val in value] else False


    def getKey(self, val):
        return [key for key, value in self.chardefs.items() if val in value][0]


    def isInCharDef(self, key):
        return key in self.chardefs


    def getCharDef(self, key):
        """ 
        will return a list conaining all possible result
        """
        return self.chardefs[key]


    def haveNextCharDef(self, key):
        chardefslist = []
        for chardef in self.chardefs:
            if key == chardef[:1]:
                chardefslist.append(chardef)
                if len(chardefslist) >= 2:
                    break
        return chardefslist


    def getCharEncode(self, root):
        nunbers = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩']
        i = 0
        result = root + ':'
        for chardef in self.chardefs:
            for char in self.chardefs[chardef]:
                if char == root:
                    result += '　' + nunbers[i]
                    if i < 9:
                        i = i + 1
                    for str in chardef:
                        result += self.getKeyName(str)

        if result == root + ':':
            result = '查無字根...'
        return result


    def updateCinTable(self, userExtendTable, priorityExtendTable, extendtable, ignorePrivateUseArea):
        if userExtendTable:
            for key in extendtable.chardefs:
                for root in extendtable.chardefs[key]:
                    if priorityExtendTable:
                        i = extendtable.chardefs[key].index(root)
                        try:
                            self.chardefs[key.lower()].insert(i, root)
                        except KeyError:
                            self.chardefs[key.lower()] = [root]
                    else:
                        try:
                            self.chardefs[key.lower()].append(root)
                        except KeyError:
                            self.chardefs[key.lower()] = [root]


    def loadCountFile(self):
        filename = self.getCountFile()
        if os.path.exists(filename) and os.stat(filename).st_size > 0:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        normalized = {}
                        changed = False
                        for key, value in data.items():
                            if not isinstance(key, str) or not isinstance(value, dict):
                                changed = True
                                continue
                            normalized[key] = {}
                            for char, entry in value.items():
                                if not isinstance(char, str):
                                    changed = True
                                    continue
                                normalizedEntry = self._normalizeCountEntry(entry)
                                normalized[key][char] = normalizedEntry
                                if normalizedEntry != entry:
                                    changed = True
                        self.cincount.update(normalized)
                        if changed:
                            self._count_dirty = True
            except Exception:
                pass

    def saveCountFile(self, force=False):
        if not self._count_dirty:
            return
        now = time.time()
        if (
            not force and
            self._last_count_save_time > 0 and
            now - self._last_count_save_time < self.COUNT_SAVE_INTERVAL_SECONDS
        ):
            return
        filename = self.getCountFile()
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.cincount, f, ensure_ascii=False, separators=(",", ":"))
            self._count_dirty = False
            self._last_count_save_time = now
        except Exception:
            pass

    def _trimContextCounts(self, prev, keepKey=""):
        if len(prev) <= self.MAX_CONTEXT_ENTRIES:
            return prev

        items = sorted(prev.items(), key=lambda item: (-item[1], item[0]))
        trimmed = dict(items[:self.MAX_CONTEXT_ENTRIES])
        if keepKey and keepKey in prev and keepKey not in trimmed:
            removable = [key for key in trimmed if key != keepKey]
            if removable:
                dropKey = min(removable, key=lambda key: (trimmed[key], key))
                del trimmed[dropKey]
            trimmed[keepKey] = prev[keepKey]
        return trimmed

    def _normalizeCountEntry(self, value):
        if isinstance(value, dict):
            count = value.get("count", 0)
            try:
                count = int(count)
            except (TypeError, ValueError):
                count = 0
            last = value.get("last", 0)
            try:
                last = float(last)
            except (TypeError, ValueError):
                last = 0
            prev = value.get("prev", {})
            if not isinstance(prev, dict):
                prev = {}
            normalized_prev = {}
            for k, v in prev.items():
                if not isinstance(k, str):
                    continue
                try:
                    normalized_prev[k] = int(v)
                except (TypeError, ValueError):
                    pass
            prev = self._trimContextCounts(normalized_prev)
            return {"count": count, "last": last, "prev": prev}
        try:
            count = int(value)
        except (TypeError, ValueError):
            count = 0
        return {"count": count, "last": 0, "prev": {}}

    def _countEntryScoreParts(self, value, previousChar=""):
        if isinstance(value, dict):
            try:
                count = int(value.get("count", 0))
            except (TypeError, ValueError):
                count = 0
            try:
                last = float(value.get("last", 0))
            except (TypeError, ValueError):
                last = 0
            prevCount = 0
            prev = value.get("prev", {})
            if isinstance(previousChar, str) and previousChar and isinstance(prev, dict):
                try:
                    prevCount = int(prev.get(previousChar, 0))
                except (TypeError, ValueError):
                    prevCount = 0
            return count, last, prevCount

        try:
            count = int(value)
        except (TypeError, ValueError):
            count = 0
        return count, 0, 0

    def addCount(self, key, char, previousChar=""):
        if not isinstance(key, str) or not isinstance(char, str):
            return
        if key not in self.cincount or not isinstance(self.cincount[key], dict):
            self.cincount[key] = {}
        entry = self._normalizeCountEntry(self.cincount[key].get(char, 0))
        entry["count"] += 1
        entry["last"] = time.time()
        if isinstance(previousChar, str) and previousChar:
            entry["prev"][previousChar] = entry["prev"].get(previousChar, 0) + 1
            entry["prev"] = self._trimContextCounts(entry["prev"], previousChar)
        self.cincount[key][char] = entry
        self._count_dirty = True

    def sortByCount(self, key, candidates, previousChar="", useRecent=True, useContext=True):
        if key not in self.cincount or not isinstance(self.cincount[key], dict):
            return candidates
        counts = self.cincount[key]
        now = time.time()

        def score(candidate):
            count, last, prevCount = self._countEntryScoreParts(counts.get(candidate, 0), previousChar)
            value = float(count)
            if useContext and isinstance(previousChar, str) and previousChar:
                value += prevCount * 2.0
            if useRecent and last > 0:
                age_days = max(0.0, (now - last) / 86400.0)
                value += 3.0 / (1.0 + age_days / 7.0)
            return value

        return [candidate for _, candidate in sorted(
            enumerate(candidates),
            key=lambda item: (-score(item[1]), item[0])
        )]


    def getCountDir(self):
        count_dir = os.path.join(os.path.expandvars("%APPDATA%"), "PIME", self.imeDirName)
        os.makedirs(count_dir, exist_ok=True)
        return count_dir


    def getCountFile(self, name="cincount.json"):
        return os.path.join(self.getCountDir(), name)


__all__ = ["Cin"]
