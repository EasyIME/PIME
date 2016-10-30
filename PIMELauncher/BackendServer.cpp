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

#include "PIMELauncher.h"
#include <Windows.h>
#include <ShlObj.h>
#include <Shellapi.h>
#include <Lmcons.h> // for UNLEN
#include <cstring>
#include <cassert>
#include <string>
#include <vector>
#include <map>
#include <fstream>
#include <algorithm>
#include <json/json.h>
#include "BackendServer.h"

using namespace std;

HINTERNET BackendServer::internet_ = NULL;

BackendServer BackendServer::backends_[N_BACKENDS];

std::unordered_map<std::string, BackendServer*> BackendServer::backendMap_;

// static
void BackendServer::init(const std::wstring& topDirPath) {
	// FIXME: make this configurable from config files??
	// the python backend
	BackendServer& backend = backends_[BACKEND_PYTHON];
	backend.name_ = "python";
	backend.apiHost_ = "127.0.0.1";
	backend.apiPort_ = 5566;
	backend.command_ = topDirPath;
	backend.command_ += L"\\python\\python3\\python.exe";
	backend.workingDir_ = topDirPath;
	backend.workingDir_ += L"\\python";
	// the parameter needs to be quoted
	backend.params_ = L"\"" + backend.workingDir_ + L"\\server.py\"";

	BackendServer& backend2 = backends_[BACKEND_NODE];
	backend2.name_ = "node";
	backend2.apiHost_ = "127.0.0.1";
	backend.apiPort_ = 5566;
	backend2.command_ = topDirPath;
	backend2.command_ += L"\\node\\node.exe";
	backend2.workingDir_ = topDirPath;
	backend2.workingDir_ += L"\\node";
	// the parameter needs to be quoted
	backend2.params_ = L"\"" + backend2.workingDir_ + L"\\server.js\"";

	// maps language profiles to backend names
	initInputMethods(topDirPath);

	// initialize WinInet for http functions
	internet_ = InternetOpenA(NULL, INTERNET_OPEN_TYPE_DIRECT, NULL, NULL, 0);
}

// static
void BackendServer::initInputMethods(const std::wstring& topDirPath) {
	// maps language profiles to backend names
	ifstream stream(topDirPath + L"\\profile_backends.cache");
	string line;
	while (getline(stream, line)) {
		if (line.empty())
			continue;
		size_t sep = line.find('\t');
		if (sep != -1) {
			string guid = line.substr(0, sep);
			transform(guid.begin(), guid.end(), guid.begin(), tolower);  // convert GUID to lwoer case
			string backendName = line.substr(sep + 1);
			// map text service GUID to its backend server
			backendMap_.insert(std::make_pair(guid, fromName(backendName.c_str())));
		}
	}
	stream.close();
}

// static
void BackendServer::finalize() {
	// try to terminate launched backend server processes
	for (int i = 0; i < 2; ++i) {
		backends_[i].terminate();
	}

	InternetCloseHandle(internet_);
}

BackendServer::BackendServer():
	apiPort_(0),
	httpConnection_(NULL),
	process_(INVALID_HANDLE_VALUE) {
}

BackendServer::~BackendServer() {
	terminate();
}

void BackendServer::start() {
	if(process_ == INVALID_HANDLE_VALUE) {
		// create the child process
		PROCESS_INFORMATION pi;
		memset(&pi, 0, sizeof(pi));

		STARTUPINFO si;
		memset(&si, 0, sizeof(si));
		si.cb = sizeof(si);
		si.wShowWindow = SW_HIDE;
		si.dwFlags = STARTF_USESHOWWINDOW;

		std::wstring commandLine;
		commandLine += L'\"';
		commandLine += command_;
		commandLine += L"\" ";

		commandLine += params_;

		wchar_t* commandLineBuf = wcsdup(commandLine.c_str());  // the buffer needs to be writable
		if (CreateProcessW(NULL, commandLineBuf, NULL, NULL, TRUE, 0, NULL, workingDir_.c_str(), &si, &pi)) {
			process_ = pi.hProcess;
		}
		free(commandLineBuf);
	}
}

void BackendServer::terminate() {
	if (isRunning()) {
		if (httpConnection_) {
			/*
			FIXME:
			if (handleClientMessage(std::string("quit")).empty())
				// the RPC call fails, force termination
				::TerminateProcess(process_, 0);
			*/
			InternetCloseHandle(httpConnection_);
			httpConnection_ = NULL;
		}
		::WaitForSingleObject(process_, 3000); // wait for 3 seconds for the process to terminate
		CloseHandle(process_);
		process_ = INVALID_HANDLE_VALUE;
	}
}

bool BackendServer::isRunning() {
	if (process_ != INVALID_HANDLE_VALUE) {
		DWORD code;
		if (GetExitCodeProcess(process_, &code) && code == STILL_ACTIVE) {
			return true;
		}
		// the process is dead, close its handle
		CloseHandle(process_);
		process_ = INVALID_HANDLE_VALUE;
	}
	return false;
}

bool BackendServer::ping(int timeout) {
	bool success = false;
	// make sure the backend server is running
	if (!httpConnection_)
		httpConnection_ = InternetConnectA(internet_, apiHost_.c_str(), apiPort_, NULL, NULL, INTERNET_SERVICE_HTTP, 0, NULL);

	if (httpConnection_) {
		HINTERNET req = HttpOpenRequestA(httpConnection_, "GET", "/", NULL, NULL, NULL, 0, NULL);
		if (req) {
			if (HttpSendRequestA(req, NULL, 0, NULL, 0)) {
				char buf[32];
				DWORD read_len = 0;
				while (InternetReadFile(req, buf, 31, &read_len)) {
					if (read_len == 0)
						break;
					buf[read_len] = 0;
					success = strcmp(buf, "pong");
				}
			}
			InternetCloseHandle(req);
		}
	}
	return success;
}

std::string BackendServer::newClient() {
	std::string response = sendHttpRequest("POST", "/");
	return response;
}

void BackendServer::removeClient(const std::string& clientId) {
	std::string response = sendHttpRequest("DELETE", ("/" + clientId).c_str());
}

std::string BackendServer::handleClientMessage(const std::string& clientId, const std::string& message) {
	std::string response = sendHttpRequest("POST", ("/" + clientId).c_str(), message.c_str(), message.length());
	return response;
}

BackendServer* BackendServer::fromName(const char* name) {
	// for such a small list, linear search is often faster than hash table or map
	for (int i = 0; i < N_BACKENDS; ++i) {
		BackendServer& backend = backends_[i];
		if (backend.name_ == name)
			return &backend;
	}
	return nullptr;
}

BackendServer* BackendServer::fromTextServiceGuid(const char* guid) {
	auto it = backendMap_.find(guid);
	if (it != backendMap_.end())  // found the backend for the text service
		return it->second;
	return nullptr;
}

std::string BackendServer::sendHttpRequest(const char* method, const char* path, const char* data, int len) {
	std::string response;
	if (ensureConnection()) { // ensure the http connection
		HINTERNET req = HttpOpenRequestA(httpConnection_, method, path, NULL, NULL, NULL, 0, NULL);
		if (req) {
			if (HttpSendRequestA(req, NULL, 0, (void*)data, len)) {
				char buf[1024];
				DWORD read_len = 0;
				while (InternetReadFile(req, buf, 1023, &read_len)) {
					if (read_len == 0)
						break;
					buf[read_len] = 0;
					response += buf;
				}
			}
			InternetCloseHandle(req);
		}
	}
	return response;
}

bool BackendServer::ensureConnection() {
	if (!isRunning()) {
		//start();
	}

	if (!httpConnection_) {
		httpConnection_ = InternetConnectA(internet_, apiHost_.c_str(), apiPort_, NULL, NULL, INTERNET_SERVICE_HTTP, 0, NULL);
		return httpConnection_ != NULL;
	}
	return true;
}
