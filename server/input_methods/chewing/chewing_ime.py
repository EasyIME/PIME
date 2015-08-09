#! python3
from win32con import * # for VK_XXX constants
from ..textService import *
import os.path
from .libchewing import * # FIXME: we cannot do import libchewing directly. why?

class ChewingTextService(TextService):
    def __init__(self, client):
        TextService.__init__(self, client)
        curdir = os.path.abspath(os.path.dirname(__file__))
        self.datadir = os.path.join(curdir, "data")
        self.icon_dir = curdir

    def onActivate(self):
        TextService.onActivate(self)
        # load libchewing context
        ctx = ChewingContext(syspath = self.datadir)
        self.ctx = ctx

        ctx.set_maxChiSymbolLen(50)

        # add user phrase before or after the cursor
        # cxt.set_addPhraseDirection(chewingContext_, cfg.addPhraseForward);

        # automatically shift cursor to the next char after choosing a candidate
        # ctx.set_autoShiftCur(chewingContext_, cfg.advanceAfterSelection);

        # candiate strings per page
        # ctx.set_candPerPage(chewingContext_, cfg.candPerPage);

        # clean the composition buffer by Esc key
        # ctx.set_escCleanAllBuf(chewingContext_, cfg.escCleanAllBuf);

        # keyboard type
        # ctx.set_KBType(chewingContext_, cfg.keyboardLayout);

        # Use space key to open candidate window.
        # ctx.set_spaceAsSelection(chewingContext_, cfg.showCandWithSpaceKey);

        self.customizeUI(candFontSize = 20, candPerRow = 1)
        self.selKeys = "1234567890"
        ctx.set_selKey(self.selKeys)
        self.setSelKeys(self.selKeys)

    def onDeactivate(self):
        TextService.onDeactivate(self)
        # unload libchewing context
        self.ctx = None
        self.removeButton("test-btn")

    def filterKeyDown(self, keyEvent):
        return True

    def onKeyDown(self, keyEvent):
        return True

    def onCommand(self, commandId, commandType):
        print("onCommand", commandId, commandType)
