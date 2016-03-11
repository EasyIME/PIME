//
//	Copyright (C) 2014 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
//
//	This library is free software; you can redistribute it and/or
//	modify it under the terms of the GNU Library General Public
//	License as published by the Free Software Foundation; either
//	version 2 of the License, or (at your option) any later version.
//
//	This library is distributed in the hope that it will be useful,
//	but WITHOUT ANY WARRANTY; without even the implied warranty of
//	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
//	Library General Public License for more details.
//
//	You should have received a copy of the GNU Library General Public
//	License along with this library; if not, write to the
//	Free Software Foundation, Inc., 51 Franklin St, Fifth Floor,
//	Boston, MA  02110-1301, USA.
//

#include "PIMEClient.h"
#include "libIME/Utils.h"
#include <algorithm>
#include "rapidjson/writer.h"
#include "rapidjson/stringbuffer.h"
#include "PIMETextService.h"
#include <cstdlib>
#include <ctime>
#include <memory>

using namespace std;
using namespace rapidjson;

namespace PIME {

Client::Client(TextService* service):
	textService_(service),
	pipe_(INVALID_HANDLE_VALUE) {

	static bool init_srand = false;
	if (!init_srand) {
		srand(time(NULL));
	}
}

Client::~Client(void) {
	closePipe();

	// some language bar buttons are not unregistered properly
	if (!buttons_.empty()) {
		for (auto it = buttons_.begin(); it != buttons_.end(); ++it) {
			textService_->removeButton(it->second);
		}
	}
	LangBarButton::clearIconCache();
}

// pack a keyEvent object into a json value
//static
void Client::keyEventToJson(Writer<StringBuffer>& writer, Ime::KeyEvent& keyEvent) {
	writer.String("charCode");
	writer.Uint(keyEvent.charCode());

	writer.String("keyCode");
	writer.Uint(keyEvent.keyCode());

	writer.String("repeatCount");
	writer.Uint(keyEvent.repeatCount());

	writer.String("scanCode");
	writer.Uint(keyEvent.scanCode());

	writer.String("isExtended");
	writer.Bool(keyEvent.isExtended());

	writer.String("keyStates");
	writer.StartArray();
	const BYTE* states = keyEvent.keyStates();
	for(int i = 0; i < 256; ++i) {
		writer.Uint(states[i]);
	}
	writer.EndArray();
}

int Client::addSeqNum(Writer<StringBuffer>& writer) {
	int seqNum = rand();
	writer.String("seqNum");
	writer.Uint(seqNum);
	return seqNum;
}

bool Client::handleReply(rapidjson::Value& msg, Ime::EditSession* session) {
	auto it = msg.FindMember("success");
	if (it != msg.MemberEnd() && it->value.IsBool()) {
		bool success = it->value.GetBool();
		if (success) {
			updateStatus(msg, session);
		}
		return success;
	}
	return false;
}

void Client::updateUI(rapidjson::Value& data) {
	for (auto it = data.MemberBegin(); it != data.MemberEnd(); ++it) {
		const char* name = it->name.GetString();
		if (it->value.IsString() && strcmp(name, "candFontName") == 0) {
			wstring fontName = utf8ToUtf16(it->value.GetString());
			textService_->setCandFontName(fontName);
		}
		else if (it->value.IsInt() && strcmp(name, "candFontSize") == 0) {
			textService_->setCandFontSize(it->value.GetInt());
		}
		else if (it->value.IsInt() && strcmp(name, "candPerRow") == 0) {
			textService_->setCandPerRow(it->value.GetInt());
		}
		else if (it->value.IsBool() && strcmp(name, "candUseCursor") == 0) {
			textService_->setCandUseCursor(it->value.GetBool());
		}
	}
}

void Client::updateStatus(rapidjson::Value& msg, Ime::EditSession* session) {
	// We need to handle ordering of some types of the requests.
	// For example, setCompositionCursor() should happen after setCompositionCursor().
	rapidjson::Document::ValueType* commitStringVal = nullptr;
	rapidjson::Document::ValueType* compositionStringVal = nullptr;
	rapidjson::Document::ValueType* compositionCursorVal = nullptr;
	rapidjson::Document::ValueType* candCursorVal = nullptr;

	for (auto it = msg.MemberBegin(); it != msg.MemberEnd(); ++it) {
		const char* name = it->name.GetString();
		if (session != nullptr) { // if an edit session is available
			// commit string
			if (it->value.IsString() && strcmp(name, "commitString") == 0) {
				commitStringVal = &it->value;
				continue;
			}
			else if (it->value.IsString() && strcmp(name, "compositionString") == 0) {
				compositionStringVal = &it->value;
				continue;
			}
			else if (it->value.IsInt() && strcmp(name, "compositionCursor") == 0) {
				compositionCursorVal = &it->value;
				continue;
			}
			else if (it->value.IsArray() && strcmp(name, "candidateList") == 0) {
				// handle candidates
				rapidjson::Value& candidateList = it->value;
				// FIXME: directly access private member is dirty!!!
				vector<wstring>& candidates = textService_->candidates_;
				candidates.clear();
				for (auto it = candidateList.Begin(); it < candidateList.End(); ++it) {
					wstring cand = utf8ToUtf16(it->GetString());
					candidates.push_back(cand);
				}
				textService_->updateCandidates(session);
				continue;
			}
			else if (it->value.IsBool() && strcmp(name, "showCandidates") == 0) {
				bool showCandidates = it->value.GetBool();
				if (showCandidates) {
					textService_->showCandidates(session);
				}
				else {
					textService_->hideCandidates();
				}
				continue;
			}
			else if (it->value.IsInt() && strcmp(name, "candidateCursor") == 0) {
				candCursorVal = &it->value;
				continue;
			}
		}

		// language buttons
		if (it->value.IsArray() && strcmp(name, "addButton") == 0) {
			rapidjson::Value& buttons = it->value;
			for (auto btn_it = buttons.Begin(); btn_it < buttons.End(); ++btn_it) {
				rapidjson::Value& btn = *btn_it;
				// FIXME: when to clear the id <=> button map??
				PIME::LangBarButton* langBtn = PIME::LangBarButton::fromJson(textService_, btn);
				if (langBtn != nullptr) {
					buttons_[langBtn->id()] = langBtn; // insert into the map
					textService_->addButton(langBtn);
					langBtn->Release();
				}
			}
		}
		else if (it->value.IsArray() && strcmp(name, "removeButton") == 0) {
			// FIXME: handle windows-mode-icon
			rapidjson::Value& buttons = it->value;
			for (auto btn_it = buttons.Begin(); btn_it < buttons.End(); ++btn_it) {
				if (btn_it->IsString()) {
					string id = btn_it->GetString();
					auto map_it = buttons_.find(id);
					if (map_it != buttons_.end()) {
						textService_->removeButton(map_it->second);
						buttons_.erase(map_it); // remove from the map
					}
				}
			}
		}
		else if (it->value.IsArray() && strcmp(name, "changeButton") == 0) {
			// FIXME: handle windows-mode-icon
			rapidjson::Value& buttons = it->value;
			for (auto btn_it = buttons.Begin(); btn_it < buttons.End(); ++btn_it) {
				rapidjson::Value& btn = *btn_it;
				if (btn.IsObject()) {
					string id = btn["id"].GetString();
					auto map_it = buttons_.find(id);
					if (map_it != buttons_.end()) {
						map_it->second->update(btn);
					}
				}
			}
		}
		else if (it->value.IsArray() && strcmp(name, "addPreservedKey") == 0) {
			// preserved keys
			rapidjson::Value& keys = it->value;
			for (auto key_it = keys.Begin(); key_it < keys.End(); ++key_it) {
				rapidjson::Value& key = *key_it;
				if (key.IsObject()) {
					std::wstring guidStr = utf8ToUtf16(key["guid"].GetString());
					CLSID guid = { 0 };
					CLSIDFromString(guidStr.c_str(), &guid);
					UINT keyCode = key["keyCode"].GetUint();
					UINT modifiers = key["modifiers"].GetUint();
					textService_->addPreservedKey(keyCode, modifiers, guid);
				}
			}
		}
		else if (it->value.IsArray() && strcmp(name, "removePreservedKey") == 0) {
			rapidjson::Value& keys = it->value;
			for (auto key_it = keys.Begin(); key_it < keys.End(); ++key_it) {
				if (key_it->IsString()) {
					std::wstring guidStr = utf8ToUtf16(key_it->GetString());
					CLSID guid = { 0 };
					CLSIDFromString(guidStr.c_str(), &guid);
					textService_->removePreservedKey(guid);
				}
			}
		}
		// other configurations
		else if (it->value.IsString() && strcmp(name, "setSelKeys") == 0) {
			// keys used to select candidates
			std::wstring selKeys = utf8ToUtf16(it->value.GetString());
			textService_->setSelKeys(selKeys);
		}
		else if (it->value.IsObject() && strcmp(name, "customizeUI") == 0) {
			// customize the UI
			updateUI(it->value);
		}
		// show message
		else if (it->value.IsObject() && strcmp(name, "showMessage") == 0) {
			rapidjson::Value& message = it->value["message"];
			rapidjson::Value& duration = it->value["duration"];
			if (message.IsString() && duration.IsInt()) {
				textService_->showMessage(session, utf8ToUtf16(message.GetString()), duration.GetInt());
			}
		}
	}

	// handle comosition and commit strings
	if (session != nullptr) { // if an edit session is available
		bool endComposition = false;
		if (commitStringVal != nullptr) {
			std::wstring commitString = utf8ToUtf16(commitStringVal->GetString());
			if (!commitString.empty()) {
				if (!textService_->isComposing()) {
					textService_->startComposition(session->context());
				}
				textService_->setCompositionString(session, commitString.c_str(), commitString.length());
				textService_->endComposition(session->context());
			}
		}
		if (compositionStringVal != nullptr) {
			// composition buffer
			std::wstring compositionString = utf8ToUtf16(compositionStringVal->GetString());
			if (!textService_->isComposing()) {
				textService_->startComposition(session->context());
			}
			textService_->setCompositionString(session, compositionString.c_str(), compositionString.length());
			if (compositionString.empty()) {
				endComposition = true;
			}
		}
		if (compositionCursorVal != nullptr) {
			// composition cursor
			int compositionCursor = compositionCursorVal->GetInt();
			if (!textService_->isComposing()) {
				textService_->startComposition(session->context());
			}
			textService_->setCompositionCursor(session, compositionCursor);
		}
		if (candCursorVal != nullptr) {
			if (textService_->candidateWindow_ != nullptr) {
				textService_->candidateWindow_->setCurrentSel(candCursorVal->GetInt());
			}
		}
		if (endComposition && session != nullptr) {
			textService_->endComposition(session->context());
		}
	}
}

// handlers for the text service
void Client::onActivate() {
	StringBuffer s;
	Writer<StringBuffer> writer(s);
	writer.StartObject();
	int sn = addSeqNum(writer);

	writer.String("method");
	writer.String("onActivate");

	writer.EndObject();
	s.GetString();

	rapidjson::Document ret;
	sendRequest(s.GetString(), sn, ret);
	if (handleReply(ret)) {
	}
}

void Client::onDeactivate() {
	StringBuffer s;
	Writer<StringBuffer> writer(s);
	writer.StartObject();
	int sn = addSeqNum(writer);

	writer.String("method");
	writer.String("onDeactivate");

	writer.EndObject();

	rapidjson::Document ret;
	sendRequest(s.GetString(), sn, ret);
	if (handleReply(ret)) {
	}
	LangBarButton::clearIconCache();
}

bool Client::filterKeyDown(Ime::KeyEvent& keyEvent) {
	StringBuffer s;
	Writer<StringBuffer> writer(s);
	writer.StartObject();

	int sn = addSeqNum(writer);

	writer.String("method");
	writer.String("filterKeyDown");

	keyEventToJson(writer, keyEvent);

	writer.EndObject();

	rapidjson::Document ret;
	sendRequest(s.GetString(), sn, ret);
	if (handleReply(ret)) {
		return ret["return"].GetBool();
	}
	return false;
}

bool Client::onKeyDown(Ime::KeyEvent& keyEvent, Ime::EditSession* session) {
	StringBuffer s;
	Writer<StringBuffer> writer(s);
	writer.StartObject();

	int sn = addSeqNum(writer);

	writer.String("method");
	writer.String("onKeyDown");

	keyEventToJson(writer, keyEvent);

	writer.EndObject();

	rapidjson::Document ret;
	sendRequest(s.GetString(), sn, ret);
	if (handleReply(ret, session)) {
		return ret["return"].GetBool();
	}
	return false;
}

bool Client::filterKeyUp(Ime::KeyEvent& keyEvent) {
	StringBuffer s;
	Writer<StringBuffer> writer(s);
	writer.StartObject();

	int sn = addSeqNum(writer);

	writer.String("method");
	writer.String("filterKeyUp");

	keyEventToJson(writer, keyEvent);

	writer.EndObject();

	rapidjson::Document ret;
	sendRequest(s.GetString(), sn, ret);
	if (handleReply(ret)) {
		return ret["return"].GetBool();
	}
	return false;
}

bool Client::onKeyUp(Ime::KeyEvent& keyEvent, Ime::EditSession* session) {
	StringBuffer s;
	Writer<StringBuffer> writer(s);
	writer.StartObject();

	int sn = addSeqNum(writer);

	writer.String("method");
	writer.String("onKeyUp");

	keyEventToJson(writer, keyEvent);

	writer.EndObject();

	rapidjson::Document ret;
	sendRequest(s.GetString(), sn, ret);
	if (handleReply(ret, session)) {
		return ret["return"].GetBool();
	}
	return false;
}

bool Client::onPreservedKey(const GUID& guid) {
	LPOLESTR str = NULL;
	if (SUCCEEDED(::StringFromCLSID(guid, &str))) {
		StringBuffer s;
		Writer<StringBuffer> writer(s);
		writer.StartObject();

		int sn = addSeqNum(writer);

		writer.String("method");
		writer.String("onPreservedKey");

		writer.String("guid");
		writer.String(utf16ToUtf8(str));
		::CoTaskMemFree(str);

		writer.EndObject();

		rapidjson::Document ret;
		sendRequest(s.GetString(), sn, ret);
		if (handleReply(ret)) {
			return ret["return"].GetBool();
		}
	}
	return false;
}

bool Client::onCommand(UINT id, Ime::TextService::CommandType type) {
	StringBuffer s;
	Writer<StringBuffer> writer(s);
	writer.StartObject();

	int sn = addSeqNum(writer);

	writer.String("method");
	writer.String("onCommand");

	writer.String("id");
	writer.Uint(id);

	writer.String("type");
	writer.Uint(type);

	writer.EndObject();

	rapidjson::Document ret;
	sendRequest(s.GetString(), sn, ret);
	if (handleReply(ret)) {
		return ret["return"].GetBool();
	}
	return false;
}

bool Client::sendOnMenu(std::string button_id, rapidjson::Document& result) {
	StringBuffer s;
	Writer<StringBuffer> writer(s);
	writer.StartObject();

	int sn = addSeqNum(writer);

	writer.String("method");
	writer.String("onMenu");

	writer.String("id");
	writer.String(button_id);

	writer.EndObject();

	sendRequest(s.GetString(), sn, result);
	if (handleReply(result)) {
		return true;
	}
	return false;
}

static bool menuFromJson(ITfMenu* pMenu, rapidjson::Value& menuInfo) {
	if (pMenu != nullptr && menuInfo.IsArray()) {
		for (auto it = menuInfo.Begin(); it != menuInfo.End(); ++it) {
			rapidjson::Value& item = *it;
			UINT id = 0;
			auto prop_it = item.FindMember("id");
			if (prop_it != item.MemberEnd() && prop_it->value.IsInt())
				id = prop_it->value.GetInt();

			std::wstring text;
			prop_it = item.FindMember("text");
			if (prop_it != item.MemberEnd() && prop_it->value.IsString())
				text = utf8ToUtf16(prop_it->value.GetString());

			DWORD flags = 0;
			rapidjson::Value* submenuInfo = nullptr;
			ITfMenu* submenu = nullptr;
			if (id == 0 && text.empty())
				flags = TF_LBMENUF_SEPARATOR;
			else {
				prop_it = item.FindMember("checked");
				if (prop_it != item.MemberEnd() && prop_it->value.IsBool() && prop_it->value.GetBool())
					flags |= TF_LBMENUF_CHECKED;

				prop_it = item.FindMember("enabled");
				if (prop_it != item.MemberEnd() && prop_it->value.IsBool() && !prop_it->value.GetBool())
					flags |= TF_LBMENUF_GRAYED;

				prop_it = item.FindMember("submenu");
				if (prop_it != item.MemberEnd() && prop_it->value.IsArray()) {
					submenuInfo = &prop_it->value;
					flags |= TF_LBMENUF_SUBMENU;
				}
			}
			pMenu->AddMenuItem(id, flags, NULL, NULL, text.c_str(), text.length(), submenuInfo != nullptr ? &submenu : nullptr);
			if (submenu != nullptr && submenuInfo != nullptr) {
				menuFromJson(submenu, *submenuInfo);
			}
		}
		return true;
	}
	return false;
}

// called when a language bar button needs a menu
// virtual
bool Client::onMenu(LangBarButton* btn, ITfMenu* pMenu) {
	rapidjson::Document result;
	if(sendOnMenu(btn->id(), result)) {
		rapidjson::Value& menuInfo = result["return"];
		return menuFromJson(pMenu, menuInfo);
	}
	return false;
}

static HMENU menuFromJson(rapidjson::Value& menuInfo) {
	// TODO
	return NULL;
}

// called when a language bar button needs a menu
// virtual
HMENU Client::onMenu(LangBarButton* btn) {
	rapidjson::Document result;
	if (sendOnMenu(btn->id(), result)) {
		rapidjson::Value& menuInfo = result["return"];
		return menuFromJson(menuInfo);
	}
	return NULL;
}

// called when a compartment value is changed
void Client::onCompartmentChanged(const GUID& key) {
	LPOLESTR str = NULL;
	if (SUCCEEDED(::StringFromCLSID(key, &str))) {
		StringBuffer s;
		Writer<StringBuffer> writer(s);
		writer.StartObject();

		int sn = addSeqNum(writer);

		writer.String("method");
		writer.String("onCompartmentChanged");

		writer.String("guid");
		writer.String(utf16ToUtf8(str));
		::CoTaskMemFree(str);

		writer.EndObject();

		rapidjson::Document ret;
		sendRequest(s.GetString(), sn, ret);
		if (handleReply(ret)) {
		}
	}
}

// called when the keyboard is opened or closed
void Client::onKeyboardStatusChanged(bool opened) {
	StringBuffer s;
	Writer<StringBuffer> writer(s);
	writer.StartObject();

	int sn = addSeqNum(writer);

	writer.String("method");
	writer.String("onKeyboardStatusChanged");

	writer.String("opened");
	writer.Bool(opened);

	writer.EndObject();

	rapidjson::Document ret;
	sendRequest(s.GetString(), sn, ret);
	if (handleReply(ret)) {
	}
}

// called just before current composition is terminated for doing cleanup.
void Client::onCompositionTerminated(bool forced) {
	StringBuffer s;
	Writer<StringBuffer> writer(s);
	writer.StartObject();

	int sn = addSeqNum(writer);

	writer.String("method");
	writer.String("onCompositionTerminated");

	writer.String("forced");
	writer.Bool(forced);

	writer.EndObject();

	rapidjson::Document ret;
	sendRequest(s.GetString(), sn, ret);
	if (handleReply(ret)) {
	}
}

void Client::onLangProfileActivated(REFIID lang) {
	LPOLESTR str = NULL;
	if (SUCCEEDED(::StringFromCLSID(lang, &str))) {

		StringBuffer s;
		Writer<StringBuffer> writer(s);
		writer.StartObject();
		int sn = addSeqNum(writer);

		writer.String("method");
		writer.String("onLangProfileActivated");

		writer.String("guid");
		writer.String(utf16ToUtf8(str));
		::CoTaskMemFree(str);

		writer.EndObject();

		rapidjson::Document ret;
		sendRequest(s.GetString(), sn, ret);
		if (handleReply(ret)) {
		}
	}
}

void Client::onLangProfileDeactivated(REFIID lang) {
	LPOLESTR str = NULL;
	if (SUCCEEDED(::StringFromCLSID(lang, &str))) {
		StringBuffer s;
		Writer<StringBuffer> writer(s);
		writer.StartObject();
		int sn = addSeqNum(writer);

		writer.String("method");
		writer.String("onLangProfileDeactivated");

		writer.String("guid");
		writer.String(utf16ToUtf8(str));
		::CoTaskMemFree(str);

		writer.EndObject();

		rapidjson::Document ret;
		sendRequest(s.GetString(), sn, ret);
		if (handleReply(ret)) {
		}
	}
	LangBarButton::clearIconCache();
}

void Client::init() {
	StringBuffer s;
	Writer<StringBuffer> writer(s);
	writer.StartObject();

	int sn = addSeqNum(writer);

	writer.String("method");
	writer.String("init");

	writer.String("id"); // id of the input method
	writer.String("");

	writer.String("isWindows8Above");
	writer.Bool(textService_->imeModule()->isWindows8Above());

	writer.String("isMetroApp");
	writer.Bool(textService_->isMetroApp());

	writer.String("isUiLess");
	writer.Bool(textService_->isUiLess());

	writer.String("isConsole");
	writer.Bool(textService_->isConsole());

	writer.EndObject();

	rapidjson::Document ret;
	sendRequest(s.GetString(), sn, ret);
	if (handleReply(ret)) {
	}
}

bool PIME::Client::sendRequest(std::string req, int seqNo, rapidjson::Document & result) {
	std::string ret;
	if (connectPipe()) { // ensure that we're connected
		char buf[1024];
		DWORD rlen = 0;
		if(TransactNamedPipe(pipe_, (void*)req.c_str(), req.length(), buf, 1023, &rlen, NULL)) {
			buf[rlen] = '\0';
			ret = buf;
		}
		else { // error!
			if (GetLastError() != ERROR_MORE_DATA) {
				// unknown error happens, reset the pipe?
				closePipe();
				return false;
			}
			buf[rlen] = '\0';
			ret = buf;
			for (;;) {
				BOOL success = ReadFile(pipe_, buf, 1023, &rlen, NULL);
				if (!success && (GetLastError() != ERROR_MORE_DATA))
					break;
				buf[rlen] = '\0';
				ret += buf;
				if (success)
					break;
			}
		}
	}
	result.Parse(ret.c_str());
	return true;
}

bool Client::connectPipe() {
	if (pipe_ == INVALID_HANDLE_VALUE) { // the pipe is not connected
		wstring pipeName = L"\\\\.\\pipe\\";
		DWORD len = 0;
		::GetUserNameW(NULL, &len); // get the required size of the buffer
		if (len <= 0)
			return false;
		// add username to the pipe path so it won't clash with the other users' pipes
		unique_ptr<wchar_t> username(new wchar_t[len]);
		if (!::GetUserNameW(username.get(), &len))
			return false;
		pipeName += username.get();
		pipeName += L"\\PIME_pipe";
		for (;;) {
			pipe_ = CreateFile(pipeName.c_str(), GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, 0, NULL);
			if (pipe_ != INVALID_HANDLE_VALUE) {
				// security check: make sure that we're connecting to the correct server
				ULONG serverPid;
				if (GetNamedPipeServerProcessId(pipe_, &serverPid)) {
					// FIXME: check the command line of the server?
					// See this: http://www.codeproject.com/Articles/19685/Get-Process-Info-with-NtQueryInformationProcess
					// Too bad! Undocumented Windows internal API might be needed here. :-(
					break;
				}
			}
			if (GetLastError() != ERROR_PIPE_BUSY)
				return false;
			// All pipe instances are busy, so wait for 10 seconds.
			if (!WaitNamedPipe(pipeName.c_str(), 10000))
				return false;
		}
		// The pipe is connected; change to message-read mode.
		DWORD mode = PIPE_READMODE_MESSAGE;
		BOOL success = SetNamedPipeHandleState(pipe_, &mode, NULL, NULL);
		if (!success) {
			closePipe();
			return false;
		}
		init(); // send initialization info to the server
	}
	return true;
}

void Client::closePipe() {
	if (pipe_ != INVALID_HANDLE_VALUE) {
		DisconnectNamedPipe(pipe_);
		CloseHandle(pipe_);
		LangBarButton::clearIconCache();
		pipe_ = INVALID_HANDLE_VALUE;
	}
}


} // namespace PIME
