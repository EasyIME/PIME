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
#include <fstream>
#include <cctype>
#include <algorithm>
#include <Winnls.h>  // for IS_HIGH_SURROGATE() macro for checking UTF16 surrogate pairs

using namespace std;

namespace PIME {

Client::Client(TextService* service, REFIID langProfileGuid):
	textService_(service),
	pipe_(INVALID_HANDLE_VALUE),
	newSeqNum_(0),
	isActivated_(false),
	connectingServerPipe_(false) {

	LPOLESTR guidStr = NULL;
	if (SUCCEEDED(::StringFromCLSID(langProfileGuid, &guidStr))) {
		guid_ = utf16ToUtf8(guidStr);
		transform(guid_.begin(), guid_.end(), guid_.begin(), tolower);  // convert GUID to lwoer case
		::CoTaskMemFree(guidStr);
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

	// set sel keys before update candidates
	const auto& setSelKeysVal = msg["setSelKeys"];
	if (setSelKeysVal.isString()) {
		// keys used to select candidates
		std::wstring selKeys = utf8ToUtf16(setSelKeysVal.asCString());
		textService_->setSelKeys(selKeys);
	}

	// show message
    bool endComposition = false;
	const auto& showMessageVal = msg["showMessage"];
	if (showMessageVal.isObject()) {
		const Json::Value& message = showMessageVal["message"];
		const Json::Value& duration = showMessageVal["duration"];
		if (message.isString() && duration.isInt()) {
			if (!textService_->isComposing()) {
				textService_->startComposition(session->context());
                endComposition = true;
			}
			textService_->showMessage(session, utf8ToUtf16(message.asCString()), duration.asInt());
		}
	}

	if (session != nullptr) { // if an edit session is available
		// handle candidate list
		const auto& showCandidatesVal = msg["showCandidates"];
		if (showCandidatesVal.isBool()) {
			if (showCandidatesVal.asBool()) {
				// start composition if we are not composing.
				// this is required to get correctly position the candidate window
				if (!textService_->isComposing()) {
					textService_->startComposition(session->context());
				}
				textService_->showCandidates(session);
			}
			else {
				textService_->hideCandidates();
			}
		}

		const auto& candidateListVal = msg["candidateList"];
		if (candidateListVal.isArray()) {
			// handle candidates
			// FIXME: directly access private member is dirty!!!
			vector<wstring>& candidates = textService_->candidates_;
			candidates.clear();
			for (auto cand_it = candidateListVal.begin(); cand_it != candidateListVal.end(); ++cand_it) {
				wstring cand = utf8ToUtf16(cand_it->asCString());
				candidates.push_back(cand);
			}
			textService_->updateCandidates(session);
			if (!showCandidatesVal.asBool()) {
				textService_->hideCandidates();
			}
		}

		const auto& candidateCursorVal = msg["candidateCursor"];
		if (candidateCursorVal.isInt()) {
			if (textService_->candidateWindow_ != nullptr) {
				textService_->candidateWindow_->setCurrentSel(candidateCursorVal.asInt());
				textService_->refreshCandidates();
			}
		}

		// handle comosition and commit strings
		const auto& commitStringVal = msg["commitString"];
		if (commitStringVal.isString()) {
			std::wstring commitString = utf8ToUtf16(commitStringVal.asCString());
			if (!commitString.empty()) {
				if (!textService_->isComposing()) {
					textService_->startComposition(session->context());
				}
				textService_->setCompositionString(session, commitString.c_str(), commitString.length());
				textService_->endComposition(session->context());
			}
		}

		const auto& compositionStringVal = msg["compositionString"];
		bool emptyComposition = false;
		bool hasCompositionString = false;
		std::wstring compositionString;
		if (compositionStringVal.isString()) {
			// composition buffer
			compositionString = utf8ToUtf16(compositionStringVal.asCString());
			hasCompositionString = true;
			if (compositionString.empty()) {
				emptyComposition = true;
				if (textService_->isComposing() && !textService_->showingCandidates()) {
					// when the composition buffer is empty and we are not showing the candidate list, end composition.
					textService_->setCompositionString(session, L"", 0);
					endComposition = true;
				}
			}
			else {
				if (!textService_->isComposing()) {
					textService_->startComposition(session->context());
				}
				textService_->setCompositionString(session, compositionString.c_str(), compositionString.length());
			}
		}

		const auto& compositionCursorVal = msg["compositionCursor"];
		if (compositionCursorVal.isInt()) {
			// composition cursor
			if (!emptyComposition) {
				int compositionCursor = compositionCursorVal.asInt();
				if (!textService_->isComposing()) {
					textService_->startComposition(session->context());
				}
				// NOTE:
				// This fixes PIME bug #166: incorrect handling of UTF-16 surrogate pairs.
				// The TSF API unfortunately treat a UTF-16 surrogate pair as two characters while
				// they actually represent one unicode character only. To workaround this TSF bug,
				// we get the composition string, and try to move the cursor twice when a UTF-16
				// surrogate pair is found.
				if(!hasCompositionString)
					compositionString = textService_->compositionString(session);
				int fixedCursorPos = 0;
				for (int i = 0; i < compositionCursor; ++i) {
					++fixedCursorPos;
					if (IS_HIGH_SURROGATE(compositionString[i])) // this is the first part of a UTF16 surrogate pair (Windows uses UTF16-LE)
						++fixedCursorPos;
				}
				textService_->setCompositionCursor(session, fixedCursorPos);
			}
		}

		if (endComposition) {
			textService_->endComposition(session->context());
		}
	}

	// language buttons
	const auto& addButtonVal = msg["addButton"];
	if (addButtonVal.isArray()) {
		for (auto btn_it = addButtonVal.begin(); btn_it != addButtonVal.end(); ++btn_it) {
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
	
	const auto& removeButtonVal = msg["removeButton"];
	if (removeButtonVal.isArray()) {
		// FIXME: handle windows-mode-icon
		for (auto btn_it = removeButtonVal.begin(); btn_it != removeButtonVal.end(); ++btn_it) {
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

	const auto& changeButtonVal = msg["changeButton"];
	if (changeButtonVal.isArray()) {
		// FIXME: handle windows-mode-icon
		for (auto btn_it = changeButtonVal.begin(); btn_it != changeButtonVal.end(); ++btn_it) {
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

	// preserved keys
	const auto& addPreservedKeyVal = msg["addPreservedKey"];
	if (addPreservedKeyVal.isArray()) {
		// preserved keys
		for (auto key_it = addPreservedKeyVal.begin(); key_it != addPreservedKeyVal.end(); ++key_it) {
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
	
	const auto& removePreservedKeyVal = msg["removePreservedKey"];
	if (removePreservedKeyVal.isArray()) {
		for (auto key_it = removePreservedKeyVal.begin(); key_it != removePreservedKeyVal.end(); ++key_it) {
			if (key_it->isString()) {
				std::wstring guidStr = utf8ToUtf16(key_it->asCString());
				CLSID guid = { 0 };
				CLSIDFromString(guidStr.c_str(), &guid);
				textService_->removePreservedKey(guid);
			}
		}
	}

	// keyboard status
	const auto& openKeyboardVal = msg["openKeyboard"];
	if (openKeyboardVal.isBool()) {
		textService_->setKeyboardOpen(openKeyboardVal.asBool());
	}

	// other configurations
	const auto& customizeUIVal = msg["customizeUI"];
	if (customizeUIVal.isObject()) {
		// customize the UI
		updateUI(customizeUIVal);
	}

	// hide message
    const auto& hideMessageVal = msg["hideMessage"];
	if (hideMessageVal.isBool()) {
        textService_->hideMessage();
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
	isActivated_ = true;
}

void Client::onDeactivate() {
	Json::Value req;
	req["method"] = "onDeactivate";

	Json::Value ret;
	sendRequest(req, ret);
	if (handleReply(ret)) {
	}
	LangBarButton::clearIconCache();
	isActivated_ = false;
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

void Client::init() {
	Json::Value req;
	req["method"] = "init";
	req["id"] = guid_.c_str();  // language profile guid
	req["isWindows8Above"] = textService_->imeModule()->isWindows8Above();
	req["isMetroApp"] = textService_->isMetroApp();
	req["isUiLess"] = textService_->isUiLess();
	req["isConsole"] = textService_->isConsole();

	Json::Value ret;
	sendRequest(req, ret);
	if (handleReply(ret)) {
	}
}

bool Client::sendRequestText(HANDLE pipe, const char* data, int len, std::string& reply) {
	char buf[1024];
	DWORD rlen = 0;
	if (TransactNamedPipe(pipe, (void*)data, len, buf, sizeof(buf) - 1, &rlen, NULL)) {
		buf[rlen] = '\0';
		reply = buf;
	}
	else { // error!
		if (GetLastError() != ERROR_MORE_DATA) { // unknown error happens
			return false;
		}
		// still has more data to read
		buf[rlen] = '\0';
		reply = buf;
		for (;;) {
			BOOL success = ReadFile(pipe, buf, sizeof(buf) - 1, &rlen, NULL);
			if (!success && (GetLastError() != ERROR_MORE_DATA)) {
				// unknown error happens, reset the pipe?
				return false; // error reading the pipe
			}
			buf[rlen] = '\0';
			reply += buf;
			if (success)
				break;
		}
	}
	return true;
}

// send the request to the server
// a sequence number will be added to the req object automatically.
bool Client::sendRequest(Json::Value& req, Json::Value & result) {
	bool success = false;
	unsigned int seqNum = newSeqNum_++;
	req["seqNum"] = seqNum; // add a sequence number for the request
	std::string ret;
	DWORD rlen = 0;
	Json::FastWriter writer;
	std::string reqStr = writer.write(req); // convert the json object to string

	for (int retry_connect = 1; retry_connect >= 0; --retry_connect) {
		if (!connectingServerPipe_) {  // if we're not in the middle of initializing the pipe connection
			if (!connectServerPipe()) {  // ensure that we're connected
				continue;
			}
		}
		// now we should be connected. if not, it's an error.
		if (pipe_ == INVALID_HANDLE_VALUE)
			break;

		if (sendRequestText(pipe_, reqStr.c_str(), reqStr.length(), ret)) {
			Json::Reader reader;
			success = reader.parse(ret, result);
			if (success) {
				if (result["seqNum"].asUInt() != seqNum) // sequence number mismatch
					success = false;
			}
			break; // send request succeeded, no more retries
		}
		else { // fail to send the request to the server
			if (connectingServerPipe_) { // we're in the middle of initializing the pipe connection
				break; // fail directly
			}
			else {
				closePipe(); // close the pipe connection and try again
			}
		}
	};
	return success;
}

// establish a connection to the specified pipe and returns its handle
HANDLE Client::connectPipe(const wchar_t* pipeName) {
	bool hasErrors = false;
	HANDLE pipe = INVALID_HANDLE_VALUE;
	for (;;) {
		pipe = CreateFile(pipeName, GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, 0, NULL);
		if (pipe != INVALID_HANDLE_VALUE) {
			// the pipe is successfully created
			// security check: make sure that we're connecting to the correct server
			ULONG serverPid;
			if (GetNamedPipeServerProcessId(pipe, &serverPid)) {
				// FIXME: check the command line of the server?
				// See this: http://www.codeproject.com/Articles/19685/Get-Process-Info-with-NtQueryInformationProcess
				// Too bad! Undocumented Windows internal API might be needed here. :-(
			}
			break;
		}
		// being busy is not really an error since we just need to wait.
		if (GetLastError() != ERROR_PIPE_BUSY) {
			hasErrors = true; // otherwise, pipe creation fails
			break;
		}
		// All pipe instances are busy, so wait for 2 seconds.
		if (!WaitNamedPipe(pipeName, 2000)) {
			hasErrors = true;
			break;
		}
	}

	if (!hasErrors) {
		// The pipe is connected; change to message-read mode.
		DWORD mode = PIPE_READMODE_MESSAGE;
		if (!SetNamedPipeHandleState(pipe, &mode, NULL, NULL)) {
			hasErrors = true;
		}
	}

	// the pipe is created, but errors happened, destroy it.
	if (hasErrors && pipe != INVALID_HANDLE_VALUE) {
		DisconnectNamedPipe(pipe);
		CloseHandle(pipe);
		pipe = INVALID_HANDLE_VALUE;
	}
	return pipe;
}


// Ensure that we're connected to the PIME input method server
// If we are already connected, the method simply returns true;
// otherwise, it tries to establish the connection.
bool Client::connectServerPipe() {
	if (pipe_ == INVALID_HANDLE_VALUE) { // the pipe is not connected
		connectingServerPipe_ = true;
		wstring serverPipeName = getPipeName(L"Launcher");
		// try to connect to the server
		pipe_ = connectPipe(serverPipeName.c_str());

		if (pipe_ != INVALID_HANDLE_VALUE) { // successfully connected to the server
			init(); // send initialization info to the server
			if (isActivated_) {
				// we lost connection while being activated previously
				// re-initialize the whole text service.

				// cleanup for the previous instance.
				// remove all buttons
				for (auto it = buttons_.begin(); it != buttons_.end(); ++it) {
					textService_->removeButton(it->second);
				}
				buttons_.clear();

				// FIXME: other cleanup might also be needed

				// activate the text service again.
				onActivate();
			}
		}
		connectingServerPipe_ = false;
		return (pipe_ != INVALID_HANDLE_VALUE);
	}
	return true;
}

void Client::closePipe() {
	if (pipe_ != INVALID_HANDLE_VALUE) {
		DisconnectNamedPipe(pipe_);
		CloseHandle(pipe_);
		pipe_ = INVALID_HANDLE_VALUE;
	}
}

wstring Client::getPipeName(const wchar_t* base_name) {
	wstring pipeName = L"\\\\.\\pipe\\";
	DWORD len = 0;
	::GetUserNameW(NULL, &len); // get the required size of the buffer
	if (len <= 0)
		return false;
	// add username to the pipe path so it won't clash with the other users' pipes
	unique_ptr<wchar_t[]> username(new wchar_t[len]);
	if (!::GetUserNameW(username.get(), &len))
		return false;
	pipeName += username.get();
	pipeName += L"\\PIME\\";
	pipeName += base_name;
	return pipeName;
}


} // namespace PIME
