//
//	Copyright (C) 2015 - 2020 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
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
#include "libIME2/src/Utils.h"
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
#include <VersionHelpers.h>  // Provided by Windows SDK >= 8.1

using namespace std;

namespace PIME {

static std::string uuidToString(const UUID& uuid) {
    std::string result;
    LPOLESTR buf = nullptr;
    if (SUCCEEDED(::StringFromCLSID(uuid, &buf))) {
        result = utf16ToUtf8(buf);
        ::CoTaskMemFree(buf);
        // convert GUID to lwoer case
        transform(result.begin(), result.end(), result.begin(), tolower);
    }
    return result;
}

bool uuidFromString(const char* uuidStr, UUID& result) {
    std::wstring utf16UuidStr = utf8ToUtf16(uuidStr);
    return SUCCEEDED(CLSIDFromString(utf16UuidStr.c_str(), &result));
}


Client::Client(TextService* service, REFIID langProfileGuid):
	textService_(service),
	pipe_(INVALID_HANDLE_VALUE),
	nextSeqNum_(0),
	isActivated_(false),
    guid_{uuidToString(langProfileGuid)},
    shouldWaitConnection_{true} {
}

Client::~Client(void) {
	closeRpcConnection();
    resetTextServiceState();
	LangBarButton::clearIconCache();
}

// pack a keyEvent object into a json value
//static
void Client::addKeyEventToRpcRequest(Json::Value& request, Ime::KeyEvent& keyEvent) {
	request["charCode"] = keyEvent.charCode();
	request["keyCode"] = keyEvent.keyCode();
	request["repeatCount"] = keyEvent.repeatCount();
	request["scanCode"] = keyEvent.scanCode();
	request["isExtended"] = keyEvent.isExtended();
	Json::Value keyStates(Json::arrayValue);
	const BYTE* states = keyEvent.keyStates();
	for(int i = 0; i < 256; ++i) {
		keyStates.append(states[i]);
	}
	request["keyStates"] = keyStates;
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
			for (const auto& candidate: candidateListVal) {
				candidates.emplace_back(utf8ToUtf16(candidate.asCString()));
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
                // FIXME: update the position of candidate and message window when the composition string is changed.
                if (textService_->candidateWindow_ != nullptr) {
                    textService_->updateCandidatesWindow(session);
                }
                if (textService_->messageWindow_ != nullptr) {
                    textService_->updateMessageWindow(session);
                }
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
            // FIXME: update the position of candidate and message window when the composition string is changed.
            if (textService_->candidateWindow_ != nullptr) {
                textService_->updateCandidatesWindow(session);
            }
            if (textService_->messageWindow_ != nullptr) {
                textService_->updateMessageWindow(session);
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
		for (const auto& btn: addButtonVal) {
			// FIXME: when to clear the id <=> button map??
			auto langBtn = Ime::ComPtr<PIME::LangBarButton>::takeover(PIME::LangBarButton::fromJson(textService_, btn));
			if (langBtn != nullptr) {
				buttons_.emplace(langBtn->id(), langBtn); // insert into the map
				textService_->addButton(langBtn);
			}
		}
	}

	const auto& removeButtonVal = msg["removeButton"];
	if (removeButtonVal.isArray()) {
		// FIXME: handle windows-mode-icon
        for (const auto& btn : removeButtonVal) {
            if (btn.isString()) {
				string id = btn.asString();
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
		for (const auto& btn: changeButtonVal) {
			if (btn.isObject()) {
				string id = btn["id"].asString();
				auto map_it = buttons_.find(id);
				if (map_it != buttons_.end()) {
					map_it->second->updateFromJson(btn);
				}
			}
		}
	}

	// preserved keys
	const auto& addPreservedKeyVal = msg["addPreservedKey"];
	if (addPreservedKeyVal.isArray()) {
		// preserved keys
		for (auto& key: addPreservedKeyVal) {
			if (key.isObject()) {
				UINT keyCode = key["keyCode"].asUInt();
				UINT modifiers = key["modifiers"].asUInt();
                UUID guid = { 0 };
                if (uuidFromString(key["guid"].asCString(), guid)) {
                    textService_->addPreservedKey(keyCode, modifiers, guid);
                }
			}
		}
	}
	
	const auto& removePreservedKeyVal = msg["removePreservedKey"];
	if (removePreservedKeyVal.isArray()) {
		for (auto& key: removePreservedKeyVal) {
			if (key.isString()) {
				UUID guid = { 0 };
                if (uuidFromString(key["guid"].asCString(), guid)) {
                    textService_->removePreservedKey(guid);
                }
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
    Json::Value req = createRpcRequest("onActivate");
	req["isKeyboardOpen"] = textService_->isKeyboardOpened();

	Json::Value ret;
	callRpcMethod(req, ret);
	if (handleReply(ret)) {
	}
	isActivated_ = true;
}

void Client::onDeactivate() {
    Json::Value req = createRpcRequest("onDeactivate");
	Json::Value ret;
	callRpcMethod(req, ret);
	if (handleReply(ret)) {
	}
	LangBarButton::clearIconCache();
	isActivated_ = false;
}

bool Client::filterKeyDown(Ime::KeyEvent& keyEvent) {
    Json::Value req = createRpcRequest("filterKeyDown");
	addKeyEventToRpcRequest(req, keyEvent);

	Json::Value ret;
	callRpcMethod(req, ret);
	if (handleReply(ret)) {
		return ret["return"].asBool();
	}
	return false;
}

bool Client::onKeyDown(Ime::KeyEvent& keyEvent, Ime::EditSession* session) {
    Json::Value req = createRpcRequest("onKeyDown");
	addKeyEventToRpcRequest(req, keyEvent);

	Json::Value ret;
	callRpcMethod(req, ret);
	if (handleReply(ret, session)) {
		return ret["return"].asBool();
	}
	return false;
}

bool Client::filterKeyUp(Ime::KeyEvent& keyEvent) {
    Json::Value req = createRpcRequest("filterKeyUp");
	addKeyEventToRpcRequest(req, keyEvent);

	Json::Value ret;
	callRpcMethod(req, ret);
	if (handleReply(ret)) {
		return ret["return"].asBool();
	}
	return false;
}

bool Client::onKeyUp(Ime::KeyEvent& keyEvent, Ime::EditSession* session) {
    Json::Value req = createRpcRequest("onKeyUp");
	addKeyEventToRpcRequest(req, keyEvent);

	Json::Value ret;
	callRpcMethod(req, ret);
	if (handleReply(ret, session)) {
		return ret["return"].asBool();
	}
	return false;
}

bool Client::onPreservedKey(const GUID& guid) {
    auto guidStr = uuidToString(guid);
	if (!guidStr.empty()) {
        Json::Value req = createRpcRequest("onPreservedKey");
        req["guid"] = std::move(guidStr);

		Json::Value ret;
		callRpcMethod(req, ret);
		if (handleReply(ret)) {
			return ret["return"].asBool();
		}
	}
	return false;
}

bool Client::onCommand(UINT id, Ime::TextService::CommandType type) {
    Json::Value req = createRpcRequest("onCommand");
	req["id"] = id;
	req["type"] = type;

	Json::Value ret;
	callRpcMethod(req, ret);
	if (handleReply(ret)) {
		return ret["return"].asBool();
	}
	return false;
}

bool Client::sendOnMenu(std::string button_id, Json::Value& result) {
    Json::Value req = createRpcRequest("onMenu");
	req["id"] = button_id;

	callRpcMethod(req, result);
	if (handleReply(result)) {
		return true;
	}
	return false;
}

static bool menuFromJson(ITfMenu* pMenu, const Json::Value& menuInfo) {
	if (pMenu != nullptr && menuInfo.isArray()) {
		for (const auto& item: menuInfo) {
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
		for (const auto& item: menuInfo) {
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
    auto guidStr = uuidToString(key);
	if (!guidStr.empty()) {
        Json::Value req = createRpcRequest("onCompartmentChanged");
        req["guid"] = std::move(guidStr);

		Json::Value ret;
		callRpcMethod(req, ret);
		if (handleReply(ret)) {
		}
	}
}

// called when the keyboard is opened or closed
void Client::onKeyboardStatusChanged(bool opened) {
    Json::Value req = createRpcRequest("onKeyboardStatusChanged");
	req["opened"] = opened;

	Json::Value ret;
	callRpcMethod(req, ret);
	if (handleReply(ret)) {
	}
}

// called just before current composition is terminated for doing cleanup.
void Client::onCompositionTerminated(bool forced) {
    Json::Value req = createRpcRequest("onCompositionTerminated");
	req["forced"] = forced;

	Json::Value ret;
	callRpcMethod(req, ret);
	if (handleReply(ret)) {
	}
}

bool Client::init() {
    Json::Value req = createRpcRequest("init");
	req["id"] = guid_.c_str();  // language profile guid
	req["isWindows8Above"] = ::IsWindows8OrGreater();
	req["isMetroApp"] = textService_->isMetroApp();
	req["isUiLess"] = textService_->isUiLess();
	req["isConsole"] = textService_->isConsole();

	Json::Value ret;
    return callRpcMethod(req, ret) && handleReply(ret);
}


Json::Value Client::createRpcRequest(const char* methodName) {
    Json::Value request;
    request["method"] = methodName;

    // TODO: add other environment info?
    return request;
}

bool Client::callRpcPipe(HANDLE pipe, const std::string& serializedRequest, std::string& serializedReply) {
	char buf[1024];
	DWORD rlen = 0;
    bool hasMoreData = false;
    if (!TransactNamedPipe(pipe, (void*)serializedRequest.data(), serializedRequest.size(), buf, sizeof(buf), &rlen, NULL)) {
        if (GetLastError() == ERROR_MORE_DATA) {
            hasMoreData = true;
        }
        else {  // unknown error
            return false;
        }
    }
    serializedReply.append(buf, rlen);

    while (hasMoreData) {
        if (ReadFile(pipe, buf, sizeof(buf), &rlen, NULL)) {
            hasMoreData = false;
        }
        else if (::GetLastError() != ERROR_MORE_DATA) {  // unknown error
            return false;
        }
        serializedReply.append(buf, rlen);
    }
	return true;
}

// send the request to the server
// a sequence number will be added to the req object automatically.
bool Client::callRpcMethod(Json::Value& request, Json::Value & response) {
    if (shouldWaitConnection_ && !waitForRpcConnection()) {
        return false;
    }

    // Add a sequence number for the request.
    auto seqNum = nextSeqNum_++;
    request["seqNum"] = seqNum;

	Json::FastWriter writer;
	std::string serializedRequest = writer.write(request); // convert the json object to string

    std::string serializedResponse;
    bool success = false;
    if (callRpcPipe(pipe_, serializedRequest, serializedResponse)) {
		Json::Reader reader;
		success = reader.parse(serializedResponse, response);
		if (success) {
			if (response["seqNum"].asUInt() != seqNum) // sequence number mismatch
				success = false;
		}
	}
    else {
        success = false;
    }

	if(!success) { // fail to send the request to the server
		closeRpcConnection(); // close the pipe connection since it's broken
        resetTextServiceState();  // since we lost the connection, the state is unknonw so we reset.
	}
	return success;
}

bool Client::isPipeCreatedByPIMEServer(HANDLE pipe) {
    // security check: make sure that we're connecting to the correct server
    ULONG serverPid;
    if (GetNamedPipeServerProcessId(pipe, &serverPid)) {
        // FIXME: check the command line of the server?
        // See this: http://www.codeproject.com/Articles/19685/Get-Process-Info-with-NtQueryInformationProcess
        // Too bad! Undocumented Windows internal API might be needed here. :-(
    }
    return true;
}

// establish a connection to the specified pipe and returns its handle
// static
HANDLE Client::connectPipe(const wchar_t* pipeName, int timeoutMs) {
    HANDLE pipe = INVALID_HANDLE_VALUE;
    if (WaitNamedPipe(pipeName, timeoutMs)) {
        pipe = CreateFile(pipeName, GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, 0, NULL);
    }

    if (pipe != INVALID_HANDLE_VALUE) {
        DWORD mode = PIPE_READMODE_MESSAGE;
        // The pipe is connected; change to message-read mode.
        if (!isPipeCreatedByPIMEServer(pipe) || !::SetNamedPipeHandleState(pipe, &mode, NULL, NULL)) {
            DisconnectNamedPipe(pipe);
            CloseHandle(pipe);
            pipe = INVALID_HANDLE_VALUE;
        }
    }
	return pipe;
}


// Ensure that we're connected to the PIME input method server
// If we are already connected, the method simply returns true;
// otherwise, it tries to establish the connection.
bool Client::waitForRpcConnection() {
    if (pipe_ != INVALID_HANDLE_VALUE) {
        return true;
    }

	wstring serverPipeName = getPipeName(L"Launcher");
    for (int attempt = 0; pipe_ == INVALID_HANDLE_VALUE && attempt < 5; ++attempt) {
		// try to connect to the server
		pipe_ = connectPipe(serverPipeName.c_str(), 30000);
	}

    if (pipe_ != INVALID_HANDLE_VALUE) {
        // send initialization info to the server for hand-shake.
        shouldWaitConnection_ = false;  // prevent recursive call of waitForRpcConnection
        if (!init()) {
            closeRpcConnection();
            shouldWaitConnection_ = true;
            return false;
        }

        if (isActivated_) {
            // we lost connection while being activated previously
            // re-initialize the whole text service.
            // activate the text service again.
            onActivate();
        }
        shouldWaitConnection_ = true;
    }
    // if init() or onActivate() RPC fails, the pipe_ might have been closed.
    return pipe_ != INVALID_HANDLE_VALUE;
}

void Client::resetTextServiceState() {
    // we lost connection while being activated previously
    // re-initialize the whole text service.

    // cleanup for the previous instance.
    // remove all buttons

    // some language bar buttons are not unregistered properly
    if (!buttons_.empty()) {
        for (auto& item : buttons_) {
            textService_->removeButton(item.second);
        }
        buttons_.clear();
    }
}

void Client::closeRpcConnection() {
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
