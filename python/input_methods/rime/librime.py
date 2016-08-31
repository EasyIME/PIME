#!/usr/bin/env python3
#
# Copyright (C) librime developers
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

from ctypes import *
from time import time
import sys, os

if __name__ == "__main__":
    sys.path.append('../../')
from opencc import OpenCC

ENC = sys.getfilesystemencoding()
RIME = "Rime"
_librime = None
if sys.platform == "win32": # Windows
    import os.path
    # find in current dir first
    dll_path = os.path.join(os.path.dirname(__file__), "rime.dll")
    if not os.path.exists(dll_path):
        dll_path = "rime.dll" # search in system path
    _librime = CDLL(dll_path)
else: # UNIX-like systems
    _librime = CDLL('librime.so')

RimeSessionId = POINTER(c_uint)
RimeNotificationHandler = CFUNCTYPE(None, c_void_p, RimeSessionId, c_char_p, c_char_p)
Bool = c_int
RIME_MAX_NUM_CANDIDATES = 10
CHAR_SIZE = 100

class RIME_STRUCT(Structure):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_size = sizeof(self) - sizeof(c_int)

    def has_member(self, member):
        return hasattr(self, member)

    def __del__(self):
        try:
            memset(self, 0, sizeof(self))
        except:
            pass
        finally:
            del self

class RimeTraits(RIME_STRUCT):
    _fields_ = [
        ("data_size", c_int),
        ("shared_data_dir", c_char_p),
        ("user_data_dir", c_char_p),
        ("distribution_name", c_char_p),
        ("distribution_code_name", c_char_p),
        ("distribution_version", c_char_p),
        ("app_name", c_char_p),
        ("modules", POINTER(c_char_p))]

class RimeComposition(Structure):
    _fields_ = [
        ("length", c_int),
        ("cursor_pos", c_int),
        ("sel_start", c_int),
        ("sel_end", c_int),
        ("preedit", c_char_p)]

class RimeCandidate(Structure):
    _fields_ = [
        ("text", c_char_p),
        ("comment", c_char_p),
        ("reserved", c_void_p)]

class RimeMenu(Structure):
    _fields_ = [
        ("page_size", c_int),
        ("page_no", c_int),
        ("is_last_page", Bool),
        ("highlighted_candidate_index", c_int),
        ("num_candidates", c_int),
        ("candidates", POINTER(RimeCandidate)),
        ("select_keys", c_char_p)]

class RimeCommit(RIME_STRUCT):
    _fields_ = [
        ("data_size", c_int),
        ("text", c_char_p)]

class RimeContext(RIME_STRUCT):
    _fields_ = [
        ("data_size", c_int),
        ("composition", RimeComposition),
        ("menu", RimeMenu),
        ("commit_text_preview", c_char_p),
        ("select_labels", POINTER(c_char_p))
        ]

class RimeStatus(RIME_STRUCT):
    _fields_ = [
        ("data_size", c_int),
        ("schema_id", c_char_p),
        ("schema_name", c_char_p),
        ("is_disabled", Bool),
        ("is_composing", Bool),
        ("is_ascii_mode", Bool),
        ("is_full_shape", Bool),
        ("is_simplified", Bool),
        ("is_traditional", Bool),
        ("is_ascii_punct", Bool),
        ]

class RimeCandidateListIterator(Structure):
    _fields_ = [
        ("ptr", c_void_p),
        ("index", c_int),
        ("candidate", RimeCandidate)]

class RimeConfig(Structure):
    _fields_ = [("ptr", c_void_p)]

class RimeConfigIterator(Structure):
    _fields_ = [
        ("list", c_void_p),
        ("map", c_void_p),
        ("index", c_int),
        ("key", c_char_p),
        ("path", c_char_p)]

class RimeSchemaListItem(Structure):
    _fields_ = [
        ("schema_id", c_char_p),
        ("name", c_char_p),
        ("reserved", c_void_p)]

class RimeSchemaList(Structure):
    _fields_ = [
        ("size", c_size_t),
        ("list", POINTER(RimeSchemaListItem))]

class RimeCustomApi(RIME_STRUCT):
    _fields_ = [("data_size", c_int)]

class RimeModule(RIME_STRUCT):
    _fields_ = [("data_size", c_int),
        ("module_name", c_char_p),
        ("initialize", c_void_p),
        ("finalize", c_void_p),
        ("get_api", CFUNCTYPE(POINTER(RimeCustomApi)))
        ]

_librime.RimeCreateSession.restype = RimeSessionId
_librime.RimeConfigGetCString.restype = c_char_p
_librime.RimeConfigListSize.restype = c_size_t
_librime.RimeGetSharedDataDir.restype=c_char_p
_librime.RimeGetUserDataDir.restype=c_char_p
_librime.RimeGetSyncDir.restype=c_char_p
_librime.RimeGetUserId.restype=c_char_p
_librime.RimeFindModule.restype = POINTER(RimeModule)

class RimeApi(RIME_STRUCT):
    _fields_ = [("data_size", c_int),
        ("setup", CFUNCTYPE(None, POINTER(RimeTraits))),
        ("set_notification_handler", CFUNCTYPE(None, RimeNotificationHandler, c_void_p)),
        ("initialize", CFUNCTYPE(None, POINTER(RimeTraits))),
        ("finalize", CFUNCTYPE(None)),
        ("start_maintenance", CFUNCTYPE(Bool, Bool)),
        ("is_maintenance_mode", CFUNCTYPE(Bool)),
        ("join_maintenance_thread", CFUNCTYPE(None)),
        ("deployer_initialize", CFUNCTYPE(None, POINTER(RimeTraits))),
        ("prebuild", CFUNCTYPE(Bool)),
        ("deploy", CFUNCTYPE(Bool)),
        ("deploy_schema", CFUNCTYPE(Bool, c_char_p)),
        ("deploy_config_file", CFUNCTYPE(Bool, c_char_p, c_char_p)),
        ("sync_user_data", CFUNCTYPE(Bool)),
        ("create_session", CFUNCTYPE(RimeSessionId)),
        ("find_session", CFUNCTYPE(Bool, RimeSessionId)),
        ("destroy_session", CFUNCTYPE(Bool, RimeSessionId)),
        ("cleanup_stale_sessions", CFUNCTYPE(None)),
        ("cleanup_all_sessions", CFUNCTYPE(None)),
        ("process_key", CFUNCTYPE(Bool, RimeSessionId, c_int, c_int)),
        ("commit_composition", CFUNCTYPE(Bool, RimeSessionId)),
        ("clear_composition", CFUNCTYPE(None, RimeSessionId)),
        ("get_commit", CFUNCTYPE(Bool, RimeSessionId, POINTER(RimeCommit))),
        ("free_commit", CFUNCTYPE(Bool, POINTER(RimeCommit))),
        ("get_context", CFUNCTYPE(Bool, RimeSessionId, POINTER(RimeContext))),
        ("free_context", CFUNCTYPE(Bool, POINTER(RimeContext))),
        ("get_status", CFUNCTYPE(Bool, RimeSessionId, POINTER(RimeStatus))),
        ("free_status", CFUNCTYPE(Bool, POINTER(RimeStatus))),
        ("set_option", CFUNCTYPE(None, RimeSessionId, c_char_p, Bool)),
        ("get_option", CFUNCTYPE(Bool, RimeSessionId, c_char_p)),
        ("set_property", CFUNCTYPE(None, RimeSessionId, c_char_p, c_char_p)),
        ("get_property", CFUNCTYPE(Bool, RimeSessionId, c_char_p, c_char_p, c_size_t)),
        ("get_schema_list", CFUNCTYPE(Bool, POINTER(RimeSchemaList))),
        ("free_schema_list", CFUNCTYPE(None, POINTER(RimeSchemaList))),
        ("get_current_schema", CFUNCTYPE(Bool, RimeSessionId, c_char_p, c_size_t)),
        ("select_schema", CFUNCTYPE(Bool, RimeSessionId, c_char_p)),
        ("schema_open", CFUNCTYPE(Bool, c_char_p, POINTER(RimeConfig))),
        ("config_open", CFUNCTYPE(Bool, c_char_p, POINTER(RimeConfig))),
        ("config_close", CFUNCTYPE(Bool, POINTER(RimeConfig))),
        ("config_get_bool", CFUNCTYPE(Bool, POINTER(RimeConfig), c_char_p, POINTER(Bool))),
        ("config_get_int", CFUNCTYPE(Bool, POINTER(RimeConfig), c_char_p, POINTER(c_int))),
        ("config_get_double", CFUNCTYPE(Bool, POINTER(RimeConfig), c_char_p, POINTER(c_double))),
        ("config_get_string", CFUNCTYPE(Bool, POINTER(RimeConfig), c_char_p, c_char_p, c_size_t)),
        ("config_get_cstring", CFUNCTYPE(c_char_p, POINTER(RimeConfig), c_char_p)),
        ("config_update_signature", CFUNCTYPE(Bool, POINTER(RimeConfig), c_char_p)),
        ("config_begin_map", CFUNCTYPE(Bool, POINTER(RimeConfigIterator), POINTER(RimeConfig), c_char_p)),
        ("config_next", CFUNCTYPE(Bool, POINTER(RimeConfigIterator))),
        ("config_end", CFUNCTYPE(None, POINTER(RimeConfigIterator))),
        ("simulate_key_sequence", CFUNCTYPE(Bool, RimeSessionId, c_char_p)),
        ("register_module", CFUNCTYPE(Bool, POINTER(RimeModule))),
        ("find_module", CFUNCTYPE(POINTER(RimeModule), c_char_p)),
        ("run_task", CFUNCTYPE(Bool, c_char_p)),
        ("get_shared_data_dir", CFUNCTYPE(c_char_p)),
        ("get_user_data_dir", CFUNCTYPE(c_char_p)),
        ("get_sync_dir", CFUNCTYPE(c_char_p)),
        ("get_user_id", CFUNCTYPE(c_char_p)),
        ("get_user_data_sync_dir", CFUNCTYPE(None, c_char_p, c_size_t)),
        ("config_init", CFUNCTYPE(Bool, POINTER(RimeConfig))),
        ("config_load_string", CFUNCTYPE(Bool, POINTER(RimeConfig), c_char_p)),
        ("config_set_bool", CFUNCTYPE(Bool, POINTER(RimeConfig), c_char_p, Bool)),
        ("config_set_int", CFUNCTYPE(Bool, POINTER(RimeConfig), c_char_p, c_int)),
        ("config_set_double", CFUNCTYPE(Bool, POINTER(RimeConfig), c_char_p, c_double)),
        ("config_set_string", CFUNCTYPE(Bool, POINTER(RimeConfig), c_char_p, c_char_p)),
        ("config_get_item", CFUNCTYPE(Bool, POINTER(RimeConfig), c_char_p, POINTER(RimeConfig))),
        ("config_set_item", CFUNCTYPE(Bool, POINTER(RimeConfig), c_char_p, POINTER(RimeConfig))),
        ("config_clear", CFUNCTYPE(Bool, POINTER(RimeConfig), c_char_p)),
        ("config_create_list", CFUNCTYPE(Bool, POINTER(RimeConfig), c_char_p)),
        ("config_create_map", CFUNCTYPE(Bool, POINTER(RimeConfig), c_char_p)),
        ("config_list_size", CFUNCTYPE(c_size_t, POINTER(RimeConfig), c_char_p)),
        ("config_begin_list", CFUNCTYPE(Bool, POINTER(RimeConfigIterator), POINTER(RimeConfig), c_char_p)),
        ("get_input", CFUNCTYPE(c_char_p, RimeSessionId)),
        ("get_caret_pos", CFUNCTYPE(c_size_t, RimeSessionId)),
        ("select_candidate", CFUNCTYPE(Bool, RimeSessionId, c_size_t)),
        ("get_version", CFUNCTYPE(c_char_p)),
        ("set_caret_pos", CFUNCTYPE(None, RimeSessionId, c_size_t)),
        ("select_candidate_on_current_page", CFUNCTYPE(Bool, RimeSessionId, c_size_t)),
        ("candidate_list_begin", CFUNCTYPE(Bool, RimeSessionId, POINTER(RimeCandidateListIterator))),
        ("candidate_list_next", CFUNCTYPE(Bool, POINTER(RimeCandidateListIterator))),
        ("candidate_list_end", CFUNCTYPE(None, POINTER(RimeCandidateListIterator))),
        ]

_librime.rime_get_api.restype = POINTER(RimeApi)

rime = _librime.rime_get_api().contents

def rimeNotificationHandler(context_object, session_id, message_type, message_value):
    print(context_object, session_id.contents if session_id else 0, message_type, message_value)

def rimeInit(datadir="data", userdir="data", fullcheck=True, appname="python", appver="0.01"):
    traits = RimeTraits(
        shared_data_dir=c_char_p(datadir.encode(ENC)),
        user_data_dir=c_char_p(userdir.encode(ENC)),
        distribution_name=c_char_p(RIME.encode("UTF-8")),
        distribution_code_name=c_char_p(appname.encode("UTF-8")),
        distribution_version=c_char_p(appver.encode("UTF-8")),
        app_name=c_char_p(("%s.%s"%(RIME, appname)).encode("UTF-8"))
        )
    rime.setup(traits)
    #cb = RimeNotificationHandler(rimeNotificationHandler)
    #rime.set_notification_handler(cb, byref(rime))
    rime.initialize(None)
    if rime.start_maintenance(fullcheck):
        rime.join_maintenance_thread()

def rimeGetString(config, name):
    cstring = rime.config_get_cstring(config, name.encode("UTF-8"))
    return cstring.decode("UTF-8") if cstring else ""

def rimeSelectSchema(session_id, schema_id):
    rime.select_schema(session_id, schema_id)
    user_config = RimeConfig()
    if rime.config_open(b'user', user_config):
        rime.config_set_string(user_config, b'var/previously_selected_schema', schema_id)
        rime.config_set_int(user_config, b'var/schema_access_time/' + schema_id, c_int(int(time())))
        rime.config_close(user_config)

# 選單項目和語言列按鈕的 command ID
ID_MODE_ICON = 1
ID_ASCII_MODE = 2
ID_FULL_SHAPE = 3

ID_DEPLOY = 10
ID_SYNC = 11
ID_SYNC_DIR = 12
ID_SHARED_DIR = 13
ID_USER_DIR = 14
ID_SCHEMA_LIST = 15
ID_LOG_DIR = 16

ID_URI = 300 #os.startfile
ID_SCHEMA = 200 #rime.select_schema
ID_OPTION = 100 #rime.set_option

commands = {
    "deploy": ID_DEPLOY,
    "sync_user_data": ID_SYNC,
    "get_sync_dir": ID_SYNC_DIR,
    "get_shared_data_dir": ID_SHARED_DIR,
    "get_user_data_dir": ID_USER_DIR,
    "get_schema_list": ID_SCHEMA_LIST,
    "get_log_dir": ID_LOG_DIR,
}

class RimeStyle:
    font_face = "MingLiu"
    candidate_format = "{0} {1}"
    inline_preedit = "false"
    menu_opencc = None
    font_point = 20
    candidate_per_row = 1
    inline_code = False
    display_tray_icon = False
    candidate_use_cursor = False
    soft_cursor = False
    menu = []
    options = []
    options_states = []
    schemas = []
    uris = []
    session_id = None

    def __init__(self, appname, session_id):
        self.session_id = session_id
        config = RimeConfig()
        if not rime.config_open(appname.encode("UTF-8"), config):
            return
        self.font_face = rimeGetString(config, 'style/font_face')
        self.candidate_format = rimeGetString(config, 'style/candidate_format')
        self.inline_preedit = rimeGetString(config, 'style/inline_preedit')
        menu_opencc_config = rimeGetString(config, 'style/menu_opencc')
        self.menu_opencc = OpenCC(menu_opencc_config) if menu_opencc_config else None
        value = c_int()
        if rime.config_get_int(config, b'style/font_point', value):
            self.font_point = value.value
        if rime.config_get_bool(config, b'style/horizontal', value):
            self.candidate_per_row = 10 if bool(value) else 1
        if rime.config_get_int(config, b'style/candidate_per_row', value):
            self.candidate_per_row = value.value
        if rime.config_get_bool(config, b'style/display_tray_icon', value):
            self.display_tray_icon = bool(value)
        if rime.config_get_bool(config, b'style/candidate_use_cursor', value):
            self.candidate_use_cursor = bool(value)
        if rime.config_get_bool(config, b'style/soft_cursor', value):
            self.soft_cursor = bool(value)
        self.options.clear()
        self.options_states.clear()
        self.uris.clear()
        self.menu = self.config_get_menu(config, b'menu')
        #print("menu", self.menu)
        rime.config_close(config)

    def get_schema(self, commandId):
        if commandId >= ID_SCHEMA:
            return self.schemas[commandId - ID_SCHEMA]

    def get_option(self, commandId):
        if commandId >= ID_OPTION:
            return self.options[commandId - ID_OPTION]

    def get_uri(self, commandId):
        if commandId >= ID_URI:
            return self.uris[commandId - ID_URI]

    def get_schema_list(self):
        schema_list = RimeSchemaList()
        self.schemas = []
        submenu = []
        current_schema = bytes(CHAR_SIZE)
        rime.get_current_schema(self.session_id, current_schema, CHAR_SIZE)
        current_schema_id = current_schema.rstrip(b'\0')
        if rime.get_schema_list(schema_list):
            n = schema_list.size
            for i in range(n):
                schema_id = schema_list.list[i].schema_id
                name = schema_list.list[i].name.decode("UTF-8")
                if self.menu_opencc:
                    name = self.menu_opencc.convert(name)
                self.schemas.append(schema_id)
                d = {'text': name, 'id': ID_SCHEMA + i}
                if schema_id == current_schema_id:
                    d["checked"] = True
                submenu.append(d)
        rime.free_schema_list(schema_list)
        return submenu          

    def config_get_menu(self, config, path):
        menu = []
        iterator = RimeConfigIterator()
        if not rime.config_begin_list(iterator, config, path):
            return
        while rime.config_next(iterator):
            d = {}
            name = rime.config_get_cstring(config, iterator.path + b'/name')
            command = rime.config_get_cstring(config, iterator.path + b'/command')
            uri = rime.config_get_cstring(config, iterator.path + b'/uri')
            text = rime.config_get_cstring(config, iterator.path + b'/text')
            if command:
                d["id"] = commands.get(command.decode("UTF-8"), 0)
                if ID_SCHEMA_LIST == d["id"]:
                    d["submenu"] = self.get_schema_list()
                elif ID_SYNC_DIR == d["id"]:
                    d["enabled"] = os.path.isdir(rime.get_sync_dir().decode(ENC))
            elif uri:
                d["id"] = ID_URI + len(self.uris)
                self.uris.append(uri.decode("UTF-8"))
            elif name:
                states = [rime.config_get_cstring(config, iterator.path + b'/states/@0').decode("UTF-8"),
                          rime.config_get_cstring(config, iterator.path + b'/states/@1').decode("UTF-8")]
                d["id"] = ID_OPTION + len(self.options)
                state_id = rime.get_option(self.session_id, name)
                d["text"] = "%s → %s" % (states[state_id], states[1 - state_id])
                self.options_states.append(states)
                self.options.append(name)
            if text:
                d["text"] = text.decode("UTF-8")
                if self.menu_opencc:
                    d["text"] = self.menu_opencc.convert(d["text"])
                submenu = self.config_get_menu(config, iterator.path + b'/submenu')
                if submenu:
                    d["submenu"] = submenu
            menu.append(d)
        rime.config_end(iterator)
        return menu

def processKey(session_id, keycode, mask):
    print("process_key", keycode, "ret", rime.process_key(session_id, keycode, mask))
    status = RimeStatus()
    if rime.get_status(session_id, status):
        print("is_composing",  status.is_composing)
        print("is_ascii_mode",  status.is_ascii_mode)
        print("current_schema", status.schema_name.decode("UTF-8"))
        rime.free_status(status)

    commit = RimeCommit()
    if rime.get_commit(session_id, commit):
        print("commit",commit.text.decode("UTF-8"))
        rime.free_commit(commit)

    context = RimeContext()
    if not rime.get_context(session_id, context) or context.composition.length == 0:
        rime.free_context(context)
        exit

    if context.commit_text_preview:
        commit_text_preview = context.commit_text_preview.decode("UTF-8")
        print("commit_text_preview",commit_text_preview)

    if context.composition.length:
        print("preedit", context.composition.preedit.decode("UTF-8"),
              "cursor_pos", context.composition.cursor_pos,
              "sel_start", context.composition.sel_start,
              "sel_end", context.composition.sel_end)

    if context.menu.page_size:
        print("page_size",context.menu.page_size)
        select_keys = b''
        if context.select_labels:
            for i in range(context.menu.page_size):
                select_keys += context.select_labels[i]
        elif context.menu.select_keys:
            select_keys = context.menu.select_keys
        if select_keys:
            print("select_keys",select_keys.decode("UTF-8"))

    if context.menu.num_candidates:
        print("num_candidates", context.menu.num_candidates)
        candidates = []
        for i in range(context.menu.num_candidates):
            cand = context.menu.candidates[i]
            s = cand.text
            if cand.comment:
                s += b' ' + cand.comment
            candidates.append(s.decode("UTF-8"))
        print(candidates)
    rime.free_context(context)

if __name__ == "__main__":
    rimeInit()
    session_id = rime.create_session()
    RimeStyle("PIME", session_id)
    processKey(session_id, ord('a'), 0)
    #processKey(session_id, ord('a'), 1<<30)
    processKey(session_id, 0xFFE2, 0)
    processKey(session_id, 0xFFE2,1 << 30)
    rime.destroy_session(session_id)
    rime.finalize()
