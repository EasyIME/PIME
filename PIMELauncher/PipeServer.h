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
#include <rpc.h> // for UuidCreate
#include <cstring>
#include <string>
#include <vector>
#include <unordered_map>
#include <queue>
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


class PipeServer {
public:
	PipeServer();

	~PipeServer();

	int exec(LPSTR cmd);

	static PipeServer* get() { // get the singleton object
		return singleton_;
	}

	void quit();

	void handleBackendReply(const char* readBuf, size_t len);

	void outputDebugMessage(const char* msg, size_t len);

	BackendServer* backendFromLangProfileGuid(const char* guid);

	BackendServer* backendFromName(const char* name);

	void onBackendClosed(BackendServer* backend);

private:
	// backend server
	void initBackendServers(const std::wstring& topDirPath);
	void finalizeBackendServers();
	void initInputMethods(const std::wstring& topDirPath);

	static std::string getPipeName(const char* base_name);
	void initSecurityAttributes();
	void initPipe(uv_pipe_t* pipe, const char * app_name, SECURITY_ATTRIBUTES* sa = nullptr);
	void terminateExistingLauncher();
	void parseCommandLine(LPSTR cmd);
	// bool launchBackendByName(const char* name);

	void onNewClientConnected(uv_stream_t* server, int status);
	void onClientDataReceived(uv_stream_t* stream, ssize_t nread, const uv_buf_t* buf);
	void handleClientMessage(ClientInfo* client, const char* readBuf, size_t len);
	void closeClient(ClientInfo* client);

	void onNewDebugClientConnected(uv_stream_t* server, int status);
	void closeDebugClient();

	void sendReplyToClient(const std::string clientId, const char* msg, size_t len);

private:
	// security attribute stuff for creating the server pipe
	PSECURITY_DESCRIPTOR securittyDescriptor_;
	SECURITY_ATTRIBUTES securityAttributes_;
	PACL acl_;
	EXPLICIT_ACCESS explicitAccesses_[2];
	PSID everyoneSID_;
	PSID allAppsSID_;
	
	std::wstring topDirPath_;
	bool quitExistingLauncher_;
	static PipeServer* singleton_;
	std::vector<ClientInfo*> clients_;
	uv_pipe_t serverPipe_; // main server pipe accepting connections from the clients
	uv_pipe_t debugServerPipe_; // pipe used for communicate with the debug console
	uv_pipe_t* debugClientPipe_; // connected client pipe of the debug console

	std::vector<BackendServer*> backends_;
	std::unordered_map<std::string, BackendServer*> backendMap_;
};

} // namespace PIME

#endif // _PIME_PIPE_SERVER_H_
