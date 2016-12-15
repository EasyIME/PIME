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

#ifndef _PIME_PIPE_SERVER_H_
#define _PIME_PIPE_SERVER_H_

#include <Windows.h>
#include <ShlObj.h>
#include <Shellapi.h>
#include <Lmcons.h> // for UNLEN
#include <Winnt.h> // for security attributes constants
#include <aclapi.h> // for ACL
#include <cstring>
#include <string>
#include <vector>
#include <unordered_map>
#include <queue>
#include <memory>
#include "BackendServer.h"


namespace PIME {

struct ClientInfo {
	HANDLE pipe_;
	BackendServer* backend_;
	std::string textServiceGuid_;
	std::string clientId_;

	std::string readBuf_;

	ClientInfo(HANDLE pipe) :
		pipe_(pipe),
		backend_(nullptr) {
	}
};


class PipeServer;

struct AsyncRequest {
	enum Type {
		ASYNC_READ,
		ASYNC_WRITE
	};

	OVERLAPPED overlapped_;
	PipeServer* server_;
	std::weak_ptr<ClientInfo>  client_;
	Type type_;
	std::unique_ptr<char[]> buf_;
	int bufSize_;
	DWORD errCode_;
	DWORD numBytes_;
	bool success_;

	AsyncRequest(PipeServer* server, const std::shared_ptr<ClientInfo>& client, Type type, int bufSize, const char* bufContent = nullptr) :
		server_(server),
		client_(client),
		type_(type),
		buf_(new char[bufSize]),
		bufSize_(bufSize),
		errCode_(0),
		numBytes_(0),
		success_(false) {
		memset(&overlapped_, 0, sizeof(OVERLAPPED));
		if (bufContent != nullptr) {
			memcpy(buf_.get(), bufContent, bufSize);
		}
	}

	~AsyncRequest() {
	}
};


class PipeServer {
public:

	PipeServer();
	~PipeServer();

	int exec(LPSTR cmd);
	static PipeServer* get() { // get the singleton object
		return singleton_;
	}

	void quit();

	void readClient(const std::shared_ptr<ClientInfo>& client);
	void writeClient(const std::shared_ptr<ClientInfo>& client, const char* data, int len);
	void closeClient(const std::shared_ptr<ClientInfo>& client);

private:
	static std::string getPipeName(const char* base_name);
	void initSecurityAttributes();
	HANDLE acceptClientPipe();
	HANDLE createPipe(const wchar_t * app_name);
	void closePipe(HANDLE pipe);
	void terminateExistingLauncher();
	void parseCommandLine(LPSTR cmd);
	// bool launchBackendByName(const char* name);

	static void CALLBACK _onFinishedCallback(DWORD err, DWORD numBytes, OVERLAPPED* overlapped);

	void onReadFinished(AsyncRequest* req);

	void onWriteFinished(AsyncRequest* req);

	void handleClientMessage(const std::shared_ptr<ClientInfo>& client);

private:
	// security attribute stuff for creating the server pipe
	PSECURITY_DESCRIPTOR securittyDescriptor_;
	SECURITY_ATTRIBUTES securityAttributes_;
	PACL acl_;
	EXPLICIT_ACCESS explicitAccesses_[2];
	PSID everyoneSID_;
	PSID allAppsSID_;

	OVERLAPPED connectPipeOverlapped_;
	bool pendingPipeConnection_;

	std::wstring topDirPath_;
	bool quitExistingLauncher_;
	static PipeServer* singleton_;
	std::unordered_map<HANDLE, std::shared_ptr<ClientInfo>> clients_;
	std::queue<AsyncRequest*> finishedRequests_;
};

} // namespace PIME

#endif // _PIME_PIPE_SERVER_H_
