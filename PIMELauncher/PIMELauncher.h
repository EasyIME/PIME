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

#ifndef _PIME_LAUNCHER_H_
#define _PIME_LAUNCHER_H_

// #include <uv.h>  // need to be put before windows.h for unknown reasons :-(
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
#include "BackendServer.h"
#include <queue>


struct ClientInfo {
	HANDLE pipe_;
	BackendServer* backend_;
	std::string textServiceGuid_;
	std::string clientId_;

	std::string readBuf_;

	ClientInfo(HANDLE pipe):
		pipe_(pipe),
		backend_(nullptr) {
	}
};


class PIMELauncher;

struct AsyncRequest {
	enum Type {
		ASYNC_READ,
		ASYNC_WRITE
	};

	OVERLAPPED overlapped_;
	PIMELauncher* server_;
	ClientInfo*  client_;
	Type type_;
	char *buf_;
	int bufSize_;
	DWORD errCode_;
	DWORD numBytes_;
	bool success_;

	AsyncRequest(PIMELauncher* server, ClientInfo* client, Type type, int bufSize, const char* bufContent = nullptr):
		server_(server),
		client_(client),
		type_(type),
		buf_(new char[bufSize]),
		bufSize_(bufSize),
		errCode_(0),
		numBytes_(0),
		success_(false) {
		memset(&overlapped_, 0, sizeof(OVERLAPPED));
		buf_ = new char[bufSize];
		if (bufContent != nullptr) {
			memcpy(buf_, bufContent, bufSize);
		}
	}

	~AsyncRequest() {
		delete []buf_;
	}
};


class PIMELauncher {
public:

	PIMELauncher();
	~PIMELauncher();

	int exec(LPSTR cmd);
	static PIMELauncher* get() { // get the singleton object
		return singleton_;
	}

	void quit();

	void readClient(ClientInfo* client);
	void writeClient(ClientInfo* client, const char* data, int len);
	void closeClient(ClientInfo* client);

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

	void handleClientMessage(ClientInfo* client);

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
	static PIMELauncher* singleton_;
	std::unordered_map<HANDLE, ClientInfo*> clients_;
	std::queue<AsyncRequest*> finishedRequests_;
};


#endif // _PIME_LAUNCHER_H_
