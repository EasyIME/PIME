#! python3
# Copyright (C) 2015 - 2016 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
#
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

from keycodes import * # for VK_XXX constants
from textService import *
import os.path
import time
from .libchewing import ChewingContext
from .chewing_config import chewingConfig

# from libchewing/include/global.h
CHINESE_MODE = 1
ENGLISH_MODE = 0
FULLSHAPE_MODE = 1
HALFSHAPE_MODE = 0

keyNames = {
    VK_ESCAPE: "Esc",
    VK_RETURN: "Enter",
    VK_TAB: "Tab",
    VK_DELETE: "Del",
    VK_BACK: "Backspace",
    VK_UP: "Up",
    VK_DOWN: "Down",
    VK_LEFT: "Left",
    VK_RIGHT: "Right",
    VK_HOME: "Home",
    VK_END: "End",
    VK_PRIOR: "PageUp",
    VK_NEXT: "PageDown"
}

SHIFT_SPACE_GUID = "{F1DAE0FB-8091-44A7-8A0C-3082A1515447}"
ID_SWITCH_LANG = 1
ID_SWITCH_SHAPE = 2
ID_SETTINGS = 3
ID_MODE_ICON = 4

class ChewingTextService(TextService):
    def __init__(self, client):
        TextService.__init__(self, client)
        self.curdir = os.path.abspath(os.path.dirname(__file__))
        self.datadir = os.path.join(self.curdir, "data")
        # print(self.datadir)
        self.icon_dir = self.curdir
        self.ctx = None # libchewing context

        self.langMode = -1
        self.shapeMode = -1
        self.outputSimpChinese = False
        self.lastKeyDownCode = 0
        self.lastKeyDownTime = 0.0
        self.configTimeStamp = chewingConfig.lastTime

    # check whether the config file is changed and reload it as needed
    def checkConfigChange(self):
        chewingConfig.reloadIfNeeded()
        if self.configTimeStamp != chewingConfig.lastTime:
            # configurations are changed
            self.applyConfig()

    def applyConfig(self):
        cfg = chewingConfig # globally shared config object
        self.configTimeStamp = cfg.lastTime
        ctx = self.ctx

        # add user phrase before or after the cursor
        ctx.set_addPhraseDirection(cfg.addPhraseForward);

        # automatically shift cursor to the next char after choosing a candidate
        ctx.set_autoShiftCur(cfg.advanceAfterSelection);

        # candiate strings per page
        ctx.set_candPerPage(cfg.candPerPage);

        # clean the composition buffer by Esc key
        ctx.set_escCleanAllBuf(cfg.escCleanAllBuf);

        # keyboard type
        ctx.set_KBType(cfg.keyboardLayout);

        # Use space key to open candidate window.
        ctx.set_spaceAsSelection(cfg.showCandWithSpaceKey);

        self.customizeUI(candFontSize = cfg.fontSize, candPerRow = cfg.candPerRow)
        self.setSelKeys(cfg.getSelKeys())

    def initChewingContext(self):
        # load libchewing context
        if not self.ctx:
            cfg = chewingConfig # globally shared config object
            datadir = self.datadir.encode("UTF-8")
            user_phrase = cfg.getUserPhrase().encode("UTF-8")
            ctx = ChewingContext(syspath = datadir, userpath = user_phrase)
            self.ctx = ctx
            ctx.set_maxChiSymbolLen(50)

            self.langMode = ENGLISH_MODE if cfg.defaultEnglish else CHINESE_MODE
            ctx.set_ChiEngMode(self.langMode)

            self.shapeMode = FULLSHAPE_MODE if cfg.defaultFullSpace else HALFSHAPE_MODE
            ctx.set_ShapeMode(self.shapeMode)

        self.applyConfig()

    def onActivate(self):
        cfg = chewingConfig # globally shared config object
        TextService.onActivate(self)
        self.initChewingContext()

        # add preserved keys
        self.addPreservedKey(VK_SPACE, TF_MOD_SHIFT, SHIFT_SPACE_GUID); # shift + space

        # add language bar buttons
        # siwtch Chinese/English modes
        icon_name = "chi.ico" if self.langMode == CHINESE_MODE else "eng.ico"
        self.addButton("switch-lang",
            icon = os.path.join(self.icon_dir, icon_name),
            tooltip = "中英文切換",
            commandId = ID_SWITCH_LANG
        )
        # Windows 8 systray IME mode icon
        if self.client.isWindows8Above:
            self.addButton("windows-mode-icon",
                icon = os.path.join(self.icon_dir, icon_name),
                commandId = ID_MODE_ICON
            )
        
        # toggle full shape/half shape
        icon_name = "full.ico" if self.shapeMode == FULLSHAPE_MODE else "half.ico"
        self.addButton("switch-shape",
            icon = os.path.join(self.icon_dir, icon_name),
            tooltip = "全形/半形切換",
            commandId = ID_SWITCH_SHAPE
        )

        # settings and others, may open a popup menu
        # FIXME: popup menu is not yet implemented
        self.addButton("settings",
            icon = os.path.join(self.icon_dir, "config.ico"),
            tooltip = "設定",
            commandId = ID_SETTINGS
        )

    def onDeactivate(self):
        TextService.onDeactivate(self)
        # unload libchewing context
        self.ctx = None
        self.lastKeyDownCode = 0

        self.removeButton("switch-lang")
        self.removeButton("switch-shape")
        self.removeButton("settings")
        if self.client.isWindows8Above:
            self.removeButton("windows-mode-icon")

    def setSelKeys(self, selKeys):
        TextService.setSelKeys(self, selKeys)
        self.selKeys = selKeys
        if self.ctx:
            self.ctx.set_selKey(selKeys)

    def filterKeyDown(self, keyEvent):
        self.lastKeyDownCode = keyEvent.keyCode
        if self.lastKeyDownTime == 0.0:
            self.lastKeyDownTime = time.time()
        # return False if we don't need this key
        if not self.isComposing(): # we're not composing now
            # don't do further handling in English + half shape mode
            if self.langMode != CHINESE_MODE and self.shapeMode != FULLSHAPE_MODE:
                return False

            # if Ctrl or Alt key is down
            if keyEvent.isKeyDown(VK_CONTROL) or keyEvent.isKeyDown(VK_MENU):
                # bypass IME. This might be a shortcut key used in the application
                # FIXME: we only need Ctrl in composition mode for adding user phrases.
                # However, if we turn on easy symbol input with Ctrl support later,
                # we'll need th Ctrl key then.
                return False

            # we always need further processing in full shape mode since all English chars,
            # numbers, and symbols need to be converted to full shape Chinese chars.
            if self.shapeMode != FULLSHAPE_MODE:
                # Caps lock is on => English mode
                # if cfg.enableCapsLock and keyEvent.isKeyToggled(VK_CAPITAL):
                if keyEvent.isKeyToggled(VK_CAPITAL):
                    # We need to handle this key because in onKeyDown(),
                    # the upper case chars need to be converted to lower case
                    # before doing output to the applications.
                    if keyEvent.isChar() and chr(keyEvent.charCode).isalpha():
                        return True # this is an English alphabet
                    else:
                        return False

                if keyEvent.isKeyToggled(VK_NUMLOCK): # NumLock is on
                    # if this key is Num pad 0-9, +, -, *, /, pass it back to the system
                    if keyEvent.keyCode >= VK_NUMPAD0 and keyEvent.keyCode <= VK_DIVIDE:
                        return False # bypass IME
            else: # full shape mode
                if keyEvent.keyCode == VK_SPACE: # we need to convert space to fullshape.
                    return True

            # when not composing, we only cares about Bopomofo
            # FIXME: we should check if the key is mapped to a phonetic symbol instead
            if keyEvent.isPrintableChar(includingSpace = True):
                # this is a key mapped to a printable charStr. we want it!
                return True
            return False
        return True

    def onKeyDown(self, keyEvent):
        ctx = self.ctx
        charCode = keyEvent.charCode
        charStr = chr(charCode)
        temporaryEnglishMode = False
        oldLangMode = ctx.get_ChiEngMode()

        """ // What's easy symbol input??
            // set this to true or false according to the status of Shift key
            // alternatively, should we set this when onKeyDown and onKeyUp receive VK_SHIFT or VK_CONTROL?
            bool easySymbols = false;
            if(cfg.easySymbolsWithShift)
                easySymbols = keyEvent.isKeyDown(VK_SHIFT);
            if(!easySymbols && cfg.easySymbolsWithCtrl)
                easySymbols = keyEvent.isKeyDown(VK_CONTROL);
            ::chewing_set_easySymbolInput(chewingContext_, easySymbols);
        """
        if keyEvent.isPrintableChar(): # printable characters (exclude extended keys?)
            invertCase = False
            # If Caps lock is on, temporarily change to English mode
            # if cfg.enableCapsLock and keyEvent.isKeyToggled(VK_CAPITAL):
            if keyEvent.isKeyToggled(VK_CAPITAL):
                temporaryEnglishMode = True
                invertCase = True # need to convert upper case to lower, and vice versa.

            # If Shift is pressed, but we don't want to enter full shape symbols
            # if keyEvent.isKeyDown(VK_SHIFT) and (cfg.fullShapeSymbols or isalpha(charCode)):
            if keyEvent.isKeyDown(VK_SHIFT) and charStr.isalpha():
                temporaryEnglishMode = True
                # if !cfg.upperCaseWithShift)
                #    invertCase = True # need to convert upper case to lower, and vice versa.

            if self.langMode == ENGLISH_MODE: # English mode
                ctx.handle_Default(charCode)
            elif temporaryEnglishMode: # temporary English mode
                ctx.set_ChiEngMode(ENGLISH_MODE) # change to English mode temporarily
                if invertCase: # need to invert upper case and lower case
                    # we're NOT in real English mode, but Capslock is on, so we treat it as English mode
                    # reverse upper and lower case
                    if charStr.isupper():
                        charCode = ord(charStr.lower())
                    else:
                        charCode = ord(charStr.upper())
                print("temp English", charCode)
                ctx.handle_Default(charCode)
            else : # Chinese mode
                if charStr.isalpha(): # alphabets: A-Z
                    ctx.handle_Default(ord(charStr.lower()))
                elif keyEvent.keyCode == VK_SPACE: # space key
                    ctx.handle_Space()
                elif keyEvent.isKeyDown(VK_CONTROL) and charStr.isdigit(): # Ctrl + number (0~9)
                    ctx.handle_CtrlNum(charCode)
                elif keyEvent.isKeyToggled(VK_NUMLOCK) and keyEvent.keyCode >= VK_NUMPAD0 and keyEvent.keyCode <= VK_DIVIDE:
                    # numlock is on, handle numpad keys
                    ctx.handle_Numlock(charCode)
                else : # other keys, no special handling is needed
                    ctx.handle_Default(charCode)
        else: # non-printable keys
            keyHandled = False
            # if we want to use the arrow keys to select candidate strings
            '''
            if config().cursorCandList and showingCandidates() and candidateWindow_:
                # if the candidate window is open, let it handle the key first
                if candidateWindow_->filterKeyEvent(keyEvent):
                    # the user selected a string from the candidate list already
                    if candidateWindow_->hasResult():
                        wchar_t selKey = candidateWindow_->currentSelKey()
                        # pass the selKey to libchewing.
                        ctx.handle_Default(selKey)
                        keyHandled = True
                    
                    else # no candidate has been choosen yet
                        return True # eat the key and don't pass it to libchewing at all
            '''
            if not keyHandled:
                # the candidate window does not need the key. pass it to libchewing.
                keyName = keyNames.get(keyEvent.keyCode)
                if keyName: # call libchewing method for the key
                    methodName = "handle_" + keyName
                    getattr(ctx, methodName)()
                else: # we don't know this key. ignore it!
                    return False

        self.updateLangButtons()

        if ctx.keystroke_CheckIgnore():
            if temporaryEnglishMode:
                ctx.set_ChiEngMode(oldLangMode) # restore previous mode
            return False

        # handle candidates
        if ctx.cand_TotalChoice() > 0: # has candidates
            # FIXME: avoid updating candidate list everytime if it's not changed
            candidates = []
            ctx.cand_Enumerate()
            n = ctx.cand_ChoicePerPage(); # candidate string shown per page
            for i in range(0, n):
                if not ctx.cand_hasNext():
                    break
                cand = ctx.cand_String().decode("UTF-8")
                candidates.append(cand)
            self.setCandidateList(candidates)
            if not self.showCandidates:
                self.setShowCandidates(True)
        else:
            if self.showCandidates:
                self.setShowCandidates(False)

        # has something to commit
        if ctx.commit_Check():
            commitStr = ctx.commit_String().decode("UTF-8")
            # commit the text, replace currently selected text with our commit string
            self.setCommitString(commitStr)
            print("commit:", commitStr)

        # composition string
        compStr = ""
        if ctx.buffer_Check():
            compStr = ctx.buffer_String().decode("UTF-8")

        if ctx.bopomofo_Check():
            bopomofoStr = ""
            bopomofoStr = ctx.bopomofo_String(None).decode("UTF-8")
            # put bopomofo symbols at insertion point
            pos = ctx.cursor_Current()
            compStr = compStr[:pos] + bopomofoStr + compStr[pos:]
        print("compStr:", compStr)
        self.setCompositionString(compStr)
        # update cursor pos
        self.setCompositionCursor(ctx.cursor_Current())
        '''
        # show aux info
        if ctx.aux_Check():
            char* str = ctx.aux_String()
            std::wstring wstr = utf8ToUtf16(str)
            ctx.free(str)
            # show the message to the user
            # FIXME: sometimes libchewing shows the same aux info
            # for subsequent key events... I think this is a bug.
            showMessage(session, wstr, 2)
        '''
        if temporaryEnglishMode:
            ctx.set_ChiEngMode(oldLangMode) # restore previous mode

        return True

    def filterKeyUp(self, keyEvent):
        if chewingConfig.switchLangWithShift:
            if self.lastKeyDownCode == VK_SHIFT and keyEvent.keyCode == VK_SHIFT:
                # last key down event is also shift key
                # a <Shift> key down + key up pair was detected switch language
                pressedDuration = time.time() - self.lastKeyDownTime
                if pressedDuration < 0.5: # pressed for < 0.5 second
                    self.toggleLanguageMode()
        self.lastKeyDownCode = 0
        self.lastKeyDownTime = 0.0
        return False

    def onPreservedKey(self, guid):
        self.lastKeyDownCode = 0;
        # some preserved keys registered are pressed
        if guid == SHIFT_SPACE_GUID: # shift + space is pressed
            toggleShapeMode()
            return True
        return False
        
    def onCommand(self, commandId, commandType):
        print("onCommand", commandId, commandType)
        # FIXME: We should distinguish left and right click using commandType
        if commandId == ID_SWITCH_LANG:
            self.toggleLanguageMode()
        elif commandId == ID_SWITCH_SHAPE:
            self.toggleShapeMode()
        elif commandId == ID_SETTINGS:
            # launch our configuration tool
            # Luckily, there is a Windows-only python call for it
            config_tool = os.path.join(self.curdir, "config", "config.hta")
            os.startfile(config_tool)
        elif commandId == ID_MODE_ICON: # windows 8 mode icon
            self.toggleLanguageMode()

    def updateLangButtons(self):
        ctx = self.ctx
        if not ctx:
            return
        langMode = ctx.get_ChiEngMode()
        if langMode != self.langMode:
            self.langMode = langMode
            icon_name = "chi.ico" if langMode == CHINESE_MODE else "eng.ico"
            icon_path = os.path.join(self.icon_dir, icon_name)
            self.changeButton("switch-lang", icon=icon_path)

            if self.client.isWindows8Above: # windows 8 mode icon
                # FIXME: we need a better set of icons to meet the 
                #        WIndows 8 IME guideline and UX guidelines.
                self.changeButton("windows-mode-icon", icon=icon_path)

        shapeMode = ctx.get_ShapeMode()
        if shapeMode != self.shapeMode:
            self.shapeMode = shapeMode
            icon_name = "full.ico" if shapeMode == FULLSHAPE_MODE else "half.ico"
            icon_path = os.path.join(self.icon_dir, icon_name)
            self.changeButton("switch-shape", icon=icon_path)

    #toggle between English and Chinese
    def toggleLanguageMode(self):
        ctx = self.ctx
        if ctx:
            if ctx.get_ChiEngMode() == CHINESE_MODE:
                new_mode = ENGLISH_MODE
            else:
                new_mode = CHINESE_MODE
            ctx.set_ChiEngMode(new_mode)
            self.updateLangButtons()

    # toggle between full shape and half shape
    def toggleShapeMode(self):
        ctx = self.ctx
        if ctx:
            if ctx.get_ShapeMode() == HALFSHAPE_MODE:
                new_mode = FULLSHAPE_MODE
            else:
                new_mode = HALFSHAPE_MODE
            ctx.set_ShapeMode(new_mode)
            self.updateLangButtons()

    # called when the keyboard is opened or closed
    def onKeyboardStatusChanged(self, opened):
        TextService.onKeyboardStatusChanged(self, opened)
        if opened: # keyboard is opened
            self.initChewingContext()
        else: # keyboard is closed
            if self.showCandidates: # disable candidate window if it's opened
                self.setShowCandidates(False)
            # self.hideMessage() # hide message window, if there's any
            # self.freeChewingContext(); # IME is closed, chewingContext is not needed

        # Windows 8 systray IME mode icon
        if self.client.isWindows8Above:
            self.changeButton("windows-mode-icon", enable=opened)
        # FIXME: should we also disable other language bar buttons as well?

    # called just before current composition is terminated for doing cleanup.
    # if forced is true, the composition is terminated by others, such as
    # the input focus is grabbed by another application.
    # if forced is false, the composition is terminated gracefully.
    def onCompositionTerminated(self, forced):
        TextService.onCompositionTerminated(self, forced)
        # we do special handling here for forced composition termination.
        if forced:
            # we're still editing our composition and have something in the preedit buffer.
            # however, some other applications grabs the focus and force us to terminate
            # our composition.
            ctx = self.ctx
            if ctx:
                if self.showCandidates:
                    ctx.cand_close()
                if ctx.bopomofo_Check():
                    ctx.clean_bopomofo_buf()
                if ctx.buffer_Check():
                    ctx.commit_preedit_buf()
