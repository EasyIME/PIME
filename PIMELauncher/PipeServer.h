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
#include <deque>
#include <memory>
#include "BackendServer.h"

#include <uv.h>

#include <spdlog/spdlog.h>


namespace PIME {

class PipeServer;
class BackendServer;
class PipeClient;


class PipeServer {
public:
	PipeServer();

	~PipeServer();

	int exec(LPSTR cmd);

	static PipeServer* get() { // get the singleton object
		return singleton_;
	}

	std::shared_ptr<spdlog::logger>& logger() {
		return logger_;
	}

	void quit();

	BackendServer* backendFromLangProfileGuid(const char* guid);

	BackendServer* backendFromName(const char* name);

	PipeClient* clientFromId(const std::string& clientId);

	void onBackendClosed(BackendServer* backend);

	void removeClient(PipeClient* client);

private:
	// Windows GUI message loop
	void runGuiThread();
	LPCTSTR registerWndClass(WNDCLASSEX& wndClass) const;
	LRESULT wndProc(UINT msg, WPARAM wp, LPARAM lp);
	void createShellNotifyIcon();
	void destroyShellNotifyIcon();
	void showPopupMenu() const;

	// backend server
	void initBackendServers(const std::wstring& topDirPath);
	void finalizeBackendServers();
	void initInputMethods(const std::wstring& topDirPath);
	void restartAllBackends();

	// main pipe server
	void initDataDir();
	void initLogger();
	void loadConfig();
	void saveConfig();
	static std::string getPipeName(const char* base_name);
	void initSecurityAttributes();
	void initPipe(uv_pipe_t* pipe, const char * app_name, SECURITY_ATTRIBUTES* sa = nullptr);
	void terminateExistingLauncher(HWND existingHwnd);
	void parseCommandLine(LPSTR cmd);

	// client handling
	void onNewClientConnected(uv_stream_t* server, int status);
	void acceptClient(PipeClient* client);

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
	static wchar_t singleInstanceMutexName_[];
	std::vector<PipeClient*> clients_;
	uv_pipe_t serverPipe_; // main server pipe accepting connections from the clients

	std::vector<BackendServer*> backends_;
	std::unordered_map<std::string, BackendServer*> backendMap_;

	HWND hwnd_; // handle of the window
	static wchar_t wndClassName_[];
	NOTIFYICONDATA shellNotifyIconData_;

	HANDLE singleInstanceMutex_;

	// error logging
	spdlog::level::level_enum logLevel_;
	std::wstring dataDirPath_;
	std::shared_ptr<spdlog::logger> logger_;
};

} // namespace PIME

#endif // _PIME_PIPE_SERVER_H_
