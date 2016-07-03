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
#include <libIME/TextService.h>
#include <libIME/KeyEvent.h>
#include <libIME/EditSession.h>
#include "PIMELangBarButton.h"

#include <unordered_map>
#include <string>
#include <json/json.h>

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
	HANDLE connectPipe(const wchar_t* pipeName);
	bool connectServerPipe();
	bool launchServer();
	bool sendRequestText(HANDLE pipe, const char* data, int len, std::string& reply);
	bool sendRequest(Json::Value& req, Json::Value& result);
	void closePipe();
	void init();

	void keyEventToJson(Ime::KeyEvent& keyEvent, Json::Value& jsonValue);
	bool handleReply(Json::Value& msg, Ime::EditSession* session = nullptr);
	void updateStatus(Json::Value& msg, Ime::EditSession* session = nullptr);
	void updateUI(const Json::Value& data);
	bool sendOnMenu(std::string button_id, Json::Value& result);

	static std::wstring getPipeName(const wchar_t* base_name);

	TextService* textService_;
	std::string guid_;
	HANDLE pipe_;
	std::unordered_map<std::string, PIME::LangBarButton*> buttons_; // map buttons to string IDs
	unsigned int newSeqNum_;
	bool isActivated_;
	bool connectingServerPipe_;
	std::string backend_;
};

}

#endif // _PIME_CLIENT_H_
