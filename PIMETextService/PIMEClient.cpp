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
#include "CompositionCursor.h"
#include "JsonUtils.h"
#include "libIME2/src/Utils.h"
#include <algorithm>
#include <nlohmann/json.hpp>

#include "PIMETextService.h"
#include <VersionHelpers.h> // Provided by Windows SDK >= 8.1
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
	nextSeqNum_(0),
	isActivated_(false),
	state_(State::Disconnected),
	guid_{ uuidToString(langProfileGuid) } {
}

Client::~Client(void) {
	state_ = State::Disconnected;
	if (connector_) {
		connector_->cancel();
		connector_.reset();
	}
	pipe_.close();
	resetTextServiceState();
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
	// A failed RPC call leaves msg as null, and jsonValueOr is noexcept.
	if (!msg.is_object()) {
		return false;
	}
	bool success = jsonValueOr<bool>(msg, "success", false);
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
			const int fixedCursorPos = compositionCursorToUtf16Position(compositionString, compositionCursor);
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
				string id = jsonValueOr<string>(btn, "id", "");
				if (!id.empty()) {
					auto map_it = buttons_.find(id);
					if (map_it != buttons_.end()) {
						map_it->second->updateFromJson(btn);
					}
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
				UINT keyCode = jsonValueOr<UINT>(key, "keyCode", 0u);
				UINT modifiers = jsonValueOr<UINT>(key, "modifiers", 0u);
				std::string guidStr = jsonValueOr<std::string>(key, "guid", "");
				UUID guid = { 0 };
				if (!guidStr.empty() && uuidFromString(guidStr.c_str(), guid)) {
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
			if (candidate.is_string()) {
				candidates.emplace_back(utf8ToUtf16(candidate.get<string>().c_str()));
			}
		}
		textService_->updateCandidates(session);
		if (showCandidatesVal.is_boolean() && !showCandidatesVal.get<bool>()) {
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

bool Client::ensureConnected() {
	if (state_ == State::Ready) {
		return true;
	}
	if (state_ == State::Disconnected && isActivated_) {
		const uint64_t now = ::GetTickCount64();
		int shift = connectFailures_ - 1;
		if (shift < 0) shift = 0;
		if (shift > 5) shift = 5;
		const uint64_t delayMs = (connectFailures_ == 0) ? 0 : (500ULL << shift);
		if (now - lastConnectAttempt_ >= delayMs) {
			startAsyncConnect();
		}
	}
	return false;
}

// handlers for the text service
void Client::onActivate() {
	isActivated_ = true;
	if (state_ == State::Ready) {
		json req = createRpcRequest("onActivate");
		req["isKeyboardOpen"] = textService_->isKeyboardOpened();

		json ret;
		callRpcMethod(req, ret, kServerStartupTimeoutMs);
		if (handleRpcResponse(ret)) {
		}
		return;
	}

	startAsyncConnect();
}

void Client::onDeactivate() {
	isActivated_ = false;
	state_ = State::Disconnected;
	if (connector_) {
		connector_->cancel();
		connector_.reset();
	}

	if (pipe_.isValid()) {
		json req = createRpcRequest("onDeactivate");
		json ret;
		callRpcMethod(req, ret);
		if (handleRpcResponse(ret)) {
		}
		pipe_.close();
	}
}

bool Client::filterKeyDown(Ime::KeyEvent& keyEvent) {
	if (!ensureConnected()) {
		return false;
	}

	json req = createRpcRequest("filterKeyDown");
	addKeyEventToRpcRequest(req, keyEvent);

	json ret;
	callRpcMethod(req, ret);
	if (handleRpcResponse(ret)) {
		return jsonValueOr<bool>(ret, "return", false);
	}
	return false;
}

bool Client::onKeyDown(Ime::KeyEvent& keyEvent, Ime::EditSession* session) {
	if (!ensureConnected()) {
		return false;
	}

	json req = createRpcRequest("onKeyDown");
	addKeyEventToRpcRequest(req, keyEvent);

	json ret;
	callRpcMethod(req, ret);
	if (handleRpcResponse(ret, session)) {
		return jsonValueOr<bool>(ret, "return", false);
	}
	return false;
}

bool Client::filterKeyUp(Ime::KeyEvent& keyEvent) {
	if (!ensureConnected()) {
		return false;
	}

	json req = createRpcRequest("filterKeyUp");
	addKeyEventToRpcRequest(req, keyEvent);

	json ret;
	callRpcMethod(req, ret);
	if (handleRpcResponse(ret)) {
		return jsonValueOr<bool>(ret, "return", false);
	}
	return false;
}

bool Client::onKeyUp(Ime::KeyEvent& keyEvent, Ime::EditSession* session) {
	if (!ensureConnected()) {
		return false;
	}

	json req = createRpcRequest("onKeyUp");
	addKeyEventToRpcRequest(req, keyEvent);

	json ret;
	callRpcMethod(req, ret);
	if (handleRpcResponse(ret, session)) {
		return jsonValueOr<bool>(ret, "return", false);
	}
	return false;
}

bool Client::onPreservedKey(const GUID& guid) {
	if (!ensureConnected()) {
		return false;
	}

	auto guidStr = uuidToString(guid);
	if (!guidStr.empty()) {
		json req = createRpcRequest("onPreservedKey");
		req["guid"] = std::move(guidStr);

		json ret;
		callRpcMethod(req, ret);
		if (handleRpcResponse(ret)) {
			return jsonValueOr<bool>(ret, "return", false);
		}
	}
	return false;
}

bool Client::onCommand(UINT id, Ime::TextService::CommandType type) {
	if (!ensureConnected()) {
		return false;
	}

	json req = createRpcRequest("onCommand");
	req["id"] = id;
	req["type"] = type;

	json ret;
	callRpcMethod(req, ret);
	if (handleRpcResponse(ret)) {
		return jsonValueOr<bool>(ret, "return", false);
	}
	return false;
}

bool Client::sendOnMenu(std::string button_id, json& result) {
	if (!ensureConnected()) {
		return false;
	}

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
			if (!item.is_object())
				continue;
			UINT id = jsonValueOr<UINT>(item, "id", 0u);
			std::wstring text = utf8ToUtf16(jsonValueOr<std::string>(item, "text", "").c_str());

			DWORD flags = 0;
			json submenuInfo;
			ITfMenu* submenu = nullptr;
			if (id == 0 && text.empty())
				flags = TF_LBMENUF_SEPARATOR;
			else {
				if (jsonValueOr<bool>(item, "checked", false))
					flags |= TF_LBMENUF_CHECKED;
				if (!jsonValueOr<bool>(item, "enabled", true))
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
			if (!item.is_object())
				continue;
			UINT id = jsonValueOr<UINT>(item, "id", 0u);
			std::wstring text = utf8ToUtf16(jsonValueOr<std::string>(item, "text", "").c_str());

			UINT flags = MF_STRING;
			if (id == 0 && text.empty())
				flags = MF_SEPARATOR;
			else {
				if (jsonValueOr<bool>(item, "checked", false))
					flags |= MF_CHECKED;
				if (!jsonValueOr<bool>(item, "enabled", true))
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
	if (!ensureConnected()) {
		return NULL;
	}

	json result;
	if (sendOnMenu(btn->id(), result)) {
		json& menuInfo = result["return"];
		return menuFromJson(menuInfo);
	}
	return NULL;
}

// called when a compartment value is changed
void Client::onCompartmentChanged(const GUID& key) {
	if (!ensureConnected()) {
		return;
	}

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
	if (!ensureConnected()) {
		return;
	}

	json req = createRpcRequest("onKeyboardStatusChanged");
	req["opened"] = opened;

	json ret;
	callRpcMethod(req, ret);
	if (handleRpcResponse(ret)) {
	}
}

// called just before current composition is terminated for doing cleanup.
void Client::onCompositionTerminated(bool forced) {
	if (!ensureConnected()) {
		return;
	}

	json req = createRpcRequest("onCompositionTerminated");
	req["forced"] = forced;

	json ret;
	callRpcMethod(req, ret);
	if (handleRpcResponse(ret)) {
	}
}

void Client::startAsyncConnect() {
	if (connector_) {
		connector_->cancel();
		connector_.reset();
	}

	lastConnectAttempt_ = ::GetTickCount64();
	state_ = State::Connecting;

	json initReq = createRpcRequest("init");
	initReq["id"] = guid_.c_str();  // language profile guid
	initReq["isWindows8Above"] = ::IsWindows8OrGreater();
	initReq["isMetroApp"] = textService_->isMetroApp();
	initReq["isUiLess"] = textService_->isUiLess();
	initReq["isConsole"] = textService_->isConsole();

	connector_ = std::make_shared<AsyncConnector>();
	connector_->connect(getPipeName(L"Launcher"), std::move(initReq), [this](RpcPipe pipe, json initResp) {
		connector_.reset();
		if (pipe.isValid()) {
			pipe_ = std::move(pipe);
			nextSeqNum_ = 2; // seqNum 1 was used by init
			handleRpcResponse(initResp);

			// Mark Ready before sending onActivate RPC so callRpcMethod allows it:
			state_ = State::Ready;

			// With backend warmed up and pipe connected, sync onActivate takes < 1ms:
			json req = createRpcRequest("onActivate");
			req["isKeyboardOpen"] = textService_->isKeyboardOpened();
			json actResp;
			if (callRpcMethod(req, actResp)) {
				connectFailures_ = 0;
				handleRpcResponse(actResp);
			}
			else {
				connectFailures_ = (connectFailures_ < 6) ? connectFailures_ + 1 : 6;
			}
		}
		else {
			state_ = State::Disconnected;
			connectFailures_ = (connectFailures_ < 6) ? connectFailures_ + 1 : 6;
		}
	});
}


json Client::createRpcRequest(const char* methodName) {
	json request;
	request["method"] = methodName;

	// TODO: add other environment info?
	return request;
}

// send the request to the server
// a sequence number will be added to the req object automatically.
bool Client::callRpcMethod(json& request, json & response, int timeoutMs) {
	if (!ensureConnected()) {
		return false;
	}

	// Add a sequence number for the request.
	auto seqNum = nextSeqNum_++;
	request["seqNum"] = seqNum;

	std::string serializedRequest = request.dump(); // convert the json object to string
	std::string methodName = jsonValueOr<std::string>(request, "method", "");

	std::string serializedResponse;
	bool success = false;
	if (pipe_.callRpc(serializedRequest, serializedResponse, timeoutMs)) {
		response = parseJsonNoThrow(serializedResponse);
		if (!response.is_discarded() && response.is_object() &&
		    jsonValueOr<unsigned int>(response, "seqNum", 0) == seqNum) {
			success = true;
		}
	}

	if (!success) { // fail to send the request to the server
		response = nullptr; // never let callers act on a stale or partial response
		pipe_.close(); // close the pipe connection since it's broken
		state_ = State::Disconnected;
		connectFailures_ = (connectFailures_ < 6) ? connectFailures_ + 1 : 6;
		resetTextServiceState();  // since we lost the connection, the state is unknown so we reset.
		// Note: We do NOT immediately call startAsyncConnect() here synchronously.
		// Instead, ensureConnected() handles reconnect attempts with exponential backoff
		// to prevent UI freezing loops when the backend is unresponsive.
	}
	return success;
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

wstring Client::getPipeName(const wchar_t* baseName) {
	wstring pipeName = L"\\\\.\\pipe\\";
	DWORD len = 0;
	::GetUserNameW(NULL, &len);
	if (len <= 0) {
		return L"";
	}

	unique_ptr<wchar_t[]> username(new wchar_t[len]);
	if (!::GetUserNameW(username.get(), &len)) {
		return L"";
	}

	pipeName += username.get();
	pipeName += L"\\PIME\\";
	pipeName += baseName;
	return pipeName;
}

} // namespace PIME
