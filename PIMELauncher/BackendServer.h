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
#include <sstream>
#include <memory>

#include <json/json.h>
#include <spdlog/spdlog.h>

#include "UvPipe.h"

namespace PIME {

class PipeServer;
class PipeClient;

class BackendServer {
public:
	friend class PipeServer;

	BackendServer(PipeServer* pipeServer, const Json::Value& info);

	~BackendServer();

	const std::string name() const {
		return name_;
	}

	void startProcess();

	void terminateProcess();

	bool isProcessRunning();

	void restartProcess();

	std::shared_ptr<spdlog::logger>& logger();

	void handleClientMessage(PipeClient* client, const char* readBuf, size_t len);

private:
    uv::Pipe* createStdinPipe();

    uv::Pipe* createStdoutPipe();

    uv::Pipe* createStderrPipe();

    void onStdoutRead(const char* buf, size_t len);

    void onStderrRead(const char* buf, size_t len);

    void onReadError(int status);

	void onProcessTerminated(int64_t exit_status, int term_signal);

    void closeStdioPipes();

	void handleBackendReply();

private:
	PipeServer* pipeServer_;
	std::string name_;
	uv_process_t* process_;
	uv::Pipe* stdinPipe_;
    uv::Pipe* stdoutPipe_;
    uv::Pipe* stderrPipe_;
	std::stringstream stdoutReadBuf_;

	bool needRestart_;
	// command to launch the server process
	std::string command_;
	std::string params_;
	std::string workingDir_;
};

} // namespace PIME

#endif // _BACKEND_SERVER_H_
