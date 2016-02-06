#! python3
from keycodes import * # for VK_XXX constants
from textService import *
import os.path
from .libchewing import ChewingContext
from .chewing_config import ChewingConfig

# from libchewing/include/global.h
CHINESE_MODE = 1
ENGLISH_MODE = 0
FULLSHAPE_MODE = 1
HALFSHAPE_MODE = 0

# from libchewing/include/internal/userphrase-private.h
DB_NAME	= "chewing.sqlite3"

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

class ChewingTextService(TextService):
    def __init__(self, client):
        TextService.__init__(self, client)
        curdir = os.path.abspath(os.path.dirname(__file__))
        self.datadir = os.path.join(curdir, "data")
        print(self.datadir)
        self.icon_dir = curdir
        
        self.langMode_ = -1
        self.shapeMode_ = -1
        self.outputSimpChinese_ = False
        self.lastKeyDownCode_ = 0

        # load configurations from a user-specific config file
        # FIXME: should we share this among all ChewingTextService instances?
        # FIXME: how to reload the configurations properly when they are changed?
        self.config = ChewingConfig()

    def onActivate(self):
        cfg = self.config
        TextService.onActivate(self)
        # load libchewing context
        datadir = self.datadir.encode("UTF-8")
        user_phrase = os.path.join(cfg.getConfigDir(), DB_NAME).encode("UTF-8")
        ctx = ChewingContext(syspath = datadir, userpath = user_phrase)
        self.ctx = ctx

        ctx.set_maxChiSymbolLen(50)

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

        self.langMode_ = CHINESE_MODE
        ctx.set_ChiEngMode(CHINESE_MODE)

    def setSelKeys(self, selKeys):
        TextService.setSelKeys(self, selKeys)
        self.selKeys = selKeys
        if self.ctx:
            self.ctx.set_selKey(selKeys)

    def onDeactivate(self):
        TextService.onDeactivate(self)
        # unload libchewing context
        self.ctx = None
        self.removeButton("test-btn")

    def filterKeyDown(self, keyEvent):
        self.lastKeyDownCode = keyEvent.keyCode
        # return False if we don't need this key
        if not self.isComposing(): # we're not composing now
            # don't do further handling in English + half shape mode
            if self.langMode_ != CHINESE_MODE and self.shapeMode_ != FULLSHAPE_MODE:
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
            if self.shapeMode_ != FULLSHAPE_MODE:
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
        if keyEvent.isPrintableChar(): # printable characters (exclude extended keys?)
            oldLangMode = ctx.get_ChiEngMode()
            temporaryEnglishMode = False
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

            if self.langMode_ == ENGLISH_MODE: # English mode
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
                ctx.handle_Default(charCode)
                ctx.set_ChiEngMode(oldLangMode) # restore previous mode
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
        # updateLangButtons()

        # if ctx.keystroke_CheckIgnore():
        #    return False

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
        return True

    def onCommand(self, commandId, commandType):
        print("onCommand", commandId, commandType)
