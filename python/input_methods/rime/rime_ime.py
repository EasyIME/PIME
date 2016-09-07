#!/usr/bin/env python3
# Copyright (C) 2016 Osfans <waxaca@163.com>
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

from .librime import *
from .rime_keyevent import translateKeyCode, translateModifiers, RELEASE_MASK

from keycodes import * # for VK_XXX constants
from textService import *

from ctypes import *
import os

APP = "PIME"
APP_VERSION = "0.01"
CONFIG_FILE = APP + ".yaml"

user_dir = os.path.join(os.path.expandvars("%APPDATA%"), APP, RIME)
first_run = not os.path.isdir(user_dir)
if first_run:
    os.makedirs(user_dir, mode=0o700, exist_ok=True)
curdir = os.path.abspath(os.path.dirname(__file__))
shared_dir = os.path.join(curdir, "data")
rimeInit(datadir=shared_dir, userdir=user_dir, appname=APP, appver=APP_VERSION, fullcheck=first_run)
rime.deploy_config_file(CONFIG_FILE.encode("UTF-8"), b'config_version')

def rimeCallback(context_object, session_id, message_type, message_value):
    pass
rime_callback = RimeNotificationHandler(rimeCallback)
rime.set_notification_handler(rime_callback, None)

class RimeTextService(TextService):   
    session_id = None
    icon_dir = os.path.join(curdir, "icons")
    style = None
    lastKeyDownCode = None
    lastKeySkip = 0
    lastKeyDownRet = True
    lastKeyUpCode = None
    lastKeyUpRet = True
    keyComposing = False

    def __init__(self, client):
        TextService.__init__(self, client)

    def onActivate(self):
        TextService.onActivate(self)
        self.createSession()

        if not self.style.display_tray_icon: return
        # Windows 8 以上systray IME mode icon
        if self.client.isWindows8Above:
            icon_name = "%s_%s_caps%s.ico" % ("eng", "full", "on")
            self.addButton("windows-mode-icon",
                icon = os.path.join(self.icon_dir, icon_name),
                tooltip = "中西文切換",
                commandId = ID_MODE_ICON
            )

        icon_name = "eng.ico"
        self.addButton("switch-lang",
            icon = os.path.join(self.icon_dir, icon_name),
            text = "中西文切換",
            tooltip = "中西文切換",
            commandId = ID_ASCII_MODE,
        )
        # 切換全半形
        icon_name = "full.ico"
        self.addButton("switch-shape",
            icon = os.path.join(self.icon_dir, icon_name),
            text = "全半角切換",
            tooltip = "全角/半角切換",
            commandId = ID_FULL_SHAPE
        )
        # 設定
        self.addButton("settings",
            icon = os.path.join(self.icon_dir, "config.ico"),
            text = "設定",
            tooltip = "設定",
            type = "menu"
        )
        self.updateLangStatus()

    def createSession(self):
        if not (self.session_id and rime.find_session(self.session_id)):
            self.session_id = rime.create_session()
            self.style = RimeStyle(APP, self.session_id)
            self.customizeUI(candFontSize = self.style.font_point,
                candFontName = self.style.font_face,
                candPerRow = self.style.candidate_per_row,
                candUseCursor = self.style.candidate_use_cursor)
            rime.set_option(self.session_id, b'soft_cursor', self.style.soft_cursor)
            rime.set_option(self.session_id, b'_horizontal', self.style.candidate_per_row > 1)

    def onDeactivate(self):
        TextService.onDeactivate(self)
        self.destroySession()
        if not self.style.display_tray_icon: return
        self.removeButton("switch-lang")
        self.removeButton("switch-shape")
        self.removeButton("settings")
        if self.client.isWindows8Above:
            self.removeButton("windows-mode-icon")

    def processKey(self, keyEvent, isUp = False):
        self.createSession()
        print("session", self.session_id.contents if self.session_id else None, rime)
        if not isUp: self.keyComposing = self.isComposing()
        ret = rime.process_key(self.session_id, translateKeyCode(keyEvent), translateModifiers(keyEvent, isUp))
        print("Up" if isUp else "Down", keyEvent.keyCode,keyEvent.repeatCount,keyEvent.scanCode,translateKeyCode(keyEvent), translateModifiers(keyEvent, isUp), "ret", ret)
        if ret:
            return True
        if self.keyComposing and keyEvent.keyCode == VK_RETURN:
            return True
        if (keyEvent.keyCode in (VK_SHIFT, VK_CONTROL, VK_CAPITAL)) and translateModifiers(keyEvent, isUp) in (0, RELEASE_MASK):
            return True
        return ret

    def filterKeyDown(self, keyEvent):
        #print("keyDown", keyEvent.keyCode,keyEvent.repeatCount)
        if self.lastKeyDownCode == keyEvent.keyCode:
            self.lastKeySkip += 1
            if self.lastKeySkip >= 2:
                self.lastKeyDownCode = None
                self.lastKeySkip = 0
        else:
            self.lastKeyDownCode = keyEvent.keyCode
            self.lastKeySkip = 0
            self.lastKeyDownRet = self.processKey(keyEvent)
        self.lastKeyUpCode = None
        return self.lastKeyDownRet

    def filterKeyUp(self, keyEvent):
        if self.lastKeyUpCode == keyEvent.keyCode:
            self.lastKeyUpCode = None
        else:
            self.lastKeyUpCode = keyEvent.keyCode
            self.lastKeyUpRet = self.processKey(keyEvent, True)
        self.lastKeyDownCode = None
        self.lastKeySkip = 0
        return self.lastKeyUpRet

    def clear(self):
        self.setShowCandidates(False)
        self.setCompositionString("")
        self.setCompositionCursor(0)
        rime.clear_composition(self.session_id)

    def destroySession(self):
        self.clear()
        if self.session_id:
            rime.destroy_session(self.session_id)
        self.session_id = None
        #rime.finalize()
        #self.style = None

    def getKeyState(self, keyCode):
        return WinDLL("User32.dll").GetKeyState(keyCode)

    # 依照目前輸入法狀態，更新語言列顯示
    def updateLangStatus(self):
        if not self.session_id: return
        if not self.style.display_tray_icon: return
        is_ascii_mode = rime.get_option(self.session_id, b'ascii_mode')
        is_full_shape = rime.get_option(self.session_id, b'full_shape')
        is_caps_on = self.getKeyState(VK_CAPITAL)

        if self.client.isWindows8Above: # windows 8 mode icon
            # FIXME: we need a better set of icons to meet the 
            #        WIndows 8 IME guideline and UX guidelines.
            icon_name = "%s_%s_caps%s.ico" % ("eng" if is_ascii_mode else "chi", "full" if is_full_shape else "half", "on" if is_caps_on else "off")
            icon_path = os.path.join(self.icon_dir, icon_name)
            self.changeButton("windows-mode-icon", icon=icon_path)

        icon_name = "eng.ico" if is_ascii_mode else "chi.ico"
        icon_path = os.path.join(self.icon_dir, icon_name)
        self.changeButton("switch-lang", icon=icon_path)

        icon_name = "full.ico" if is_full_shape else "half.ico"
        icon_path = os.path.join(self.icon_dir, icon_name)
        self.changeButton("switch-shape", icon=icon_path)

    def onKey(self):
        self.updateLangStatus()

        commit = RimeCommit()
        if rime.get_commit(self.session_id, commit):
            self.setCommitString(commit.text.decode("UTF-8"))
            rime.free_commit(commit)

        context = RimeContext()
        if not rime.get_context(self.session_id, context) or context.composition.length == 0:
            rime.free_context(context)
            self.clear()
            return True

        if self.style.inline_preedit in ("composition", "true"):
            composition = context.composition.preedit
            preedit = composition.decode("UTF-8") if composition else ""
            self.setCompositionString(preedit)
            self.setCompositionCursor(len(composition[:context.composition.cursor_pos].decode("UTF-8")) if composition else 0)
        elif self.style.inline_preedit in ("preview", "preedit"):
            preedit = context.commit_text_preview.decode("UTF-8") if context.commit_text_preview else ""
            self.setCompositionString(preedit)
            self.setCompositionCursor(len(preedit))
        elif self.style.inline_preedit == "input":
            preedit = rime.get_input(self.session_id).decode("UTF-8")
            self.setCompositionString(preedit)
            self.setCompositionCursor(len(preedit))

        if context.menu.page_size:
            select_keys = b''
            if context.select_labels:
                for i in range(context.menu.page_size):
                    select_keys += context.select_labels[i]
            elif context.menu.select_keys:
                select_keys = context.menu.select_keys
            if select_keys:
                self.setSelKeys(select_keys.decode("UTF-8"))

        hide_candidate = rime.get_option(self.session_id, b'_hide_candidate')
        if context.menu.num_candidates and not hide_candidate:
            n = context.menu.num_candidates
            candidates = []
            for i in range(n):
                cand = context.menu.candidates[i]
                s = cand.text.decode("UTF-8")
                if cand.comment:
                    try:
                        s = self.style.candidate_format.format(s, cand.comment.decode("UTF-8"))
                    except:
                        s += " " + cand.comment.decode("UTF-8")
                candidates.append(s)
            self.setCandidateList(candidates)
            self.setCandidateCursor(context.menu.highlighted_candidate_index)
            self.setShowCandidates(True)
        else:
            self.setShowCandidates(False)
        rime.free_context(context)
        return True

    def onKeyDown(self, keyEvent):
        return self.onKey()

    def onKeyUp(self, keyEvent):
        return self.onKey()

    def toggleOption(self, name):
        ret = rime.get_option(self.session_id, name)
        rime.set_option(self.session_id, name, not ret)
        self.updateLangStatus()
        
    def onCommand(self, commandId, commandType):
        print("onCommand", commandId, commandType)
        global user_dir, shared_dir
        if commandId >= ID_URI:
            os.startfile(self.style.get_uri(commandId))
        elif commandId >= ID_SCHEMA:
            schema_id = self.style.get_schema(commandId)
            rimeSelectSchema(self.session_id, schema_id)
        elif commandId >= ID_OPTION:
            self.toggleOption(self.style.get_option(commandId))
        elif commandId in (ID_ASCII_MODE, ID_MODE_ICON) and commandType == COMMAND_LEFT_CLICK:  # 切換中英文模式
            self.toggleOption(b'ascii_mode')
        elif commandId == ID_FULL_SHAPE:  # 切換全半角
            self.toggleOption(b'full_shape')
        elif commandId == ID_USER_DIR:
            os.startfile(user_dir)
        elif commandId == ID_SHARED_DIR:
            os.startfile(shared_dir)
        elif commandId == ID_SYNC_DIR:
            sync_dir = rime.get_sync_dir().decode(ENC)
            if os.path.isdir(sync_dir):
                os.startfile(sync_dir)
        elif commandId == ID_LOG_DIR:
            os.startfile(os.path.expandvars("%TEMP%"))
        elif commandId == ID_SYNC:
            rime.sync_user_data()
        elif commandId == ID_DEPLOY:
            self.destroySession()
            rime.finalize()
            #rime.set_notification_handler(None, None)
            rime.initialize(None)
            if rime.start_maintenance(True):
                rime.join_maintenance_thread()
            rime.deploy_config_file(CONFIG_FILE.encode("UTF-8"), b'config_version')
            self.createSession()
            self.onKey()

    # 開啟語言列按鈕選單
    def onMenu(self, buttonId):
        # print("onMenu", buttonId)
        # 設定按鈕 (windows 8 mode icon 按鈕也使用同一個選單)
        if buttonId in ("settings", "windows-mode-icon"):
            self.style = RimeStyle(APP, self.session_id)
            return self.style.menu
        return None

    # 鍵盤開啟/關閉時會被呼叫 (在 Windows 10 Ctrl+Space 時)
    def onKeyboardStatusChanged(self, opened):
        TextService.onKeyboardStatusChanged(self, opened)
        if opened: # 鍵盤開啟
            rime.initialize(None)
            self.createSession()
        else: # 鍵盤關閉，輸入法停用
            # self.hideMessage() # hide message window, if there's any
            self.destroySession()
            rime.finalize()
        if not self.style.display_tray_icon: return
        # Windows 8 systray IME mode icon
        if self.client.isWindows8Above:
            # 若鍵盤關閉，我們需要把 widnows 8 mode icon 設定為 disabled
            self.changeButton("windows-mode-icon", enable=opened)
        # FIXME: 是否需要同時 disable 其他語言列按鈕？

    # 當中文編輯結束時會被呼叫。若中文編輯不是正常結束，而是因為使用者
    # 切換到其他應用程式或其他原因，導致我們的輸入法被強制關閉，此時
    # forced 參數會是 True，在這種狀況下，要清除一些 buffer
    def onCompositionTerminated(self, forced):
        TextService.onCompositionTerminated(self, forced)
        if forced:
            # 中文組字到一半被系統強制關閉，清除編輯區內容
            self.destroySession()
