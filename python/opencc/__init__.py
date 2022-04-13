# python3
# Simple Python 3 binding for OpenCC library developed by BYVoid <byvoid@byvoid.com>
#
# Copyright 2016 (C) Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os, sys
from ctypes import CDLL, c_char_p

OPENCC_DEFAULT_CONFIG_SIMP_TO_TRAD = "s2t.json"
OPENCC_DEFAULT_CONFIG_TRAD_TO_SIMP = "t2s.json"

_opencc_dir = os.path.dirname(__file__)
if sys.platform == "win32": # Windows
    _libopencc = CDLL(os.path.join(_opencc_dir, "opencc.dll"))
else: # UNIX-like systems
    _libopencc = CDLL("libopencc.so")
_libopencc.opencc_error.restype = c_char_p

class OpenCC:
    def __init__(self, configName):
        if not os.path.isabs(configName):
            configName = os.path.join(_opencc_dir, configName)
        self.opencc = _libopencc.opencc_open(bytes(configName, "ascii"))
        print(self.opencc)

    def convert(self, from_str):
        result = ""
        input_data = bytes(from_str, "UTF-8")
        result_p = _libopencc.opencc_convert_utf8(self.opencc, input_data, len(input_data))
        print(result_p)
        if result_p:
            result = c_char_p(result_p).value.decode("UTF-8")
            _libopencc.opencc_convert_utf8_free(result_p)
        return result

    def get_error(self):
        return _libopencc.opencc_error()

    def __del__(self):
        _libopencc.opencc_close(self.opencc)
