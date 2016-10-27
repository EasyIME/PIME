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

#include <Windows.h>
#include <ShlObj.h>
#include <Shellapi.h>
#include <Lmcons.h> // for UNLEN
#include <cstring>
#include <cassert>
#include <chrono>  // C++ 11 clock functions
#include <string>
#include <vector>
#include <map>
#include <fstream>
#include <algorithm>
#include <codecvt>  // for utf8 conversion
#include <locale>  // for wstring_convert
#include <json/json.h>
#include "BackendServer.h"
#include "Utils.h"

using namespace std;

namespace PIME {

static wstring_convert<codecvt_utf8<wchar_t>> utf8Codec;

HINTERNET BackendServer::internet_ = NULL;

vector<BackendServer*> BackendServer::backends_;

std::unordered_map<std::string, BackendServer*> BackendServer::backendMap_;

// static
void BackendServer::init(const std::wstring& topDirPath) {
	// load known backend implementations
	Json::Value backends;
	if (loadJsonFile(topDirPath + L"\\backends.json", backends)) {
		if (backends.isArray()) {
			for (auto it = backends.begin(); it != backends.end(); ++it) {
				auto& backendInfo = *it;
				BackendServer* backend = new BackendServer(backendInfo);
				backends_.push_back(backend);
			}
		}
	}

	// maps language profiles to backend names
	initInputMethods(topDirPath);

	// initialize WinInet for http functions
	internet_ = InternetOpenA(NULL, INTERNET_OPEN_TYPE_DIRECT, NULL, NULL, 0);

	// since we use local http servers, it should be very fast.
	/*
	unsigned long timeout = 5000;
	InternetSetOption(internet_, INTERNET_OPTION_CONNECT_TIMEOUT, &timeout, sizeof(timeout));
	InternetSetOption(internet_, INTERNET_OPTION_RECEIVE_TIMEOUT, &timeout, sizeof(timeout));
	*/
}

// static
void BackendServer::initInputMethods(const std::wstring& topDirPath) {
	// maps language profiles to backend names
	for (BackendServer* backend : backends_) {
		std::wstring dirPath = topDirPath + utf8Codec.from_bytes(backend->name_) + L"\\input_methods";
		// scan the dir for lang profile definition files (ime.json)
		WIN32_FIND_DATA findData = { 0 };
		HANDLE hFind = ::FindFirstFile((dirPath + L"\\*").c_str(), &findData);
		if (hFind != INVALID_HANDLE_VALUE) {
			do {
				if (findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) { // this is a subdir
					if (findData.cFileName[0] != '.') {
						std::wstring imejson = dirPath;
						imejson += '\\';
						imejson += findData.cFileName;
						imejson += L"\\ime.json";
						// Make sure the file exists
						DWORD fileAttrib = GetFileAttributesW(imejson.c_str());
						if (fileAttrib != INVALID_FILE_ATTRIBUTES) {
							// load the json file to get the info of input method
							Json::Value json;
							if (loadJsonFile(imejson, json)) {
								std::string guid = json["guid"].asCString();
								transform(guid.begin(), guid.end(), guid.begin(), tolower);  // convert GUID to lwoer case
								// map text service GUID to its backend server
								backendMap_.insert(std::make_pair(guid, fromName(backend->name_.c_str())));
							}
						}
					}
				}
			} while (::FindNextFile(hFind, &findData));
			::FindClose(hFind);
		}
	}
}

// static
void BackendServer::finalize() {
	// try to terminate launched backend server processes
	for (BackendServer* backend : backends_) {
		backend->terminateProcess();
		delete backend;
	}

	InternetCloseHandle(internet_);
}

BackendServer::BackendServer() :
	apiPort_(0),
	httpServerReady_(false),
	httpConnection_(NULL),
	processHandle_(INVALID_HANDLE_VALUE),
	processId_(0) {
}

BackendServer::BackendServer(const Json::Value& info) :
	name_(info["name"].asCString()),
	apiHost_(info["host"].asCString()),
	apiPort_(info["port"].asInt()),
	httpServerReady_(false),
	httpConnection_(NULL),
	command_(utf8Codec.from_bytes(info["command"].asCString())),
	workingDir_(utf8Codec.from_bytes(info["workingDir"].asCString())),
	params_(utf8Codec.from_bytes(info["params"].asCString())),
	processHandle_(INVALID_HANDLE_VALUE),
	processId_(0) {
}

BackendServer::~BackendServer() {
	terminateProcess();
}

void BackendServer::startProcess() {
	if (processHandle_ == INVALID_HANDLE_VALUE) {
		// create the child process
		PROCESS_INFORMATION pi;
		memset(&pi, 0, sizeof(pi));

		STARTUPINFO si;
		memset(&si, 0, sizeof(si));
		si.cb = sizeof(si);
		si.wShowWindow = SW_HIDE;
		si.dwFlags = STARTF_USESHOWWINDOW;

		std::wstring commandLine = (L"\"" + command_ + L"\" " + params_);
		wchar_t* commandLineBuf = wcsdup(commandLine.c_str());  // the buffer needs to be writable
		if (CreateProcessW(NULL, commandLineBuf, NULL, NULL, TRUE, 0, NULL, workingDir_.c_str(), &si, &pi)) {
			processHandle_ = pi.hProcess;
		}
		free(commandLineBuf);

		if (processHandle_ != INVALID_HANDLE_VALUE) {  // the process starts successfully
			processId_ = ::GetProcessId(processHandle_);

			// get the process started time
			FILETIME exitTime, kernTime, userTime;
			::GetProcessTimes(processHandle_, &processStartTime_, &exitTime, &kernTime, &userTime);

			// read the status of the web server (timeout: 5 sec)
			readHttpServerStatus(5.0);
		}
	}
}

void BackendServer::terminateProcess() {
	if (isProcessRunning()) {
		if (httpConnection_) {
			// ask the backend server to stop
			sendHttpRequest("DELETE", "/");
			InternetCloseHandle(httpConnection_);
			httpConnection_ = NULL;
			::WaitForSingleObject(processHandle_, 3000); // wait for 3 seconds for the process to terminate
			if (isProcessRunning()) {  // if the process is still running
				::TerminateProcess(processHandle_, 0);  // force termination (bad!)
				::WaitForSingleObject(processHandle_, 3000); // wait for 3 seconds for the process to terminate
			}
		}
		CloseHandle(processHandle_);
		processHandle_ = INVALID_HANDLE_VALUE;
		processId_ = 0;
		httpServerReady_ = false;
	}
}

// check if the backend web service is ready and get port info
bool BackendServer::readHttpServerStatus(double timeoutSeconds) {
	// the backend web services writes their runtime status to %LOCALAPPDATA%\PIME\status\<backend_name>.json,
	// including the process ID, port number, and access token.
	wchar_t* appDataDir;
	::SHGetKnownFolderPath(FOLDERID_LocalAppData, 0, NULL, &appDataDir);  // get the local app data folder
	std::wstring filename = std::wstring(appDataDir) + L"\\PIME\\status\\" + utf8Codec.from_bytes(name_) + L".json";
	::CoTaskMemFree(appDataDir);

	// try to read the status file repeatedly until success or timeout.
	auto readStartTime = std::chrono::steady_clock::now();
	for (;;) {
		Json::Value status;
		if (loadJsonFile(filename, status)) {
			WIN32_FILE_ATTRIBUTE_DATA attrib;
			GetFileAttributesEx(filename.c_str(), GetFileExInfoStandard, &attrib);
			// check if the file is updated after the process is started
			if (::CompareFileTime(&processStartTime_, &attrib.ftLastWriteTime) < 0) {
				DWORD pid = status.get("pid", 0).asUInt();
				if (pid == processId_) {  // the PID is the same as our backend process
					// read the info
					int port = status.get("port", 0).asInt();
					if (port > 0)
						apiPort_ = port;
					const char* token = status.get("access_token", "").asCString();
					if (token && *token)
						accessToken_ = token;

					httpServerReady_ = true;  // the http server is up and running
					return true;
				}
			}
		}
		auto currentTime = std::chrono::steady_clock::now();
		std::chrono::duration<double> elapsed = currentTime - readStartTime;
		if (elapsed >= std::chrono::duration<double>(timeoutSeconds))
			break;  // timeout! reading server status failed ==> stop!
		::Sleep(100); // wait for a while and try again
	}
	return false;
}

// check if the backend server process is running
bool BackendServer::isProcessRunning() {
	if (processHandle_ != INVALID_HANDLE_VALUE) {
		DWORD code;
		if (GetExitCodeProcess(processHandle_, &code) && code == STILL_ACTIVE) {
			return true;
		}
		// the process is dead, close its process handle and http connection
		CloseHandle(processHandle_);
		processHandle_ = INVALID_HANDLE_VALUE;
		processId_ = 0;
		httpServerReady_ = false;
		if (httpConnection_) {
			InternetCloseHandle(httpConnection_);
			httpConnection_ = NULL;
		}
	}
	return false;
}

std::string BackendServer::addNewClient() {
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
	for (BackendServer* backend : backends_) {
		if (backend->name_ == name)
			return backend;
	}
	return nullptr;
}

BackendServer* BackendServer::fromLangProfileGuid(const char* guid) {
	auto it = backendMap_.find(guid);
	if (it != backendMap_.end())  // found the backend for the text service
		return it->second;
	return nullptr;
}

std::string BackendServer::sendHttpRequest(const char* method, const char* path, const char* data, int len) {
	std::string response;
	if (ensureHttpConnection()) { // ensure the http connection
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

// ensure the backend server is running (if not, start the server as needed)
bool BackendServer::ensureProcessRunning() {
	if (!isProcessRunning()) {
		startProcess(); // start the server process
		return isProcessRunning();
	}
	return true;
}

bool BackendServer::ensureHttpConnection() {
	// ensure the server process is running
	if (!ensureProcessRunning())
		return false;

	// the server process is executed, but http server is not ready
	if (!httpServerReady_) {
		if (!readHttpServerStatus(1.0))  // read the latest server status (timeout: 1 sec)
			return false;
	}

	// ensure we have a valid http connection to the server process
	if (!httpConnection_) {
		httpConnection_ = InternetConnectA(internet_, apiHost_.c_str(), apiPort_, NULL, NULL, INTERNET_SERVICE_HTTP, 0, NULL);
		return httpConnection_ != NULL;
	}
	return true;
}

} // namespace PIME
