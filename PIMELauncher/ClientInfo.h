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

#ifndef _PIME_CLIENT_INFO_H_
#define _PIME_CLIENT_INFO_H_

#include <Windows.h>
#include <memory>
#include "BackendServer.h"

#include <uv.h>


namespace PIME {

class PipeServer;
class BackendServer;

struct ClientInfo {
	BackendServer* backend_;
	std::string textServiceGuid_;
	std::string clientId_;
	uv_pipe_t pipe_;
	PipeServer* server_;

	ClientInfo(PipeServer* server);

	uv_stream_t* stream() {
		return reinterpret_cast<uv_stream_t*>(&pipe_);
	}

	bool isInitialized() const;

	bool init(const Json::Value& params);
};

} // namespace PIME

#endif // _PIME_CLIENT_INFO_H_
