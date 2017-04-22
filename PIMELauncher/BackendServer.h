//
//	Copyright (C) 2015 - 2016 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
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

#ifndef _BACKEND_SERVER_H_
#define _BACKEND_SERVER_H_

#include <Windows.h>
#include <ShlObj.h>
#include <Shellapi.h>
#include <Lmcons.h> // for UNLEN
#include <cstring>
#include <string>
#include <vector>
#include <unordered_map>

#include <uv.h>
#include <json/json.h>

namespace PIME {

class PipeServer;
struct ClientInfo;

class BackendServer {
public:
	friend class PipeServer;

	BackendServer(PipeServer* pipeServer, const Json::Value& info);
	~BackendServer();

	void startProcess();
	void terminateProcess();
	bool isProcessRunning();

	uv_stream_t* stdinStream() {
		return reinterpret_cast<uv_stream_t*>(stdinPipe_);
	}

	uv_stream_t* stdoutStream() {
		return reinterpret_cast<uv_stream_t*>(stdoutPipe_);
	}

	void handleClientMessage(ClientInfo* client, const char* readBuf, size_t len);

private:
	static void allocReadBuf(uv_handle_t*, size_t suggested_size, uv_buf_t* buf);
	void onProcessDataReceived(uv_stream_t* stream, ssize_t nread, const uv_buf_t* buf);
	void onProcessTerminated(int64_t exit_status, int term_signal);
	void closeStdioPipes();

private:
	PipeServer* pipeServer_;
	std::string name_;
	uv_process_t* process_;
	uv_pipe_t* stdinPipe_;
	uv_pipe_t* stdoutPipe_;
	bool ready_;

	// command to launch the server process
	std::string command_;
	std::string params_;
	std::string workingDir_;
};

} // namespace PIME

#endif // _BACKEND_SERVER_H_
