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
#include <nlohmann/json.hpp>

#include "PIMETextService.h"
#include <VersionHelpers.h> // Provided by Windows SDK >= 8.1
#include <Winnls.h> // for IS_HIGH_SURROGATE() macro for checking UTF16 surrogate pairs
#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <ctime>
#include <fstream>
#include <memory>

using namespace std;
using json = nlohmann::json;

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
	guid_{ uuidToString(langProfileGuid) },
	shouldWaitConnection_{ true },
	ioEvent_{ CreateEvent(NULL, TRUE, FALSE, NULL) } {
}

Client::~Client(void) {
	closeRpcConnection();
	resetTextServiceState();
	LangBarButton::clearIconCache();
}

// pack a keyEvent object into a json value
//static
void Client::addKeyEventToRpcRequest(json& request, Ime::KeyEvent& keyEvent) {
	request["charCode"] = keyEvent.charCode();
	request["keyCode"] = keyEvent.keyCode();
	request["repeatCount"] = keyEvent.repeatCount();
	request["scanCode"] = keyEvent.scanCode();
	request["isExtended"] = keyEvent.isExtended();
	json keyStates = json::array();
	const BYTE* states = keyEvent.keyStates();
	for (int i = 0; i < 256; ++i) {
		keyStates.push_back(states[i]);
	}
	request["keyStates"] = keyStates;
}

bool Client::handleRpcResponse(json& msg, Ime::EditSession* session) {
	bool success = msg.value("success", false);
	if (success) {
		updateStatus(msg, session);
	}
	return success;
}

void Client::updateUI(json& data) {
	for (auto it = data.begin(); it != data.end(); ++it) {
		const std::string& name = it.key();
		const json& value = it.value();
		if (value.is_string() && name == "candFontName") {
			wstring fontName = utf8ToUtf16(value.get<string>().c_str());
			textService_->setCandFontName(fontName);
		}
		else if (value.is_number_integer() && name == "candFontSize") {
			textService_->setCandFontSize(value.get<int>());
		}
		else if (value.is_number_integer() && name == "candPerRow") {
			textService_->setCandPerRow(value.get<int>());
		}
		else if (value.is_boolean() && name == "candUseCursor") {
			textService_->setCandUseCursor(value.get<bool>());
		}
	}
}

void Client::updateSelectionKeys(json& msg) {
	// set sel keys before update candidates
	auto& setSelKeysVal = msg["setSelKeys"];
	if (setSelKeysVal.is_string()) {
		// keys used to select candidates
		std::wstring selKeys = utf8ToUtf16(setSelKeysVal.get<string>().c_str());
		textService_->setSelKeys(selKeys);
	}
}

void Client::updateMessageWindow(json& msg, Ime::EditSession* session, bool& endComposition) {
	auto& showMessageVal = msg["showMessage"];
	if (showMessageVal.is_object()) {
		auto& message = showMessageVal["message"];
		auto& duration = showMessageVal["duration"];
		if (message.is_string() && duration.is_number_integer()) {
			if (!textService_->isComposing()) {
				textService_->startComposition(session->context());
				endComposition = true;
			}
			textService_->showMessage(session, utf8ToUtf16(message.get<string>().c_str()), duration.get<int>());
		}
	}

	// hide message
	auto& hideMessageVal = msg["hideMessage"];
	if (hideMessageVal.is_boolean() && hideMessageVal.get<bool>()) {
		textService_->hideMessage();
	}
}

void Client::updateCommitString(json& msg, Ime::EditSession* session) {
	// handle comosition and commit strings
	auto& commitStringVal = msg["commitString"];
	if (commitStringVal.is_string()) {
		std::wstring commitString = utf8ToUtf16(commitStringVal.get<string>().c_str());
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
}

void Client::updateComposition(json& msg, Ime::EditSession* session, bool& endComposition) {
	auto& compositionStringVal = msg["compositionString"];
	bool emptyComposition = false;
	bool hasCompositionString = false;
	std::wstring compositionString;
	if (compositionStringVal.is_string()) {
		// composition buffer
		compositionString = utf8ToUtf16(compositionStringVal.get<string>().c_str());
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

	auto& compositionCursorVal = msg["compositionCursor"];
	if (compositionCursorVal.is_number_integer()) {
		// composition cursor
		if (!emptyComposition) {
			int compositionCursor = compositionCursorVal.get<int>();
			if (!textService_->isComposing()) {
				textService_->startComposition(session->context());
			}
			// NOTE:
			// This fixes PIME bug #166: incorrect handling of UTF-16 surrogate pairs.
			// The TSF API unfortunately treat a UTF-16 surrogate pair as two characters while
			// they actually represent one unicode character only. To workaround this TSF bug,
			// we get the composition string, and try to move the cursor twice when a UTF-16
			// surrogate pair is found.
			if (!hasCompositionString)
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

void Client::updateLanguageButtons(json& msg) {
	// language buttons
	auto& addButtonVal = msg["addButton"];
	if (addButtonVal.is_array()) {
		for (auto& btn : addButtonVal) {
			// FIXME: when to clear the id <=> button map??
			auto langBtn = Ime::ComPtr<PIME::LangBarButton>::takeover(PIME::LangBarButton::fromJson(textService_, btn));
			if (langBtn != nullptr) {
				buttons_.emplace(langBtn->id(), langBtn); // insert into the map
				textService_->addButton(langBtn);
			}
		}
	}

	const auto& removeButtonVal = msg["removeButton"];
	if (removeButtonVal.is_array()) {
		// FIXME: handle windows-mode-icon
		for (const auto& btn : removeButtonVal) {
			if (btn.is_string()) {
				string id = btn.get<string>();
				auto map_it = buttons_.find(id);
				if (map_it != buttons_.end()) {
					textService_->removeButton(map_it->second);
					buttons_.erase(map_it); // remove from the map
				}
			}
		}
	}
	auto& changeButtonVal = msg["changeButton"];
	if (changeButtonVal.is_array()) {
		// FIXME: handle windows-mode-icon
		for (auto& btn : changeButtonVal) {
			if (btn.is_object()) {
				string id = btn["id"].get<string>();
				auto map_it = buttons_.find(id);
				if (map_it != buttons_.end()) {
					map_it->second->updateFromJson(btn);
				}
			}
		}
	}
}

void Client::updatePreservedKeys(json& msg) {
	auto& addPreservedKeyVal = msg["addPreservedKey"];
	if (addPreservedKeyVal.is_array()) {
		// preserved keys
		for (auto& key : addPreservedKeyVal) {
			if (key.is_object()) {
				UINT keyCode = key["keyCode"].get<unsigned int>();
				UINT modifiers = key["modifiers"].get<unsigned int>();
				UUID guid = { 0 };
				if (uuidFromString(key["guid"].get<string>().c_str(), guid)) {
					textService_->addPreservedKey(keyCode, modifiers, guid);
				}
			}
		}
	}

	const auto& removePreservedKeyVal = msg["removePreservedKey"];
	if (removePreservedKeyVal.is_array()) {
		for (auto& item : removePreservedKeyVal) {
			if (item.is_string()) {
				UUID guid = { 0 };
				if (uuidFromString(item.get<string>().c_str(), guid)) {
					textService_->removePreservedKey(guid);
				}
			}
		}
	}
}

void Client::updateKeyboardStatus(json& msg) {
	const auto& openKeyboardVal = msg["openKeyboard"];
	if (openKeyboardVal.is_boolean()) {
		textService_->setKeyboardOpen(openKeyboardVal.get<bool>());
	}
}

void Client::updateStatus(json& msg, Ime::EditSession* session) {
	// We need to handle ordering of some types of the requests.
	// For example, setCompositionCursor() should happen after setCompositionCursor().
	updateSelectionKeys(msg);

	// show message
	bool endComposition = false;
	updateMessageWindow(msg, session, endComposition);

	if (session != nullptr) { // if an edit session is available
		updateCandidateList(msg, session);

		updateCommitString(msg, session);

		updateComposition(msg, session, endComposition);

	}

	updateLanguageButtons(msg);

	// preserved keys
	updatePreservedKeys(msg);

	// keyboard status
	updateKeyboardStatus(msg);

	// other configurations
	auto& customizeUIVal = msg["customizeUI"];
	if (customizeUIVal.is_object()) {
		// customize the UI
		updateUI(customizeUIVal);
	}
}

void Client::updateCandidateList(json& msg, Ime::EditSession* session) {
	// handle candidate list
	const auto& showCandidatesVal = msg["showCandidates"];
	if (showCandidatesVal.is_boolean()) {
		if (showCandidatesVal.get<bool>()) {
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
	if (candidateListVal.is_array()) {
		// handle candidates
		// FIXME: directly access private member is dirty!!!
		vector<wstring>& candidates = textService_->candidates_;
		candidates.clear();
		for (const auto& candidate : candidateListVal) {
			candidates.emplace_back(utf8ToUtf16(candidate.get<string>().c_str()));
		}
		textService_->updateCandidates(session);
		if (!showCandidatesVal.get<bool>()) {
			textService_->hideCandidates();
		}
	}

	const auto& candidateCursorVal = msg["candidateCursor"];
	if (candidateCursorVal.is_number_integer()) {
		if (textService_->candidateWindow_ != nullptr) {
			textService_->candidateWindow_->setCurrentSel(candidateCursorVal.get<int>());
			textService_->refreshCandidates();
		}
	}
}

// handlers for the text service
void Client::onActivate() {
	json req = createRpcRequest("onActivate");
	req["isKeyboardOpen"] = textService_->isKeyboardOpened();

	json ret;
	callRpcMethod(req, ret);
	if (handleRpcResponse(ret)) {
	}
	isActivated_ = true;
}

void Client::onDeactivate() {
	json req = createRpcRequest("onDeactivate");
	json ret;
	callRpcMethod(req, ret);
	if (handleRpcResponse(ret)) {
	}
	LangBarButton::clearIconCache();
	isActivated_ = false;
}

bool Client::filterKeyDown(Ime::KeyEvent& keyEvent) {
	json req = createRpcRequest("filterKeyDown");
	addKeyEventToRpcRequest(req, keyEvent);

	json ret;
	callRpcMethod(req, ret);
	if (handleRpcResponse(ret)) {
		return ret["return"].get<bool>();
	}
	return false;
}

bool Client::onKeyDown(Ime::KeyEvent& keyEvent, Ime::EditSession* session) {
	json req = createRpcRequest("onKeyDown");
	addKeyEventToRpcRequest(req, keyEvent);

	json ret;
	callRpcMethod(req, ret);
	if (handleRpcResponse(ret, session)) {
		return ret["return"].get<bool>();
	}
	return false;
}

bool Client::filterKeyUp(Ime::KeyEvent& keyEvent) {
	json req = createRpcRequest("filterKeyUp");
	addKeyEventToRpcRequest(req, keyEvent);

	json ret;
	callRpcMethod(req, ret);
	if (handleRpcResponse(ret)) {
		return ret["return"].get<bool>();
	}
	return false;
}

bool Client::onKeyUp(Ime::KeyEvent& keyEvent, Ime::EditSession* session) {
	json req = createRpcRequest("onKeyUp");
	addKeyEventToRpcRequest(req, keyEvent);

	json ret;
	callRpcMethod(req, ret);
	if (handleRpcResponse(ret, session)) {
		return ret["return"].get<bool>();
	}
	return false;
}

bool Client::onPreservedKey(const GUID& guid) {
	auto guidStr = uuidToString(guid);
	if (!guidStr.empty()) {
		json req = createRpcRequest("onPreservedKey");
		req["guid"] = std::move(guidStr);

		json ret;
		callRpcMethod(req, ret);
		if (handleRpcResponse(ret)) {
			return ret["return"].get<bool>();
		}
	}
	return false;
}

bool Client::onCommand(UINT id, Ime::TextService::CommandType type) {
	json req = createRpcRequest("onCommand");
	req["id"] = id;
	req["type"] = type;

	json ret;
	callRpcMethod(req, ret);
	if (handleRpcResponse(ret)) {
		return ret["return"].get<bool>();
	}
	return false;
}

bool Client::sendOnMenu(std::string button_id, json& result) {
	json req = createRpcRequest("onMenu");
	req["id"] = button_id;

	callRpcMethod(req, result);
	if (handleRpcResponse(result)) {
		return true;
	}
	return false;
}

static bool menuFromJson(ITfMenu* pMenu, json& menuInfo) {
	if (pMenu != nullptr && menuInfo.is_array()) {
		for (auto& item : menuInfo) {
			UINT id = item.value("id", 0);
			std::wstring text = utf8ToUtf16(item.value("text", "").c_str());

			DWORD flags = 0;
			json submenuInfo;
			ITfMenu* submenu = nullptr;
			if (id == 0 && text.empty())
				flags = TF_LBMENUF_SEPARATOR;
			else {
				if (item.value("checked", false))
					flags |= TF_LBMENUF_CHECKED;
				if (!item.value("enabled", true))
					flags |= TF_LBMENUF_GRAYED;

				if (item.contains("submenu") && item["submenu"].is_array()) {
					submenuInfo = item["submenu"];
					flags |= TF_LBMENUF_SUBMENU;
				}
			}
			pMenu->AddMenuItem(id, flags, NULL, NULL, text.c_str(), text.length(), flags & TF_LBMENUF_SUBMENU ? &submenu : nullptr);
			if (submenu != nullptr && !submenuInfo.is_null()) {
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
	json result;
	if (sendOnMenu(btn->id(), result)) {
		json& menuInfo = result["return"];
		return menuFromJson(pMenu, menuInfo);
	}
	return false;
}

static HMENU menuFromJson(json& menuInfo) {
	if (menuInfo.is_array()) {
		HMENU menu = ::CreatePopupMenu();
		for (auto& item : menuInfo) {
			UINT id = item.value("id", 0);
			std::wstring text = utf8ToUtf16(item.value("text", "").c_str());

			UINT flags = MF_STRING;
			if (id == 0 && text.empty())
				flags = MF_SEPARATOR;
			else {
				if (item.value("checked", false))
					flags |= MF_CHECKED;
				if (!item.value("enabled", true))
					flags |= MF_GRAYED;

				if (item.contains("submenu") && item["submenu"].is_array()) {
					json& subMenuValue = item["submenu"];
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
	json result;
	if (sendOnMenu(btn->id(), result)) {
		json& menuInfo = result["return"];
		return menuFromJson(menuInfo);
	}
	return NULL;
}

// called when a compartment value is changed
void Client::onCompartmentChanged(const GUID& key) {
	auto guidStr = uuidToString(key);
	if (!guidStr.empty()) {
		json req = createRpcRequest("onCompartmentChanged");
		req["guid"] = std::move(guidStr);

		json ret;
		callRpcMethod(req, ret);
		if (handleRpcResponse(ret)) {
		}
	}
}

// called when the keyboard is opened or closed
void Client::onKeyboardStatusChanged(bool opened) {
	json req = createRpcRequest("onKeyboardStatusChanged");
	req["opened"] = opened;

	json ret;
	callRpcMethod(req, ret);
	if (handleRpcResponse(ret)) {
	}
}

// called just before current composition is terminated for doing cleanup.
void Client::onCompositionTerminated(bool forced) {
	json req = createRpcRequest("onCompositionTerminated");
	req["forced"] = forced;

	json ret;
	callRpcMethod(req, ret);
	if (handleRpcResponse(ret)) {
	}
}

bool Client::init() {
	json req = createRpcRequest("init");
	req["id"] = guid_.c_str();  // language profile guid
	req["isWindows8Above"] = ::IsWindows8OrGreater();
	req["isMetroApp"] = textService_->isMetroApp();
	req["isUiLess"] = textService_->isUiLess();
	req["isConsole"] = textService_->isConsole();

	json ret;
	return callRpcMethod(req, ret) && handleRpcResponse(ret);
}


json Client::createRpcRequest(const char* methodName) {
	json request;
	request["method"] = methodName;

	// TODO: add other environment info?
	return request;
}

bool Client::callPipeIO(bool isRead, void *buffer, DWORD size, DWORD *rlen, int timeoutMs) {
	if (!ioEvent_) {
		return false;
	}

	OVERLAPPED overlapped = { 0 };
	overlapped.hEvent = ioEvent_;
	ResetEvent(ioEvent_);

	BOOL ok;
	if (isRead)
		ok = ReadFile(pipe_, buffer, size, rlen, &overlapped);
	else
		ok = WriteFile(pipe_, buffer, size, rlen, &overlapped);

	if (!ok && GetLastError() != ERROR_IO_PENDING) {
		return false;
	}

	DWORD wait = WaitForSingleObject(ioEvent_, timeoutMs);
	if (wait == WAIT_OBJECT_0) {
		ok = GetOverlappedResult(pipe_, &overlapped, rlen, FALSE);
	}
	else {
		// timeout or error
		CancelIo(pipe_);
		ok = FALSE;
	}

	return ok;
}

bool Client::callRpcPipe(HANDLE pipe, const std::string& serializedRequest, std::string& serializedReply) {
	std::string request = serializedRequest;
	if (request.empty() || request.back() != '\n') {
		request += '\n';
	}

	const int timeoutMs = 2000;
	DWORD wlen = 0;
	if (!callPipeIO(false, (void*)request.data(), (DWORD)request.size(), &wlen, timeoutMs)) {
		return false;
	}

	char buf[1024];
	DWORD rlen = 0;
	while (true) {
		// Check if we already have a full line in the buffer
		size_t pos = readBuffer_.find('\n');
		if (pos != std::string::npos) {
			serializedReply = readBuffer_.substr(0, pos); // exclude the newline for easier parsing
			readBuffer_.erase(0, pos + 1);
			return true;
		}

		if (!callPipeIO(true, buf, sizeof(buf), &rlen, timeoutMs) || rlen == 0) {
			return false;
		}
		readBuffer_.append(buf, rlen);
	}
}

// send the request to the server
// a sequence number will be added to the req object automatically.
bool Client::callRpcMethod(json& request, json & response) {
	if (shouldWaitConnection_ && !waitForRpcConnection()) {
		return false;
	}

	// Add a sequence number for the request.
	auto seqNum = nextSeqNum_++;
	request["seqNum"] = seqNum;

	std::string serializedRequest = request.dump(); // convert the json object to string

	std::string serializedResponse;
	bool success = false;
	if (callRpcPipe(pipe_, serializedRequest, serializedResponse)) {
		try {
			response = json::parse(serializedResponse);
			success = true;
			if (response["seqNum"].get<unsigned int>() != seqNum) // sequence number mismatch
				success = false;
		}
		catch (...) {
			success = false;
		}
	}
	else {
		success = false;
	}

	if (!success) { // fail to send the request to the server
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
		pipe = CreateFile(pipeName, GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, FILE_FLAG_OVERLAPPED, NULL);
	}

	if (pipe != INVALID_HANDLE_VALUE) {
		// The pipe is connected; check if it's created by our server.
		if (!isPipeCreatedByPIMEServer(pipe)) {
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
		CloseHandle(pipe_);
		pipe_ = INVALID_HANDLE_VALUE;
	}
	if (ioEvent_ != INVALID_HANDLE_VALUE) {
		CloseHandle(ioEvent_);
		ioEvent_ = INVALID_HANDLE_VALUE;
	}
	readBuffer_.clear();
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
