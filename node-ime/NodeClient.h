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

#ifndef _NODE_CLIENT_H_
#define _NODE_CLIENT_H_

#include <libIME/TextService.h>
#include <libIME/KeyEvent.h>
#include <libIME/EditSession.h>

#define RAPIDJSON_HAS_STDSTRING	1
#include "rapidjson/document.h"
#include "rapidjson/writer.h"
#include "rapidjson/stringbuffer.h"

namespace Node {

class TextService;

class Client
{
public:
	Client(TextService* service);
	~Client(void);

	// handlers for the text service
	void onActivate();
	void onDeactivate();

	bool filterKeyDown(Ime::KeyEvent& keyEvent);
	bool onKeyDown(Ime::KeyEvent& keyEvent, Ime::EditSession* session);

	bool filterKeyUp(Ime::KeyEvent& keyEvent);
	bool onKeyUp(Ime::KeyEvent& keyEvent, Ime::EditSession* session);

	bool onPreservedKey(const GUID& guid);

	bool onCommand(UINT id, Ime::TextService::CommandType type);

	// called when a compartment value is changed
	void onCompartmentChanged(const GUID& key);

	// called when the keyboard is opened or closed
	void onKeyboardStatusChanged(bool opened);

	// called just before current composition is terminated for doing cleanup.
	void onCompositionTerminated(bool forced);

	void onLangProfileActivated(REFIID lang);

	void onLangProfileDeactivated(REFIID lang);


private:
	bool connectPipe();
	rapidjson::Document sendRequest(std::string req, int seqNo);
	void closePipe();
	void init();

	void keyEventToJson(rapidjson::Writer<rapidjson::StringBuffer>& writer, Ime::KeyEvent& keyEvent);
	int addSeqNum(rapidjson::Writer<rapidjson::StringBuffer>& writer);
	bool isReplyValid(rapidjson::Document& doc);

	TextService* textService_;
	HANDLE pipe_;
};

}

#endif // _NODE_CLIENT_H_
