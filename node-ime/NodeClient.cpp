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

#include "NodeClient.h"
#include "libIME/Utils.h"
#include <algorithm>
#include "rapidjson/writer.h"
#include "rapidjson/stringbuffer.h"
#include "NodeTextService.h"
#include <cstdlib>
#include <ctime>

using namespace std;
using namespace rapidjson;

namespace Node {

static wchar_t g_pipeName[] = L"\\\\.\\pipe\\mynamedpipe";
static const UINT WM_DISPATCH_QUEUED_MESSAGES = WM_APP + 1;

Client::Client(TextService* service):
	textService_(service),
	eventWindow_(NULL),
	pipe_(INVALID_HANDLE_VALUE),
	pipeThread_(INVALID_HANDLE_VALUE),
	pipeLock_(CreateMutex(NULL, FALSE, NULL)),
	pendingMessage_(false) {

	static bool init_srand = false;
	if (!init_srand) {
		srand(time(NULL));
	}

	createEventWindow();
}

Client::~Client(void) {
	closePipe();
	if (pipeLock_ != INVALID_HANDLE_VALUE) {
		CloseHandle(pipeLock_);
	}
	if (eventWindow_)
		DestroyWindow(eventWindow_);
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
			
		}
		return success;
	}
	return false;
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
	if (Document* ret = sendRequest(s.GetString(), sn)) {
		if (handleReply(*ret)) {
		}
		delete ret;
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
	if (Document* ret = sendRequest(s.GetString(), sn)) {
		if (handleReply(*ret)) {
		}
		delete ret;
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
	if (Document* ret = sendRequest(s.GetString(), sn)) {
		auto& reply = *ret;
		if (handleReply(reply)) {
			return reply["return"].GetBool();
		}
		delete ret;
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
	if (Document* ret = sendRequest(s.GetString(), sn)) {
		auto& reply = *ret;
		if (handleReply(reply)) {
			return reply["return"].GetBool();
		}
		delete ret;
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
	if (Document* ret = sendRequest(s.GetString(), sn)) {
		auto& reply = *ret;
		if (handleReply(reply)) {
			return reply["return"].GetBool();
		}
		delete ret;
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
	if (Document* ret = sendRequest(s.GetString(), sn)) {
		auto& reply = *ret;
		if (handleReply(reply)) {
			return reply["return"].GetBool();
		}
		delete ret;
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
		if (Document* ret = sendRequest(s.GetString(), sn)) {
			auto& reply = *ret;
			if (handleReply(reply)) {
				return reply["return"].GetBool();
			}
			delete ret;
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

	writer.EndObject();
	if (Document* ret = sendRequest(s.GetString(), sn)) {
		auto& reply = *ret;
		if (handleReply(reply)) {
			return reply["return"].GetBool();
		}
		delete ret;
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
		if (Document* ret = sendRequest(s.GetString(), sn)) {
			if (handleReply(*ret)) {
			}
			delete ret;
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
	if (Document* ret = sendRequest(s.GetString(), sn)) {
		if (handleReply(*ret)) {
		}
		delete ret;
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
	if (Document* ret = sendRequest(s.GetString(), sn)) {
		if (handleReply(*ret)) {
		}
		delete ret;
	}
}

void Client::onLangProfileActivated(REFIID lang) {
	/*
	LPOLESTR str = NULL;
	if (SUCCEEDED(::StringFromCLSID(lang, &str))) {
		StringBuffer s;
		Writer<StringBuffer> writer(s);
		writer.StartObject();

		writer.String("method");
		writer.String("onLangProfileActivated");

		writer.String("lang");
		writer.String(utf16ToUtf8(str));
		::CoTaskMemFree(str);

		writer.EndObject();
		string ret = sendRequest(s.GetString());
	}
	*/
}

void Client::onLangProfileDeactivated(REFIID lang) {
	/*
	LPOLESTR str = NULL;
	if (SUCCEEDED(::StringFromCLSID(lang, &str))) {
		StringBuffer s;
		Writer<StringBuffer> writer(s);
		writer.StartObject();

		writer.String("method");
		writer.String("onLangProfileDeactivated");

		writer.String("lang");
		writer.String(utf16ToUtf8(str));
		::CoTaskMemFree(str);

		writer.EndObject();
		string ret = sendRequest(s.GetString());
	}
	*/
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
	if (Document* ret = sendRequest(s.GetString(), sn)) {
		if (handleReply(*ret)) {
		}
		delete ret;
	}
}

Document* Client::sendRequest(std::string req, int seqNo) {
	std::string ret;
	if (connectPipe()) { // ensure that we're connected
#if 0
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
#endif
		DWORD wlen = 0;
		if (WriteFile(pipe_, req.c_str(), req.length(), &wlen, NULL)) {
			Document* reply = waitForReturn(seqNo);
			return reply;
		}
	}
	//Document d;
	//d.Parse(ret.c_str());
	//return d;
	return nullptr;
}

// running in worker thread
DWORD Client::pipeThreadFunc() {
	char buf[1024];
	DWORD rlen = 0;
	string msg;
	for (;;) {
		BOOL ret = ReadFile(pipe_, buf, sizeof(buf) - 1, &rlen, NULL);
		if (ret) {
			buf[rlen] = '\0';
			msg += buf;
		}
		else {
			switch (GetLastError()) {
			default:
				break;
			}
		}
		WaitForSingleObject(pipeLock_, INFINITE); // lock the mutex
		msgQueue_.push_back(msg); // push the msg to queue
		if (!pendingMessage_) {
			PostMessage(eventWindow_, WM_DISPATCH_QUEUED_MESSAGES, 0, 0); // schedule a event dispatch
			pendingMessage_ = true;
		}
		ReleaseMutex(pipeLock_); // release the mutex
		msg.clear();
	}
	// FIXME: cleanup
}

LRESULT Client::wndProc(UINT msg, WPARAM wp, LPARAM lp) {
	switch (msg) {
	case WM_DISPATCH_QUEUED_MESSAGES: {
		WaitForSingleObject(pipeLock_, INFINITE); // lock the mutex
		while (!msgQueue_.empty()) {
			// pop a message from the queue
			string msg = msgQueue_.front();
			msgQueue_.pop_front();
			// TODO: dispatch the message
			handleMessage(msg);
		}
		pendingMessage_ = false;
		ReleaseMutex(pipeLock_); // release the mutex
		return 0;
	}
	default:
		break;
	}
	return DefWindowProc(eventWindow_, msg, wp, lp);
}

rapidjson::Document* Client::waitForReturn(int seqNo) {
	MSG msg;
	while (GetMessage(&msg, eventWindow_, 0, 0)) {
		TranslateMessage(&msg);
		DispatchMessage(&msg);
		// check for return value
		auto it = std::find_if(pendingReturn_.begin(), pendingReturn_.end(), [=](Document* doc) {
			auto v = doc->FindMember("seqNum");
			if (v != doc->MemberEnd() && v->value.GetInt() == seqNo)
				return true;
			return false;
		});
		if (it != pendingReturn_.end()) {
			Document* doc = *it;
			pendingReturn_.erase(it);
			return doc;
		}
	}
	return nullptr;
}

void Client::handleMessage(const std::string& msg) {
	// TODO: handle the message received from the server
	Document* doc = new Document();
	doc->Parse(msg.c_str());
	if (doc->FindMember("seqNum") != doc->MemberEnd()) {
		pendingReturn_.push_back(doc);
	}
	else {
		// dispatch method call
		auto it = doc->FindMember("method");
		if (it != doc->MemberEnd()) {

		}
		delete doc;
	}
}

void Client::createEventWindow() {
	static wchar_t wndClass[] = L"PIME_EventWindow";
	HINSTANCE hinst = HINSTANCE(::GetModuleHandle(NULL));
	WNDCLASS klass;
	memset(&klass, 0, sizeof(klass));
	klass.hInstance = hinst;
	klass.lpfnWndProc = _wndProc;
	klass.lpszClassName = wndClass;
	RegisterClass(&klass);
	eventWindow_ = CreateWindow(wndClass, NULL, 0, 0, 0, 0, 0, HWND_DESKTOP, NULL, hinst, NULL);
	SetWindowLongPtr(eventWindow_, GWLP_USERDATA, LONG_PTR(this));
}

bool Client::connectPipe() {
	if (pipe_ == INVALID_HANDLE_VALUE) { // the pipe is not connected
		for (;;) {
			pipe_ = CreateFile(g_pipeName, GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, 0, NULL);
			if (pipe_ != INVALID_HANDLE_VALUE)
				break;
			if (GetLastError() != ERROR_PIPE_BUSY)
				return false;
			// All pipe instances are busy, so wait for 10 seconds.
			if (!WaitNamedPipe(g_pipeName, 10000))
				return false;
		}
		// The pipe is connected; change to message-read mode.
		DWORD mode = PIPE_READMODE_MESSAGE;
		BOOL success = SetNamedPipeHandleState(pipe_, &mode, NULL, NULL);
		if (!success) {
			closePipe();
			return false;
		}
		// create a thread to read the pipe
		pipeThread_ = CreateThread(NULL, 0, _pipeThreadFunc, this, 0, NULL);
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


} // namespace Node
