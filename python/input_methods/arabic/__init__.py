#! python3
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import ctypes
import io
import math
import os.path
import threading
import time

from input_methods.arabic.cin import Cin
from keycodes import *  # for VK_XXX constants

ARABIC_MODE = 1
LATIN_MODE = 0

# shift + space Hotkey GUID
SHIFT_SPACE_GUID = "{f1dae0fb-8091-44a7-8a0c-3082a1515447}"
TF_MOD_SHIFT = 0x0004

# command IDs for menu items and language bar buttons
ID_SWITCH_LANG = 1
ID_MODE_ICON = 2
ID_WEBSITE = 3
ID_BUGREPORT = 4
ID_LEXILOGOS = 5
ID_BAHETH = 6
ID_ALMAANY = 7

# Characters (or combinations) that can only be at the end of a word
END_CHARS = ['ة', 'ى', 'ًا', 'ٍ', 'ٌ', 'ةَ', 'ةً', 'ةِ', 'ةٍ', 'ةُ', 'ةٌ', "وا"]
START_CHARS = ['أَ', 'إِ', 'أُ', 'ال']
HARAKAAT = ['َ', 'ِ', 'ُ']
PREFIXES = ['وَ', 'فَ', 'ءَ', 'بِ', 'لَ', 'لِ']
LETTERS = [
    'ا', 'ب', 'ج', 'د', 'ه', 'و', 'ز', 'ح', 'ط', 'ي',
    'ك', 'ل', 'م', 'ن', 'س', 'ع', 'ف', 'ص', 'ق', 'ر',
    'ش', 'ت', 'ث', 'خ', 'ذ', 'ض', 'ظ', 'غ'
]
PUNCTUATION_DICT = {
    ' ': ' ',
    '?': '؟',
    '.': '.',
    ';': '؛',
    ':': ':',
    ",": '،'
}


class CinBase:
    def __init__(self):
        self.cinbasecurdir = os.path.abspath(os.path.dirname(__file__))
        self.icondir = os.path.join(os.path.dirname(__file__), "icons")
        self.candselKeys = "1234567890"

        self.imeNameList = ["arabic"]

    def initTextService(self, cbTS, TextService):
        cbTS.TextService = TextService
        cbTS.TextService.setSelKeys(cbTS, self.candselKeys)

        cbTS.selKeys = "1234567890"
        cbTS.langMode = ARABIC_MODE
        cbTS.messageDurationTime = 3

        cbTS.lastKeyDownCode = 0
        cbTS.lastKeyDownTime = 0.0

        cbTS.currentCandPage = 0

        cbTS.keyUsedState = False
        cbTS.selcandmode = False

        cbTS.initCinBaseState = False
        cbTS.closemenu = True
        cbTS.isSelKeysChanged = False
        cbTS.isLangModeChanged = False
        cbTS.isShowCandidates = False
        cbTS.isShowMessage = False
        cbTS.canSetCommitString = True
        cbTS.canUseSelKey = True
        cbTS.lastCommitString = ""
        cbTS.lastCompositionCharLength = 0

        cbTS.showMessageOnKeyUp = False
        cbTS.hideMessageOnKeyUp = False
        cbTS.onKeyUpMessage = ""
        cbTS.reLoadCinTable = False
        cbTS.capsStates = True if self.getKeyState(VK_CAPITAL) else False

    # When the input method is activated by the user
    def onActivate(self, cbTS):
        cfg = cbTS.cfg
        # Declare to the system that the combination of Shift + Space is of a special purpose
        # When Shift + Space is pressed, onPreservedKey() will be called
        cbTS.addPreservedKey(VK_SPACE, TF_MOD_SHIFT, SHIFT_SPACE_GUID)  # shift + space

        # Switch between arabic and latin
        icon_name = "arabic.ico" if cbTS.langMode == ARABIC_MODE else "latin.ico"
        cbTS.addButton("switch-lang",
                       icon=os.path.join(self.icondir, icon_name),
                       tooltip="Switching language mode",
                       commandId=ID_SWITCH_LANG
                       )

        if cbTS.client.isWindows8Above:
            cbTS.addButton("windows-mode-icon",
                           icon=os.path.join(self.icondir, icon_name),
                           tooltip="Switch language mode (tap shift)",
                           commandId=ID_MODE_ICON
                           )

            # Arabic input is enabled by default at startup
            cbTS.setKeyboardOpen(True)

    # When the input method is deactivated by the user
    def onDeactivate(self, cbTS):
        cbTS.lastKeyDownCode = 0
        # Announce the removal of the key combination Shift + Space to the system
        cbTS.removePreservedKey(SHIFT_SPACE_GUID)  # shift + space

        cbTS.removeButton("switch-lang")
        cbTS.removeButton("settings")
        if cbTS.client.isWindows8Above:
            cbTS.removeButton("windows-mode-icon")

    def filterChar(self, char, previousChar, word, stepSize, position):
        if previousChar in HARAKAAT or previousChar in PREFIXES:
            if char in HARAKAAT:
                return

        if char == previousChar:  # For duplicates
            if previousChar in LETTERS:  # shadda for letters
                char = 'ّ'

        if previousChar == '':  # At the beginning of a word
            if char in HARAKAAT:
                return
        else:  # Not at the beginning of a word
            if char in PREFIXES:
                return
            if char in START_CHARS and not (position == 2 and previousChar in PREFIXES):
                return

        if stepSize < len(word):  # Not at the end of a word
            if char in END_CHARS:
                return

        return char

    def getCandidates(self, cbTS, word, previousChar='', position=0):
        candidates = []
        position = position + 1
        for stepSize in reversed(range(1, len(word) + 1)):
            charset = cbTS.cin.getCharDef(word[0:stepSize])
            if charset:
                for char in charset:
                    char = self.filterChar(char, previousChar, word, stepSize, position)
                    if not char:
                        continue

                    newCandidates = self.getCandidates(cbTS, word[stepSize:], char, position)
                    if newCandidates:
                        for newCandidate in newCandidates:
                            candidates.append(char + newCandidate)
                    else:
                        candidates.append(char)
        return candidates

    # The user presses the keys and filters those keys before the app receives them,
    # which is required by the input method.
    # return True, the system will call onKeyDown() to further process this button.
    # return False, means that we don’t need this key, the system will pass the key to the application intact.
    def filterKeyDown(self, cbTS, keyEvent, CinTable):
        # Record the last key pressed and the time pressed, used in filterKeyUp()
        cbTS.lastKeyDownCode = keyEvent.keyCode
        if cbTS.lastKeyDownTime == 0.0:
            cbTS.lastKeyDownTime = time.time()

        # Don't do any processing if in Latin mode, except for SHIFT, to change language
        if cbTS.langMode == LATIN_MODE and not keyEvent.keyCode == VK_SHIFT:
            if cbTS.isShowMessage:
                cbTS.hideMessageOnKeyUp = True
            return False

        # Don't process the Ctrl or Alt key
        if keyEvent.isKeyDown(VK_CONTROL) or keyEvent.isKeyDown(VK_MENU):
            if cbTS.isShowMessage:
                cbTS.hideMessageOnKeyUp = True
            return False

        # If NumLock is on, don't process any of the NumPad input
        if keyEvent.isKeyToggled(VK_NUMLOCK):  # NumLock is on
            # if this key is Num pad 0-9, +, -, *, /, pass it back to the system
            if VK_NUMPAD0 <= keyEvent.keyCode <= VK_DIVIDE:
                if cbTS.isShowMessage:
                    cbTS.hideMessageOnKeyUp = True
                return False  # bypass IME

        if CinTable.loading:
            return True

        # The user starts to input, the content of the editing area before sending it out is called composition string
        # isComposing() is False, indicating that the editing area is currently empty
        # If you are editing Arabic, we need to send any key to the input method for processing, directly return True
        # In addition, if you use the "`" key to input special symbols, the editing area may be empty
        # But the word selection list is open and the input method needs to be processed
        if cbTS.isComposing() or cbTS.showCandidates:
            return True

        # Process the Shift Key
        if keyEvent.isKeyDown(VK_SHIFT):
            if cbTS.isShowMessage:
                cbTS.hideMessageOnKeyUp = True
            if self.isPunctuationChar(keyEvent.charCode):
                return False
            return True

        # Check whether the pressed key is keyName list
        if cbTS.cin.isInKeyName(chr(keyEvent.charCode)):
            return True

    def onKeyDown(self, cbTS, keyEvent, CinTable):
        # If shift was last pressed, then move on
        if cbTS.lastKeyDownCode == VK_SHIFT and keyEvent.keyCode == VK_SHIFT:
            return True

        if CinTable.loading:
            if not cbTS.client.isUiLess:
                messagestr = 'Loading input method code table, please wait...'
                cbTS.isShowMessage = True
                cbTS.showMessage(messagestr, cbTS.messageDurationTime)
            return True

        keyCode = keyEvent.keyCode
        charCode = keyEvent.charCode
        charStr = chr(charCode)

        cbTS.selKeys = "1234567890"
        if not self.candselKeys == "1234567890":
            self.candselKeys = "1234567890"
            cbTS.TextService.setSelKeys(cbTS, self.candselKeys)
            cbTS.isSelKeysChanged = True

        candidates = []
        cbTS.canSetCommitString = True
        cbTS.keyUsedState = False

        if cbTS.isShowMessage:
            cbTS.isShowMessage = False
            cbTS.hideMessage()

        # Key processing------------------------------------------------ ----------------
        # Certain situations require special treatment or neglect
        # If the input editing area is empty and the menu has not been opened,
        # the Enter and Backspace keys will not be processed
        if not cbTS.isComposing() and cbTS.closemenu:
            if keyCode == VK_RETURN or keyCode == VK_BACK:
                return False

        # The characters in charStr are defined in arabic.json
        if cbTS.cin.isCharactersInKeyName(charStr) and cbTS.closemenu and not cbTS.selcandmode:
            cbTS.compositionChar += charStr

        if cbTS.langMode == ARABIC_MODE and len(cbTS.compositionChar) >= 1:
            if keyCode == VK_ESCAPE and (cbTS.showCandidates or len(cbTS.compositionChar) > 0):
                cbTS.lastCompositionCharLength = 0
                self.resetComposition(cbTS)

            # Delete a letter
            if keyCode == VK_BACK:
                cbTS.compositionChar = cbTS.compositionChar[:-1]
                cbTS.lastCompositionCharLength = cbTS.lastCompositionCharLength - 1
                cbTS.setCandidateCursor(0)
                cbTS.setCandidatePage(0)
                if cbTS.compositionChar == '':
                    self.resetComposition(cbTS)

            # Group word exceeds maximum
            if len(cbTS.compositionChar) > cbTS.maxCharLength:
                if cbTS.cin.isCharactersInKeyName(cbTS.compositionChar[len(cbTS.compositionChar) - 1:]):
                    keyLength = len(cbTS.cin.getKeyName(cbTS.compositionChar[len(cbTS.compositionChar) - 1:]))
                else:
                    keyLength = 1
                cbTS.setCompositionString(cbTS.compositionString[:-keyLength])
                cbTS.compositionChar = cbTS.compositionChar[:-1]

            if cbTS.cin.isCharactersInKeyName(cbTS.compositionChar) and cbTS.closemenu:
                candidates = [cbTS.compositionChar]
                candidates.extend(self.getCandidates(cbTS, cbTS.compositionChar))

        # Candidate list processing
        if cbTS.langMode == ARABIC_MODE and len(cbTS.compositionChar) >= 1:
            if candidates:
                if not cbTS.selcandmode:
                    cbTS.isShowCandidates = True
                    cbTS.canSetCommitString = True

                if cbTS.isShowCandidates:
                    candCursor = cbTS.candidateCursor  # Current cursor position
                    candCount = len(cbTS.candidateList)  # Number of items in the current word selection list
                    # The total number of pages of the current word selection list
                    currentCandPageCount = math.ceil(len(candidates) / cbTS.candPerPage)
                    currentCandPage = cbTS.currentCandPage  # Current number of pages in the word selection list

                    pagecandidates = list(self.chunks(candidates, cbTS.candPerPage))
                    cbTS.setCandidateList(pagecandidates[currentCandPage])

                    if not cbTS.isSelKeysChanged:
                        cbTS.setShowCandidates(True)

                if cbTS.isShowCandidates:
                    # Use the word selection keys to execute items or output candidates
                    if self.isInSelKeys(cbTS, charCode) and not keyEvent.isKeyDown(VK_SHIFT) and cbTS.canUseSelKey:
                        i = cbTS.selKeys.index(charStr)
                        if i < cbTS.candPerPage and i < len(cbTS.candidateList):
                            commitStr = cbTS.candidateList[i]
                            cbTS.lastCommitString = commitStr
                            self.setOutputString(cbTS, commitStr)
                            self.resetComposition(cbTS)
                            candCursor = 1
                            currentCandPage = 0

                    elif keyCode == VK_UP:
                        if (candCursor - cbTS.candPerRow) < 0:
                            if currentCandPage > 0:
                                currentCandPage -= 1
                                candCursor = 1
                        else:
                            if (candCursor - cbTS.candPerRow) >= 0:
                                candCursor = candCursor - cbTS.candPerRow
                    elif keyCode == VK_DOWN and cbTS.canSetCommitString:
                        if (candCursor + cbTS.candPerRow) >= cbTS.candPerPage:
                            if (currentCandPage + 1) < currentCandPageCount:
                                currentCandPage += 1
                                candCursor = 1
                        else:
                            if (candCursor + cbTS.candPerRow) < len(pagecandidates[currentCandPage]):
                                candCursor = candCursor + cbTS.candPerRow
                    elif keyCode == VK_LEFT:
                        if candCursor > 0:
                            candCursor -= 1
                        else:
                            if currentCandPage > 0:
                                currentCandPage -= 1
                                candCursor = 1
                    elif keyCode == VK_RIGHT:
                        if (candCursor + 1) < candCount:
                            candCursor += 1
                        else:
                            if (currentCandPage + 1) < currentCandPageCount:
                                currentCandPage += 1
                                candCursor = 1
                    elif keyCode == VK_HOME:
                        candCursor = 1
                    elif keyCode == VK_END:
                        candCursor = len(pagecandidates[currentCandPage]) - 1
                    elif keyCode == VK_PRIOR:
                        if currentCandPage > 0:
                            currentCandPage -= 1
                            candCursor = 1
                    elif keyCode == VK_NEXT:
                        if (currentCandPage + 1) < currentCandPageCount:
                            currentCandPage += 1
                            candCursor = 1
                    elif ((self.isPunctuationChar(charCode) or keyCode == VK_RETURN)
                          and not cbTS.cin.isInKeyName(charStr)) and cbTS.canSetCommitString:
                        commitStr = cbTS.candidateList[candCursor]
                        if self.isPunctuationChar(keyEvent.charCode):
                            commitStr = commitStr + PUNCTUATION_DICT.get(chr(keyEvent.charCode), chr(keyEvent.charCode))
                        cbTS.lastCommitString = commitStr
                        self.setOutputString(cbTS, commitStr)
                        self.resetComposition(cbTS)
                        candCursor = 1
                        currentCandPage = 0

                    # Press other keys to reset the cursor address of the candidate word
                    # and the current page number to zero
                    else:
                        candCursor = 1
                        currentCandPage = 0
                    # Update the cursor position and page number of the word selection window
                    cbTS.setCandidateCursor(candCursor)
                    cbTS.setCandidatePage(currentCandPage)
                    cbTS.setCandidateList(pagecandidates[currentCandPage])
            else:  # No candidates
                cbTS.setShowCandidates(False)
                cbTS.isShowCandidates = False

        if not cbTS.closemenu:
            cbTS.closemenu = True

        return True

    # The user releases the keys and filters those keys before the app receives them,
    # which is required by the input method.
    # return True, the system will call onKeyUp() to further process the key
    # return False, means we don’t need this key, the system will pass the key to the application intact
    def filterKeyUp(self, cbTS, keyEvent):
        if cbTS.lastKeyDownCode == VK_SHIFT and keyEvent.keyCode == VK_SHIFT:
            if (time.time() - cbTS.lastKeyDownTime) < 0.5:
                cbTS.isLangModeChanged = True
                return True

        # Regardless of the Arabic or Latin mode, as long as you release the CapsLock key,
        # the input method needs to be processed
        if cbTS.lastKeyDownCode == VK_CAPITAL and keyEvent.keyCode == VK_CAPITAL:
            return True

        cbTS.lastKeyDownCode = 0
        cbTS.lastKeyDownTime = 0.0

        if cbTS.isSelKeysChanged:
            return True

        if cbTS.showMessageOnKeyUp:
            return True

        if cbTS.hideMessageOnKeyUp:
            return True

        return False

    def onKeyUp(self, cbTS, keyEvent):
        keyCode = keyEvent.keyCode
        cbTS.lastKeyDownCode = 0
        cbTS.lastKeyDownTime = 0.0

        # If you release the Shift key then trigger Switch language mode
        if cbTS.isLangModeChanged and keyCode == VK_SHIFT:
            self.toggleLanguageMode(cbTS)  # Switch between Arabic and Latin mode
            cbTS.isLangModeChanged = False
            if cbTS.showCandidates or len(cbTS.compositionChar) > 0:
                self.resetComposition(cbTS)

        # If you release the CapsLock key
        if keyEvent.keyCode == VK_CAPITAL:
            self.updateLangButtons(cbTS)

        if cbTS.isSelKeysChanged:
            cbTS.setCandidateList(cbTS.candidateList)
            if cbTS.isShowCandidates:
                cbTS.setShowCandidates(True)
            cbTS.isSelKeysChanged = False

        if cbTS.showMessageOnKeyUp:
            if not cbTS.onKeyUpMessage == "" and not cbTS.client.isUiLess:
                cbTS.showMessage(cbTS.onKeyUpMessage, cbTS.messageDurationTime)
            cbTS.showMessageOnKeyUp = False
            cbTS.onKeyUpMessage = ""

        if cbTS.hideMessageOnKeyUp:
            cbTS.hideMessage()
            cbTS.isShowMessage = False
            cbTS.hideMessageOnKeyUp = False

    def onPreservedKey(self, cbTS, guid):
        cbTS.lastKeyDownCode = 0
        # some preserved keys registered are pressed
        return False

    def onCommand(self, cbTS, commandId, commandType):
        if commandId == ID_SWITCH_LANG and commandType == 0:  # Switch between Arabic and Latin mode
            self.toggleLanguageMode(cbTS)
        elif commandId == ID_MODE_ICON:  # windows 8 mode icon
            self.toggleLanguageMode(cbTS)
        elif commandId == ID_WEBSITE:
            os.startfile("https://github.com/ArabicIME/arabic-ime")
        elif commandId == ID_BUGREPORT:
            os.startfile("https://github.com/ArabicIME/arabic-ime/issues")
        elif commandId == ID_LEXILOGOS:
            os.startfile("https://www.lexilogos.com/english/arabic_dictionary.htm")
        elif commandId == ID_BAHETH:
            os.startfile("http://www.baheth.info")
        elif commandId == ID_ALMAANY:
            os.startfile("https://www.almaany.com/en/dict/ar-en/")

    def onMenu(self, cbTS, buttonId):
        # (windows 8 mode icon)
        if buttonId == "settings" or buttonId == "windows-mode-icon":
            return [
                {"text": "ArabicIME (&W)", "id": ID_WEBSITE},
                {},
                {"text": "ArabicIME Bug Report (&B)", "id": ID_BUGREPORT},
                {},
                {"text": "Dictionaries (&D)", "submenu": [
                    {"text": "Lexilogos", "id": ID_LEXILOGOS},
                    {},
                    {"text": "الباحِثُ العَرَبيُّ", "id": ID_BAHETH},
                    {"text": "المَعاني", "id": ID_ALMAANY},
                ]},
            ]
        return None

    # Called when the keyboard is turned on/off (in Windows 10 Ctrl+Space)
    def onKeyboardStatusChanged(self, cbTS, opened):
        if opened:
            self.resetComposition(cbTS)
        else:
            self.resetComposition(cbTS)

        # Windows 8 systray IME mode icon
        if cbTS.client.isWindows8Above:
            # If the keyboard is turned off, we need to set the windows 8 mode icon to disabled
            cbTS.changeButton("windows-mode-icon", enable=opened)
        # FIXME: Do I need to disable other language column buttons at the same time?

    # It will be called when the editing terminates. If the editing did not end normally
    # because the user switched to other applications or other reasons, then
    # the forced parameter will be True, in this case, some buffers need to be cleared
    def onCompositionTerminated(self, cbTS, forced):
        self.resetComposition(cbTS)

    # Switch between Arabic and Latin mode
    def toggleLanguageMode(self, cbTS):
        if cbTS.langMode == ARABIC_MODE:
            cbTS.langMode = LATIN_MODE
        elif cbTS.langMode == LATIN_MODE:
            cbTS.langMode = ARABIC_MODE
        self.updateLangButtons(cbTS)

    def updateLangButtons(self, cbTS):
        icon_name = "arabic.ico" if cbTS.langMode == ARABIC_MODE else "latin.ico"
        icon_path = os.path.join(self.icondir, icon_name)
        cbTS.changeButton("switch-lang", icon=icon_path)
        cbTS.capsStates = True if self.getKeyState(VK_CAPITAL) else False
        icon_path = os.path.join(self.icondir, icon_name)

        if cbTS.client.isWindows8Above:  # windows 8 mode icon
            cbTS.changeButton("windows-mode-icon", icon=icon_path)

    def resetComposition(self, cbTS):
        cbTS.compositionChar = ''
        cbTS.setCompositionString('')
        cbTS.isShowCandidates = False
        cbTS.setCandidateCursor(0)
        cbTS.setCandidatePage(0)
        cbTS.setCandidateList([])
        cbTS.setShowCandidates(False)
        cbTS.selcandmode = False
        cbTS.lastCompositionCharLength = 0

    def isPunctuationChar(self, keyCode):
        return 32 <= keyCode <= 47 or 58 <= keyCode <= 64

    def isInSelKeys(self, cbTS, charCode):
        for key in cbTS.selKeys:
            if ord(key) == charCode:
                return True
        return False

    # Page candidates
    def chunks(self, l, n):
        for i in range(0, len(l), n):
            yield l[i:i + n]

    def getKeyState(self, keyCode):
        return ctypes.WinDLL("User32.dll").GetKeyState(keyCode)

    def setOutputString(self, cbTS, commitStr):
        cbTS.setCommitString(commitStr)

    ################################################################
    # config
    ################################################################
    # Initialize the CinBase input method engine
    def initCinBaseContext(self, cbTS):
        cfg = cbTS.cfg  # All TextServices share a configuration object

        if not cbTS.initCinBaseState:
            cbTS.langMode = LATIN_MODE if cfg.defaultLatin else ARABIC_MODE
            self.updateLangButtons(cbTS)

        self.applyConfig(cbTS)  # Apply the remaining user settings

        cbTS.initCinBaseState = True

    def applyConfig(self, cbTS):
        cfg = cbTS.cfg  # All TextService share a configuration object
        cbTS.configVersion = cfg.getVersion()

        # Number of candidates in each column
        cbTS.candPerRow = cfg.candPerRow

        # If the program is in UiLess mode, replace the setting
        if cbTS.client.isUiLess:
            cbTS.candPerRow = 1

        # Number of candidates per page
        cbTS.candPerPage = cfg.candPerPage

        # Set UI appearance
        cbTS.customizeUI(candFontSize=cfg.fontSize,
                         candFontName='Segoe UI',
                         candPerRow=cfg.candPerRow,
                         candUseCursor=cfg.cursorCandList)

        cbTS.messageDurationTime = cfg.messageDurationTime

    # Check whether the configuration file has been changed and whether the new setting needs to be applied
    def checkConfigChange(self, cbTS, CinTable):
        cfg = cbTS.cfg  # All TextServices share a configuration object
        cfg.update()  # Update profile status
        reLoadCinTable = False

        if cfg.isConfigChanged(cbTS.configVersion):
            # Only when profile changes are detected, new settings need to be applied
            self.applyConfig(cbTS)

        if reLoadCinTable:
            if reLoadCinTable:
                cbTS.reLoadCinTable = True
            loadCinFile = LoadCinTable(cbTS, CinTable)
            loadCinFile.start()
        else:
            if not cbTS.cin == CinTable.cin:
                cbTS.cin = CinTable.cin


CinBase = CinBase()


class LoadCinTable(threading.Thread):
    def __init__(self, cbTS, CinTable):
        threading.Thread.__init__(self)
        self.cbTS = cbTS
        self.CinTable = CinTable

    def run(self):
        self.CinTable.loading = True
        selCinFile = self.cbTS.cinFile
        jsonPath = os.path.join(self.cbTS.jsondir, selCinFile)

        if self.cbTS.reLoadCinTable or not hasattr(self.cbTS, 'cin'):
            self.cbTS.reLoadCinTable = False

            if hasattr(self.cbTS, 'cin'):
                self.cbTS.cin.__del__()
            if hasattr(self.CinTable.cin, '__del__'):
                self.CinTable.cin.__del__()

            self.cbTS.cin = None
            self.CinTable.cin = None

            with io.open(jsonPath, 'r', encoding='utf8') as fs:
                self.cbTS.cin = Cin(fs, self.cbTS.imeDirName)
            self.CinTable.cin = self.cbTS.cin

        self.CinTable.loading = False
