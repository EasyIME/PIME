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
#include "../libpipe/libpipe.h"
#include "BackendServer.h"
#include <queue>

class ClientConnection;

struct AsyncRequest {
	OVERLAPPED overlapped;
	ClientConnection*  client;
	char buf[1024];
	DWORD errCode;
	DWORD numBytes;
	bool success;
};


class PIMELauncher {
public:
	enum BackendType {
		BACKEND_PYTHON = 0,
		BACKEND_NODE,
		N_BACKENDS
	};

	PIMELauncher();
	~PIMELauncher();


	int exec(LPSTR cmd);
	static PIMELauncher* get() { // get the singleton object
		return singleton_;
	}

	void quit();

	BackendServer* findBackendForClient(const char* guid) {
		auto it = backendMap_.find(guid);
		if (it != backendMap_.end())  // found the backend for the text service
			return it->second;
		return nullptr;
	}

	BackendServer* findBackendByName(const char* name);

	void queueAsyncResult(AsyncRequest* request) {
		finishedRequests_.push(request);
	}

private:
	static string getPipeName(const char* base_name);
	static DWORD WINAPI clientPipeThread(LPVOID param);
	void initSecurityAttributes();
	HANDLE acceptClientPipe();
	HANDLE createPipe(const wchar_t * app_name);
	void closePipe(HANDLE pipe);
	void terminateExistingLauncher();
	void parseCommandLine(LPSTR cmd);
	bool initBackends();
	bool launchBackendByName(const char* name);

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


	wstring topDirPath_;
	bool quitExistingLauncher_;
	BackendServer backends_[N_BACKENDS];
	static PIMELauncher* singleton_;
	std::unordered_map<std::string, BackendServer*> backendMap_;
	std::unordered_map<HANDLE, ClientConnection*> clients_;
	std::queue<AsyncRequest*> finishedRequests_;
};


#endif // _PIME_LAUNCHER_H_
