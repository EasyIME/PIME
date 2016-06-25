//
//	Copyright (C) 2015 - 2016 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
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
#include <json/json.h>

#include "PIMETextService.h"
#include <cstdlib>
#include <ctime>
#include <memory>

using namespace std;

namespace PIME {

Client::Client(TextService* service):
	textService_(service),
	pipe_(INVALID_HANDLE_VALUE),
	newSeqNum_(0) {
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
void Client::keyEventToJson(Ime::KeyEvent& keyEvent, Json::Value& jsonValue) {
	jsonValue["charCode"] = keyEvent.charCode();
	jsonValue["keyCode"] = keyEvent.keyCode();
	jsonValue["repeatCount"] = keyEvent.repeatCount();
	jsonValue["scanCode"] = keyEvent.scanCode();
	jsonValue["isExtended"] = keyEvent.isExtended();
	Json::Value keyStates(Json::arrayValue);
	const BYTE* states = keyEvent.keyStates();
	for(int i = 0; i < 256; ++i) {
		keyStates.append(states[i]);
	}
	jsonValue["keyStates"] = keyStates;
}

bool Client::handleReply(Json::Value& msg, Ime::EditSession* session) {
	bool success = msg.get("success", false).asBool();
	if (success) {
		updateStatus(msg, session);
	}
	return success;
}

void Client::updateUI(const Json::Value& data) {
	for (auto it = data.begin(); it != data.end(); ++it) {
		const char* name = it.memberName();
		const Json::Value& value = *it;
		if (value.isString() && strcmp(name, "candFontName") == 0) {
			wstring fontName = utf8ToUtf16(value.asCString());
			textService_->setCandFontName(fontName);
		}
		else if (value.isInt() && strcmp(name, "candFontSize") == 0) {
			textService_->setCandFontSize(value.asInt());
		}
		else if (value.isInt() && strcmp(name, "candPerRow") == 0) {
			textService_->setCandPerRow(value.asInt());
		}
		else if (value.isBool() && strcmp(name, "candUseCursor") == 0) {
			textService_->setCandUseCursor(value.asBool());
		}
	}
}

void Client::updateStatus(Json::Value& msg, Ime::EditSession* session) {
	// We need to handle ordering of some types of the requests.
	// For example, setCompositionCursor() should happen after setCompositionCursor().
	const Json::Value* commitStringVal = nullptr;
	const Json::Value* compositionStringVal = nullptr;
	const Json::Value* compositionCursorVal = nullptr;
	const Json::Value* candCursorVal = nullptr;

	for (auto it = msg.begin(); it != msg.end(); ++it) {
		const char* name = it.memberName();
		const Json::Value& value = *it;
		if (session != nullptr) { // if an edit session is available
			// commit string
			if (value.isString() && strcmp(name, "commitString") == 0) {
				commitStringVal = &value;
				continue;
			}
			else if (value.isString() && strcmp(name, "compositionString") == 0) {
				compositionStringVal = &value;
				continue;
			}
			else if (value.isInt() && strcmp(name, "compositionCursor") == 0) {
				compositionCursorVal = &value;
				continue;
			}
			else if (value.isArray() && strcmp(name, "candidateList") == 0) {
				// handle candidates
				// FIXME: directly access private member is dirty!!!
				vector<wstring>& candidates = textService_->candidates_;
				candidates.clear();
				for (auto cand_it = value.begin(); cand_it != value.end(); ++cand_it) {
					wstring cand = utf8ToUtf16(cand_it->asCString());
					candidates.push_back(cand);
				}
				textService_->updateCandidates(session);
				continue;
			}
			else if (value.isBool() && strcmp(name, "showCandidates") == 0) {
				bool showCandidates = value.asBool();
				if (showCandidates) {
					textService_->showCandidates(session);
				}
				else {
					textService_->hideCandidates();
				}
				continue;
			}
			else if (value.isInt() && strcmp(name, "candidateCursor") == 0) {
				candCursorVal = &value;
				continue;
			}
		}

		// language buttons
		if (value.isArray() && strcmp(name, "addButton") == 0) {
			for (auto btn_it = value.begin(); btn_it != value.end(); ++btn_it) {
				const Json::Value& btn = *btn_it;
				// FIXME: when to clear the id <=> button map??
				PIME::LangBarButton* langBtn = PIME::LangBarButton::fromJson(textService_, btn);
				if (langBtn != nullptr) {
					buttons_[langBtn->id()] = langBtn; // insert into the map
					textService_->addButton(langBtn);
					langBtn->Release();
				}
			}
		}
		else if (value.isArray() && strcmp(name, "removeButton") == 0) {
			// FIXME: handle windows-mode-icon
			for (auto btn_it = value.begin(); btn_it != value.end(); ++btn_it) {
				if (btn_it->isString()) {
					string id = btn_it->asString();
					auto map_it = buttons_.find(id);
					if (map_it != buttons_.end()) {
						textService_->removeButton(map_it->second);
						buttons_.erase(map_it); // remove from the map
					}
				}
			}
		}
		else if (value.isArray() && strcmp(name, "changeButton") == 0) {
			// FIXME: handle windows-mode-icon
			for (auto btn_it = value.begin(); btn_it != value.end(); ++btn_it) {
				const Json::Value& btn = *btn_it;
				if (btn.isObject()) {
					string id = btn["id"].asString();
					auto map_it = buttons_.find(id);
					if (map_it != buttons_.end()) {
						map_it->second->update(btn);
					}
				}
			}
		}
		else if (value.isArray() && strcmp(name, "addPreservedKey") == 0) {
			// preserved keys
			for (auto key_it = value.begin(); key_it != value.end(); ++key_it) {
				const Json::Value& key = *key_it;
				if (key.isObject()) {
					std::wstring guidStr = utf8ToUtf16(key["guid"].asCString());
					CLSID guid = { 0 };
					CLSIDFromString(guidStr.c_str(), &guid);
					UINT keyCode = key["keyCode"].asUInt();
					UINT modifiers = key["modifiers"].asUInt();
					textService_->addPreservedKey(keyCode, modifiers, guid);
				}
			}
		}
		else if (value.isArray() && strcmp(name, "removePreservedKey") == 0) {
			for (auto key_it = value.begin(); key_it != value.end(); ++key_it) {
				if (key_it->isString()) {
					std::wstring guidStr = utf8ToUtf16(key_it->asCString());
					CLSID guid = { 0 };
					CLSIDFromString(guidStr.c_str(), &guid);
					textService_->removePreservedKey(guid);
				}
			}
		}
		else if (value.isBool() && strcmp(name, "openKeyboard") == 0) {
			textService_->setKeyboardOpen(value.asBool());
		}
		// other configurations
		else if (value.isString() && strcmp(name, "setSelKeys") == 0) {
			// keys used to select candidates
			std::wstring selKeys = utf8ToUtf16(value.asCString());
			textService_->setSelKeys(selKeys);
		}
		else if (value.isObject() && strcmp(name, "customizeUI") == 0) {
			// customize the UI
			updateUI(value);
		}
		// show message
		else if (value.isObject() && strcmp(name, "showMessage") == 0) {
			const Json::Value& message = value["message"];
			const Json::Value& duration = value["duration"];
			if (message.isString() && duration.isInt()) {
				textService_->showMessage(session, utf8ToUtf16(message.asCString()), duration.asInt());
			}
		}
	}

	// handle comosition and commit strings
	if (session != nullptr) { // if an edit session is available
		bool endComposition = false;
		if (commitStringVal != nullptr) {
			std::wstring commitString = utf8ToUtf16(commitStringVal->asCString());
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
			std::wstring compositionString = utf8ToUtf16(compositionStringVal->asCString());
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
			int compositionCursor = compositionCursorVal->asInt();
			if (!textService_->isComposing()) {
				textService_->startComposition(session->context());
			}
			textService_->setCompositionCursor(session, compositionCursor);
		}
		if (candCursorVal != nullptr) {
			if (textService_->candidateWindow_ != nullptr) {
				textService_->candidateWindow_->setCurrentSel(candCursorVal->asInt());
			}
		}
		if (endComposition && session != nullptr) {
			textService_->endComposition(session->context());
		}
	}
}

// handlers for the text service
void Client::onActivate() {
	Json::Value req;
	req["method"] = "onActivate";
	req["isKeyboardOpen"] = textService_->isKeyboardOpened();

	Json::Value ret;
	sendRequest(req, ret);
	if (handleReply(ret)) {
	}
}

void Client::onDeactivate() {
	Json::Value req;
	req["method"] = "onDeactivate";

	Json::Value ret;
	sendRequest(req, ret);
	if (handleReply(ret)) {
	}
	LangBarButton::clearIconCache();
}

bool Client::filterKeyDown(Ime::KeyEvent& keyEvent) {
	Json::Value req;
	req["method"] = "filterKeyDown";
	keyEventToJson(keyEvent, req);

	Json::Value ret;
	sendRequest(req, ret);
	if (handleReply(ret)) {
		return ret["return"].asBool();
	}
	return false;
}

bool Client::onKeyDown(Ime::KeyEvent& keyEvent, Ime::EditSession* session) {
	Json::Value req;
	req["method"] = "onKeyDown";
	keyEventToJson(keyEvent, req);

	Json::Value ret;
	sendRequest(req, ret);
	if (handleReply(ret, session)) {
		return ret["return"].asBool();
	}
	return false;
}

bool Client::filterKeyUp(Ime::KeyEvent& keyEvent) {
	Json::Value req;
	req["method"] = "filterKeyUp";
	keyEventToJson(keyEvent, req);

	Json::Value ret;
	sendRequest(req, ret);
	if (handleReply(ret)) {
		return ret["return"].asBool();
	}
	return false;
}

bool Client::onKeyUp(Ime::KeyEvent& keyEvent, Ime::EditSession* session) {
	Json::Value req;
	req["method"] = "onKeyUp";
	keyEventToJson(keyEvent, req);

	Json::Value ret;
	sendRequest(req, ret);
	if (handleReply(ret, session)) {
		return ret["return"].asBool();
	}
	return false;
}

bool Client::onPreservedKey(const GUID& guid) {
	LPOLESTR str = NULL;
	if (SUCCEEDED(::StringFromCLSID(guid, &str))) {
		Json::Value req;
		req["method"] = "onPreservedKey";
		req["guid"] = utf16ToUtf8(str);
		::CoTaskMemFree(str);

		Json::Value ret;
		sendRequest(req, ret);
		if (handleReply(ret)) {
			return ret["return"].asBool();
		}
	}
	return false;
}

bool Client::onCommand(UINT id, Ime::TextService::CommandType type) {
	Json::Value req;
	req["method"] = "onCommand";
	req["id"] = id;
	req["type"] = type;

	Json::Value ret;
	sendRequest(req, ret);
	if (handleReply(ret)) {
		return ret["return"].asBool();
	}
	return false;
}

bool Client::sendOnMenu(std::string button_id, Json::Value& result) {
	Json::Value req;
	req["method"] = "onMenu";
	req["id"] = button_id;

	sendRequest(req, result);
	if (handleReply(result)) {
		return true;
	}
	return false;
}

static bool menuFromJson(ITfMenu* pMenu, const Json::Value& menuInfo) {
	if (pMenu != nullptr && menuInfo.isArray()) {
		for (Json::Value::const_iterator it = menuInfo.begin(); it != menuInfo.end(); ++it) {
			const Json::Value& item = *it;
			UINT id = item.get("id", 0).asUInt();
			std::wstring text = utf8ToUtf16(item.get("text", "").asCString());
			
			DWORD flags = 0;
			Json::Value submenuInfo;
			ITfMenu* submenu = nullptr;
			if (id == 0 && text.empty())
				flags = TF_LBMENUF_SEPARATOR;
			else {
				if (item.get("checked", false).asBool())
					flags |= TF_LBMENUF_CHECKED;
				if (!item.get("enabled", true).asBool())
					flags |= TF_LBMENUF_GRAYED;

				submenuInfo = item["submenu"];  // FIXME: this is a deep copy. too bad! :-(
				if (submenuInfo.isArray()) {
					flags |= TF_LBMENUF_SUBMENU;
				}
			}
			pMenu->AddMenuItem(id, flags, NULL, NULL, text.c_str(), text.length(), flags & TF_LBMENUF_SUBMENU ? &submenu : nullptr);
			if (submenu != nullptr && submenuInfo.isArray()) {
				menuFromJson(submenu, submenuInfo);
			}
		}
		return true;
	}
	return false;
}

// called when a language bar button needs a menu
// virtual
bool Client::onMenu(LangBarButton* btn, ITfMenu* pMenu) {
	Json::Value result;
	if(sendOnMenu(btn->id(), result)) {
		Json::Value& menuInfo = result["return"];
		return menuFromJson(pMenu, menuInfo);
	}
	return false;
}

static HMENU menuFromJson(const Json::Value& menuInfo) {
	if (menuInfo.isArray()) {
		HMENU menu = ::CreatePopupMenu();
		for (auto it = menuInfo.begin(); it != menuInfo.end(); ++it) {
			const Json::Value& item = *it;
			UINT id = item.get("id", 0).asUInt();
			std::wstring text = utf8ToUtf16(item.get("text", "").asCString());

			UINT flags = MF_STRING;
			if (id == 0 && text.empty())
				flags = MF_SEPARATOR;
			else {
				if (item.get("checked", false).asBool())
					flags |= MF_CHECKED;
				if (!item.get("enabled", true).asBool())
					flags |= MF_GRAYED;

				const Json::Value& subMenuValue = item.get("submenu", Json::nullValue);
				if (subMenuValue.isArray()) {
					HMENU submenu = menuFromJson(subMenuValue);
					flags |= MF_POPUP;
					id = UINT_PTR(submenu);
				}
			}
			AppendMenu(menu, flags, id, text.c_str());
		}
		return menu;
	}
	return NULL;
}

// called when a language bar button needs a menu
// virtual
HMENU Client::onMenu(LangBarButton* btn) {
	Json::Value result;
	if (sendOnMenu(btn->id(), result)) {
		Json::Value& menuInfo = result["return"];
		return menuFromJson(menuInfo);
	}
	return NULL;
}

// called when a compartment value is changed
void Client::onCompartmentChanged(const GUID& key) {
	LPOLESTR str = NULL;
	if (SUCCEEDED(::StringFromCLSID(key, &str))) {
		Json::Value req;
		req["method"] = "onCompartmentChanged";
		req["guid"] = utf16ToUtf8(str);
		::CoTaskMemFree(str);

		Json::Value ret;
		sendRequest(req, ret);
		if (handleReply(ret)) {
		}
	}
}

// called when the keyboard is opened or closed
void Client::onKeyboardStatusChanged(bool opened) {
	Json::Value req;
	req["method"] = "onKeyboardStatusChanged";
	req["opened"] = opened;

	Json::Value ret;
	sendRequest(req, ret);
	if (handleReply(ret)) {
	}
}

// called just before current composition is terminated for doing cleanup.
void Client::onCompositionTerminated(bool forced) {
	Json::Value req;
	req["method"] = "onCompositionTerminated";
	req["forced"] = forced;

	Json::Value ret;
	sendRequest(req, ret);
	if (handleReply(ret)) {
	}
}

void Client::onLangProfileActivated(REFIID lang) {
	LPOLESTR str = NULL;
	if (SUCCEEDED(::StringFromCLSID(lang, &str))) {
		Json::Value req;
		req["method"] = "onLangProfileActivated";
		req["guid"] = utf16ToUtf8(str);
		::CoTaskMemFree(str);

		Json::Value ret;
		sendRequest(req, ret);
		if (handleReply(ret)) {
		}
	}
}

void Client::onLangProfileDeactivated(REFIID lang) {
	LPOLESTR str = NULL;
	if (SUCCEEDED(::StringFromCLSID(lang, &str))) {
		Json::Value req;
		req["method"] = "onLangProfileDeactivated";
		req["guid"] = utf16ToUtf8(str);
		::CoTaskMemFree(str);

		Json::Value ret;
		sendRequest(req, ret);
		if (handleReply(ret)) {
		}
	}
	LangBarButton::clearIconCache();
}

void Client::init() {
	Json::Value req;
	req["method"] = "init";
	req["id"] = "";
	req["isWindows8Above"] = textService_->imeModule()->isWindows8Above();
	req["isMetroApp"] = textService_->isMetroApp();
	req["isUiLess"] = textService_->isUiLess();
	req["isConsole"] = textService_->isConsole();

	Json::Value ret;
	sendRequest(req, ret);
	if (handleReply(ret)) {
	}
}

// send the request to the server
// a sequence number will be added to the req object automatically.
bool PIME::Client::sendRequest(Json::Value& req, Json::Value & result) {
	unsigned int seqNum = newSeqNum_++;
	req["seqNum"] = seqNum; // add a sequence number for the request

	std::string ret;
	if (connectPipe()) { // ensure that we're connected
		char buf[1024];
		DWORD rlen = 0;
		Json::FastWriter writer;
		std::string reqStr = writer.write(req); // convert the json object to string
		if(TransactNamedPipe(pipe_, (void*)reqStr.c_str(), reqStr.length(), buf, 1023, &rlen, NULL)) {
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
	Json::Reader reader;
	bool success = reader.parse(ret, result);
	if (success) {
		if (result["seqNum"].asUInt() != seqNum) // sequence number mismatch
			success = false;
	}
	return success;
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
