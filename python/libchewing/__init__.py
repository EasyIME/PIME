import os

from .libchewing import ChewingContext

_current_dir = os.path.dirname(__file__)

CHEWING_DATA_DIR = os.path.join(_current_dir, "data")

# from libchewing/include/global.h
CHINESE_MODE = 1
ENGLISH_MODE = 0
FULLSHAPE_MODE = 1
HALFSHAPE_MODE = 0
