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

#ifndef _PIME_CLIENT_H_
#define _PIME_CLIENT_H_
#define NDEBUG
#include "PIMELangBarButton.h"
#include <libIME2/src/EditSession.h>
#include <libIME2/src/KeyEvent.h>
#include <libIME2/src/TextService.h>

#include <nlohmann/json.hpp>
#include <string>
#include <unordered_map>

namespace PIME {

class TextService;

class Client
{
public:
	// create a client connection to the input method server
	// guid is the GUID of the language profile
	Client(TextService* service, REFIID langProfileGuid);
	~Client(void);

	const std::string guid() const {
		return guid_;
	}

	// handlers for the text service
	void onActivate();
	void onDeactivate();

	bool filterKeyDown(Ime::KeyEvent& keyEvent);
	bool onKeyDown(Ime::KeyEvent& keyEvent, Ime::EditSession* session);

	bool filterKeyUp(Ime::KeyEvent& keyEvent);
	bool onKeyUp(Ime::KeyEvent& keyEvent, Ime::EditSession* session);

	bool onPreservedKey(const GUID& guid);

	bool onCommand(UINT id, Ime::TextService::CommandType type);

	// called when a language bar button needs a menu
	bool onMenu(LangBarButton* btn, ITfMenu* pMenu);

	// called when a language bar button needs a menu
	HMENU onMenu(LangBarButton* btn);

	// called when a compartment value is changed
	void onCompartmentChanged(const GUID& key);

	// called when the keyboard is opened or closed
	void onKeyboardStatusChanged(bool opened);

	// called just before current composition is terminated for doing cleanup.
	void onCompositionTerminated(bool forced);

private:
	static std::wstring getPipeName(const wchar_t* base_name);
	HANDLE connectPipe(const wchar_t* pipeName, int timeoutMs);

	nlohmann::json createRpcRequest(const char* methodName);
	bool callRpcMethod(nlohmann::json& request, nlohmann::json& response);

	bool isPipeCreatedByPIMEServer(HANDLE pipe);
	bool waitForRpcConnection();
	bool callRpcPipe(HANDLE pipe, const std::string& serializedRequest, std::string& serializedReply);
	bool callPipeIO(bool isRead, void *buffer, DWORD size, DWORD *rlen, int timeoutMs);
	void closeRpcConnection();

	bool init();
	void resetTextServiceState();

	void addKeyEventToRpcRequest(nlohmann::json& request, Ime::KeyEvent& keyEvent);
	bool sendOnMenu(std::string button_id, nlohmann::json& result);

	bool handleRpcResponse(nlohmann::json& msg, Ime::EditSession* session = nullptr);

	// Update text service and UI status based on RPC responses.
	void updateSelectionKeys(nlohmann::json& msg);
	void updateMessageWindow(nlohmann::json& msg, Ime::EditSession* session, bool& endComposition);
	void updateCommitString(nlohmann::json& msg, Ime::EditSession* session);
	void updateComposition(nlohmann::json& msg, Ime::EditSession* session, bool& endComposition);
	void updateLanguageButtons(nlohmann::json& msg);
	void updatePreservedKeys(nlohmann::json& msg);
	void updateKeyboardStatus(nlohmann::json& msg);
	void updateCandidateList(nlohmann::json& msg, Ime::EditSession* session);
	void updateUI(nlohmann::json& data);
	void updateStatus(nlohmann::json& msg, Ime::EditSession* session = nullptr);

private:
	TextService* textService_;
	std::string guid_;
	HANDLE pipe_;
	std::unordered_map<std::string, Ime::ComPtr<PIME::LangBarButton>> buttons_; // map buttons to string IDs
	unsigned int nextSeqNum_;
	bool isActivated_;
	bool shouldWaitConnection_;
	std::string readBuffer_;
	HANDLE ioEvent_;
};

}

#endif // _PIME_CLIENT_H_
