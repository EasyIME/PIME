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
#include <WinInet.h>
#include <json/json.h>

namespace PIME {

class BackendServer {
public:

	BackendServer();
	BackendServer(const Json::Value& info);
	~BackendServer();

	static void init(const std::wstring& topDirPath);
	static void finalize();

	static BackendServer* fromLangProfileGuid(const char* guid);
	static BackendServer* fromName(const char* name);

	void startProcess();
	void terminateProcess();
	bool isProcessRunning();

	std::string addNewClient();
	void removeClient(const std::string& clientId);

	std::string handleClientMessage(const std::string& clientId, const std::string& message);

private:
	static void initInputMethods(const std::wstring& topDirPath);
	bool ensureProcessRunning();
	bool ensureHttpConnection();
	bool readHttpServerStatus(double timeoutSeconds = 0.0);
	std::string sendHttpRequest(const char* method, const char* path, const char* data = nullptr, int len = 0);

private:
	std::string name_;

	// the web API endpoint of the backend
	std::string protocol_;  // should be http or https
	std::string apiHost_;
	int apiPort_;
	std::string accessToken_;
	std::string httpBasicAuth_;
	bool httpServerReady_;
	HINTERNET httpConnection_; // http connection

	// command to launch the server process
	std::wstring command_;
	std::wstring params_;
	std::wstring workingDir_;
	HANDLE processHandle_;
	DWORD processId_;
	FILETIME processStartTime_;

	static HINTERNET internet_;
	static std::vector<BackendServer*> backends_;
	static std::unordered_map<std::string, BackendServer*> backendMap_;
};

} // namespace PIME

#endif // _BACKEND_SERVER_H_
