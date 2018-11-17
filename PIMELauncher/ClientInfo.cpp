//
//	Copyright (C) 2015 - 2018 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
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

#include "ClientInfo.h"
#include "PipeServer.h"

#include "BackendServer.h"

using namespace std;

namespace PIME {

static wstring_convert<codecvt_utf8<wchar_t>> utf8Codec;


ClientInfo::ClientInfo(PipeServer* server) :
	backend_(nullptr), server_{ server } {
}

bool ClientInfo::isInitialized() const {
	return (!clientId_.empty() && backend_ != nullptr);
}

bool ClientInfo::init(const Json::Value & params) {
	const char* method = params["method"].asCString();
	if (method != nullptr) {
		if (strcmp(method, "init") == 0) {  // the client connects to us the first time
			// generate a new uuid for client ID
			UUID uuid;
			UuidCreate(&uuid);
			RPC_CSTR uuid_str = nullptr;
			UuidToStringA(&uuid, &uuid_str);
			clientId_ = (char*)uuid_str;
			RpcStringFreeA(&uuid_str);

			// find a backend for the client text service
			const char* guid = params["id"].asCString();
			backend_ = server_->backendFromLangProfileGuid(guid);
			if (backend_ != nullptr) {
				// FIXME: write some response to indicate the failure
				return true;
			}
		}
	}
	return false;
}

} // namespace PIME
