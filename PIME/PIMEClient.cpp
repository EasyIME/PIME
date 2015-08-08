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

// this is the GUID of the IME mode icon in Windows 8
// the value is not available in older SDK versions, so let's define it ourselves.
static const GUID _GUID_LBI_INPUTMODE =
{ 0x2C77A81E, 0x41CC, 0x4178, { 0xA3, 0xA7, 0x5F, 0x8A, 0x98, 0x75, 0x68, 0xE6 } };

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

bool Client::handleReply(rapidjson::Document& msg, Ime::EditSession* session) {
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

void Client::updateLangBarButton(Ime::LangBarButton* btn, rapidjson::Value& info) {
	auto it = info.FindMember("icon");
	if (it != info.MemberEnd() && it->value.IsString()) {
		wstring iconPath = utf8ToUtf16(it->value.GetString());
		HICON icon = (HICON)LoadImageW(NULL, iconPath.c_str(), IMAGE_ICON, 0, 0, LR_DEFAULTCOLOR | LR_LOADFROMFILE);
		btn->setIcon(icon);
	}

	it = info.FindMember("commandId");
	if (it != info.MemberEnd() && it->value.IsUint()) {
		UINT cmd = it->value.GetUint();
		btn->setCommandId(cmd);
	}

	it = info.FindMember("text");
	if (it != info.MemberEnd() && it->value.IsString()) {
		std::wstring text = utf8ToUtf16(it->value.GetString());
		btn->setText(text.c_str());
	}

	it = info.FindMember("tooltip");
	if (it != info.MemberEnd() && it->value.IsString()) {
		std::wstring tooltip = utf8ToUtf16(it->value.GetString());
		btn->setTooltip(tooltip.c_str());
	}
}

void Client::updateStatus(rapidjson::Document& msg, Ime::EditSession* session) {
	rapidjson::Document::MemberIterator it;
	if (session != nullptr) { // if an edit session is available
		// commit string
		it = msg.FindMember("commitString");
		if (it != msg.MemberEnd() && it->value.IsString()) {
			std::wstring commitString = utf8ToUtf16(it->value.GetString());
			if (!commitString.empty()) {
				if (!textService_->isComposing()) {
					textService_->startComposition(session->context());
				}
				textService_->setCompositionString(session, commitString.c_str(), commitString.length());
				textService_->endComposition(session->context());
			}
		}

		// composition buffer
		it = msg.FindMember("compositionString");
		if (it != msg.MemberEnd() && it->value.IsString()) {
			std::wstring compositionString = utf8ToUtf16(it->value.GetString());
			if (!compositionString.empty()) {
				if (!textService_->isComposing()) {
					textService_->startComposition(session->context());
				}
				textService_->setCompositionString(session, compositionString.c_str(), compositionString.length());
			}
		}

		// composition cursor
		it = msg.FindMember("compositionCursor");
		if (it != msg.MemberEnd() && it->value.IsInt()) {
			int compositionCursor = it->value.GetInt();
			if (!textService_->isComposing()) {
				textService_->startComposition(session->context());
			}
			textService_->setCompositionCursor(session, compositionCursor);
		}

		// handle candidates
		it = msg.FindMember("candidateList");
		if (it != msg.MemberEnd() && it->value.IsArray()) {
			rapidjson::Value& candidateList = it->value;
			// FIXME: directly access private member is dirty!!!
			vector<wstring>& candidates = textService_->candidates_;
			candidates.clear();
			for (auto it = candidateList.Begin(); it < candidateList.End(); ++it) {
				wstring cand = utf8ToUtf16(it->GetString());
				candidates.push_back(cand);
			}
		}

		it = msg.FindMember("showCandidates");
		if (it != msg.MemberEnd() && it->value.IsBool()) {
			bool showCandidates = it->value.GetBool();
			if (showCandidates) {
				textService_->showCandidates(session);
			}
			else {
				textService_->hideCandidates();
			}
		}
	}

	// language buttons
	it = msg.FindMember("addButton");
	if (it != msg.MemberEnd() && it->value.IsArray()) {
		rapidjson::Value& buttons = it->value;
		for (auto btn_it = buttons.Begin(); btn_it < buttons.End(); ++btn_it) {
			rapidjson::Value& btn = *btn_it;
			if (btn.IsObject()) {
				string id = btn["id"].GetString();

				DWORD style = TF_LBI_STYLE_BTN_BUTTON;
				auto prop_it = btn.FindMember("style");
				if (prop_it != btn.MemberEnd())
					style = prop_it->value.GetUint();

				CLSID guid = { 0 }; // create a new GUID on-the-fly
				if (id == "windows-mode-icon") {
					// Windows 8 systray IME mode icon
					guid = _GUID_LBI_INPUTMODE;
				}
				else {
					CoCreateGuid(&guid);
				}

				Ime::LangBarButton* langBtn = new Ime::LangBarButton(textService_, guid, 0, NULL, style);
				buttons_[id] = langBtn; // insert into the map
				updateLangBarButton(langBtn, btn);
				textService_->addButton(langBtn);
				langBtn->Release();
			}
		}
	}

	it = msg.FindMember("removeButton");
	if (it != msg.MemberEnd() && it->value.IsArray()) {
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

	it = msg.FindMember("changeButton");
	if (it != msg.MemberEnd() && it->value.IsArray()) {
		rapidjson::Value& buttons = it->value;
		for (auto btn_it = buttons.Begin(); btn_it < buttons.End(); ++btn_it) {
			rapidjson::Value& btn = *btn_it;
			if (btn.IsObject()) {
				string id = btn["id"].GetString();
				auto map_it = buttons_.find(id);
				if (map_it != buttons_.end()) {
					updateLangBarButton(map_it->second, btn);
				}
			}
		}
	}

	// preserved keys
	it = msg.FindMember("addPreservedKey");
	if (it != msg.MemberEnd() && it->value.IsArray()) {
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

	it = msg.FindMember("removePreservedKey");
	if (it != msg.MemberEnd() && it->value.IsArray()) {
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
	Document ret = sendRequest(s.GetString(), sn);
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
	Document ret = sendRequest(s.GetString(), sn);
	if (handleReply(ret)) {
	}
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
	Document ret = sendRequest(s.GetString(), sn);
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
	Document ret = sendRequest(s.GetString(), sn);
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
	Document ret = sendRequest(s.GetString(), sn);
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
	Document ret = sendRequest(s.GetString(), sn);
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
		Document ret = sendRequest(s.GetString(), sn);
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
	Document ret = sendRequest(s.GetString(), sn);
	if (handleReply(ret)) {
		return ret["return"].GetBool();
	}
	return false;
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

		writer.String("key");
		writer.String(utf16ToUtf8(str));
		::CoTaskMemFree(str);

		writer.EndObject();
		Document ret = sendRequest(s.GetString(), sn);
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
	Document ret = sendRequest(s.GetString(), sn);
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
	Document ret = sendRequest(s.GetString(), sn);
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
		Document ret = sendRequest(s.GetString(), sn);
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
		Document ret = sendRequest(s.GetString(), sn);
		if (handleReply(ret)) {
		}
	}
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
	Document ret = sendRequest(s.GetString(), sn);
	if (handleReply(ret)) {
	}
}

Document Client::sendRequest(std::string req, int seqNo) {
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
			}
			buf[rlen] = '\0';
			ret = buf;
			for (;;) {
				BOOL success = ReadFile(pipe_, buf, 1023, &rlen, NULL);
				if (!success && (GetLastError() != ERROR_MORE_DATA))
					break;
				buf[rlen] = '\0';
				ret += buf;
			}
		}
	}
	Document d;
	d.Parse(ret.c_str());
	return d;
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
	}
}


} // namespace PIME
