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

#include "PipeServer.h"
#include "PipeClient.h"
#include <Windows.h>
#include <windowsx.h>
#include <ShlObj.h>
#include <Shellapi.h>
#include <Lmcons.h> // for UNLEN
#include <iostream>
#include <cstring>
#include <cassert>
#include <string>
#include <vector>
#include <map>
#include <fstream>
#include <algorithm>
#include <codecvt>  // for utf8 conversion
#include <locale>  // for wstring_convert
#include <sstream>

#include <json/json.h>

#include <spdlog/spdlog.h>
#include <spdlog/sinks/stdout_sinks.h>
#include <spdlog/sinks/rotating_file_sink.h> // support for rotating file logging

#include "BackendServer.h"
#include "Utils.h"
#include "../libIME/WindowsVersion.h"

using namespace std;

namespace PIME {

PipeServer* PipeServer::singleton_ = nullptr;
wchar_t PipeServer::singleInstanceMutexName_[] = L"PIMELauncherMutex";

wchar_t PipeServer::wndClassName_[] = L"PIMELauncherWnd";

static wstring_convert<codecvt_utf8<wchar_t>> utf8Codec;

static constexpr UINT WM_SHELL_NOTIFY_ICON = WM_APP + 1;
static constexpr UINT MAIN_SHELL_NOTIFY_ICON_ID = 1;

static constexpr UINT ID_ENABLE_DEBUG_LOG = 1000;
static constexpr UINT ID_SHOW_DEBUG_LOGS = 1001;
static constexpr UINT ID_RESTART_PIME_BACKENDS = 1002;

static constexpr size_t MAX_LOG_FILE_SIZE = 5 * 1024 * 1024; // log file size: 5 MB
static constexpr int NUM_LOG_FILES = 5;  // backup 3 copies of the log file

static constexpr wchar_t CONFIG_FILE_REL_PATH[] = L"\\PIMELauncher.json";


PipeServer::PipeServer() :
	securittyDescriptor_(nullptr),
	acl_(nullptr),
	everyoneSID_(nullptr),
	allAppsSID_(nullptr),
	quitExistingLauncher_(false),
	singleInstanceMutex_(nullptr),
	logLevel_{spdlog::level::warn} {

	// this can only be assigned once
	assert(singleton_ == nullptr);
	singleton_ = this;

	initDataDir();
	loadConfig();
	initLogger();
}

PipeServer::~PipeServer() {
	if (everyoneSID_ != nullptr)
		FreeSid(everyoneSID_);
	if (allAppsSID_ != nullptr)
		FreeSid(allAppsSID_);
	if (securittyDescriptor_ != nullptr)
		LocalFree(securittyDescriptor_);
	if (acl_ != nullptr)
		LocalFree(acl_);
	if (singleInstanceMutex_) {
		::CloseHandle(singleInstanceMutex_);
	}
}

void PipeServer::initDataDir() {
	wchar_t* appLocalDataDirPath = nullptr;
	::SHGetKnownFolderPath(FOLDERID_LocalAppData, 0, NULL, &appLocalDataDirPath);
	dataDirPath_ = std::wstring(appLocalDataDirPath) + L"\\PIME";
	::CoTaskMemFree(appLocalDataDirPath);
	::SHCreateDirectoryEx(NULL, dataDirPath_.c_str(), NULL);
}

void PipeServer::initLogger() {
	auto logDirPath = dataDirPath_ + L"\\Log";
	::SHCreateDirectoryEx(NULL, logDirPath.c_str(), NULL);

	auto logFile = logDirPath + L"\\PIMELauncher.log";
	try {
		logger_ = spdlog::rotating_logger_mt("PIMELauncher", logFile, MAX_LOG_FILE_SIZE, NUM_LOG_FILES);
		spdlog::flush_on(spdlog::level::debug);  // flush to the file on any kind of errors (always flush)
	}
	catch(const spdlog::spdlog_ex& exc) {
		// fail to create file logger, fallback to console logger
		logger_ = spdlog::stderr_logger_mt("PIMELauncher");
	}

	logger_->set_level(logLevel_);
}

void PipeServer::loadConfig() {
	auto configFile = dataDirPath_ + CONFIG_FILE_REL_PATH;
	Json::Value config;
	if (loadJsonFile(configFile, config)) {
		auto levelName = config["logLevel"].asString();
		logLevel_ = spdlog::level::from_str(levelName);
	}
}

void PipeServer::saveConfig() {
	auto configFile = dataDirPath_ + CONFIG_FILE_REL_PATH;
	Json::Value config;
	config["logLevel"] = spdlog::level::to_c_str(logLevel_);
	if (!saveJsonFile(configFile, config)) {
		logger_->error("fail to write config file");
	}
}

void PipeServer::initBackendServers(const std::wstring & topDirPath) {
	// load known backend implementations
	Json::Value backends;
	if (loadJsonFile(topDirPath + L"\\backends.json", backends)) {
		if (backends.isArray()) {
			for (auto it = backends.begin(); it != backends.end(); ++it) {
				auto& backendInfo = *it;
				BackendServer* backend = new BackendServer(this, backendInfo);
				backends_.push_back(backend);
			}
		}
	}

	// maps language profiles to backend names
	initInputMethods(topDirPath);
}

void PipeServer::initInputMethods(const std::wstring& topDirPath) {
	// maps language profiles to backend names
	for (BackendServer* backend : backends_) {
		std::wstring dirPath = topDirPath + L"\\" + utf8Codec.from_bytes(backend->name_) + L"\\input_methods";
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
								std::string guid = json["guid"].asString();
								transform(guid.begin(), guid.end(), guid.begin(), tolower);  // convert GUID to lwoer case
																							 // map text service GUID to its backend server
								backendMap_.insert(std::make_pair(guid, backendFromName(backend->name_.c_str())));
							}
						}
					}
				}
			} while (::FindNextFile(hFind, &findData));
			::FindClose(hFind);
		}
	}
}

void PipeServer::finalizeBackendServers() {
	// try to terminate launched backend server processes
	for (BackendServer* backend : backends_) {
		backend->terminateProcess();
		delete backend;
	}
}

void PipeServer::restartAllBackends() {
	logger_->info("Restart all backends");
	for (auto& backend : backends_) {
		if (backend->isProcessRunning()) {
			backend->restartProcess();
		}
	}
}

BackendServer* PipeServer::backendFromName(const char* name) {
	// for such a small list, linear search is often faster than hash table or map
	for (BackendServer* backend : backends_) {
		if (backend->name_ == name)
			return backend;
	}
	return nullptr;
}

void PipeServer::onBackendClosed(BackendServer * backend) {
	// the backend server is terminated, disconnect all clients using this backend
	auto removed_it = std::remove_if(clients_.begin(), clients_.end(),
		[backend](PipeClient* client) {
		if (client->backend_ == backend) {
			// if the client is using this broken backend, disconnect it
			client->destroy();
			return true;
		}
		return false;
	});
	clients_.erase(removed_it, clients_.cend());
}

BackendServer* PipeServer::backendFromLangProfileGuid(const char* guid) {
	auto it = backendMap_.find(guid);
	if (it != backendMap_.end())  // found the backend for the text service
		return it->second;
	return nullptr;
}

string PipeServer::getPipeName(const char* base_name) {
	string pipe_name;
	char username[UNLEN + 1];
	DWORD unlen = UNLEN + 1;
	if (GetUserNameA(username, &unlen)) {
		// add username to the pipe path so it will not clash with other users' pipes.
		pipe_name = "\\\\.\\pipe\\";
		pipe_name += username;
		pipe_name += "\\PIME\\";
		pipe_name += base_name;
	}
	return pipe_name;
}

void PipeServer::parseCommandLine(LPSTR cmd) {
	int argc;
	wchar_t** argv = CommandLineToArgvW(GetCommandLine(), &argc);
	// parse command line options
	for (int i = 1; i < argc; ++i) {
		const wchar_t* arg = argv[i];
		if (wcscmp(arg, L"/quit") == 0)
			quitExistingLauncher_ = true;
	}
	LocalFree(argv);
}

// send IPC message "quit" to the existing PIME Launcher process.
void PipeServer::terminateExistingLauncher(HWND existingHwnd) {
	PostMessage(existingHwnd, WM_QUIT, 0, 0);
	::DestroyWindow(existingHwnd);
}

void PipeServer::quit() {
	finalizeBackendServers();
	ExitProcess(0); // quit PipeServer
}

PipeClient* PipeServer::clientFromId(const std::string& clientId) {
	PipeClient* client = nullptr;
	// find the client with this ID
	auto it = std::find_if(clients_.cbegin(), clients_.cend(), [clientId](const PipeClient* client) {
		return client->clientId_ == clientId;
	});
	if (it != clients_.cend()) {
		client = *it;
	}
	return client;
}

void PipeServer::initSecurityAttributes() {
	// create security attributes for the pipe
	// http://msdn.microsoft.com/en-us/library/windows/desktop/hh448449(v=vs.85).aspx
	// define new Win 8 app related constants
	memset(&explicitAccesses_, 0, sizeof(explicitAccesses_));
	// Create a well-known SID for the Everyone group.
	// FIXME: we should limit the access to current user only
	// See this article for details: https://msdn.microsoft.com/en-us/library/windows/desktop/hh448493(v=vs.85).aspx

	SID_IDENTIFIER_AUTHORITY worldSidAuthority = SECURITY_WORLD_SID_AUTHORITY;
	AllocateAndInitializeSid(&worldSidAuthority, 1,
		SECURITY_WORLD_RID, 0, 0, 0, 0, 0, 0, 0, &everyoneSID_);

	// https://services.land.vic.gov.au/ArcGIS10.1/edESRIArcGIS10_01_01_3143/Python/pywin32/PLATLIB/win32/Demos/security/explicit_entries.py

	explicitAccesses_[0].grfAccessPermissions = GENERIC_ALL;
	explicitAccesses_[0].grfAccessMode = SET_ACCESS;
	explicitAccesses_[0].grfInheritance = SUB_CONTAINERS_AND_OBJECTS_INHERIT;
	explicitAccesses_[0].Trustee.pMultipleTrustee = NULL;
	explicitAccesses_[0].Trustee.MultipleTrusteeOperation = NO_MULTIPLE_TRUSTEE;
	explicitAccesses_[0].Trustee.TrusteeForm = TRUSTEE_IS_SID;
	explicitAccesses_[0].Trustee.TrusteeType = TRUSTEE_IS_WELL_KNOWN_GROUP;
	explicitAccesses_[0].Trustee.ptstrName = (LPTSTR)everyoneSID_;

	// FIXME: will this work under Windows 7 and Vista?
	// create SID for app containers
	SID_IDENTIFIER_AUTHORITY appPackageAuthority = SECURITY_APP_PACKAGE_AUTHORITY;
	AllocateAndInitializeSid(&appPackageAuthority,
		SECURITY_BUILTIN_APP_PACKAGE_RID_COUNT,
		SECURITY_APP_PACKAGE_BASE_RID,
		SECURITY_BUILTIN_PACKAGE_ANY_PACKAGE,
		0, 0, 0, 0, 0, 0, &allAppsSID_);

	explicitAccesses_[1].grfAccessPermissions = GENERIC_ALL;
	explicitAccesses_[1].grfAccessMode = SET_ACCESS;
	explicitAccesses_[1].grfInheritance = SUB_CONTAINERS_AND_OBJECTS_INHERIT;
	explicitAccesses_[1].Trustee.pMultipleTrustee = NULL;
	explicitAccesses_[1].Trustee.MultipleTrusteeOperation = NO_MULTIPLE_TRUSTEE;
	explicitAccesses_[1].Trustee.TrusteeForm = TRUSTEE_IS_SID;
	explicitAccesses_[1].Trustee.TrusteeType = TRUSTEE_IS_GROUP;
	explicitAccesses_[1].Trustee.ptstrName = (LPTSTR)allAppsSID_;

	// create DACL
	DWORD err = SetEntriesInAcl(2, explicitAccesses_, NULL, &acl_);
	if (0 == err) {
		// security descriptor
		securittyDescriptor_ = (PSECURITY_DESCRIPTOR)LocalAlloc(LPTR, SECURITY_DESCRIPTOR_MIN_LENGTH);
		InitializeSecurityDescriptor(securittyDescriptor_, SECURITY_DESCRIPTOR_REVISION);

		// Add the ACL to the security descriptor. 
		SetSecurityDescriptorDacl(securittyDescriptor_, TRUE, acl_, FALSE);
	}

	securityAttributes_.nLength = sizeof(SECURITY_ATTRIBUTES);
	securityAttributes_.lpSecurityDescriptor = securittyDescriptor_;
	securityAttributes_.bInheritHandle = TRUE;
}


// References:
// https://msdn.microsoft.com/en-us/library/windows/desktop/aa365588(v=vs.85).aspx
void PipeServer::initPipe(uv_pipe_t* pipe, const char* app_name, SECURITY_ATTRIBUTES* sa) {
	wchar_t username[UNLEN + 1];
	DWORD unlen = UNLEN + 1;
	if (GetUserNameW(username, &unlen)) {
		// add username to the pipe path so it will not clash with other users' pipes.
		char pipe_name[MAX_PATH];
		std::string utf8_username = utf8Codec.to_bytes(username, username + unlen);
		sprintf(pipe_name, "\\\\.\\pipe\\%s\\PIME\\%s", utf8_username.c_str(), app_name);
		// create the pipe
		uv_pipe_init_windows_named_pipe(uv_default_loop(), pipe, 0, PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE, sa);
		pipe->data = this;
		uv_pipe_bind(pipe, pipe_name);
	}
}


void PipeServer::acceptClient(PipeClient* client) {
	auto serverStream = reinterpret_cast<uv_stream_t*>(&serverPipe_);
	uv_accept(serverStream, client->stream());
	clients_.push_back(client);
}

void PipeServer::removeClient(PipeClient* client) {
	clients_.erase(find(clients_.begin(), clients_.end(), client));
}

void PipeServer::onNewClientConnected(uv_stream_t* server, int status) {
	auto server_pipe = reinterpret_cast<uv_pipe_t*>(server);
	auto client = new PipeClient{this, server_pipe->pipe_mode, server_pipe->security_attributes };
	acceptClient(client);
	client->startReadPipe();
}

int PipeServer::exec(LPSTR cmd) {
	parseCommandLine(cmd);

	if (quitExistingLauncher_) { // terminate existing launcher process
		if (HWND existingHwnd = ::FindWindow(wndClassName_, nullptr)) {
			terminateExistingLauncher(existingHwnd);
		}
		return 0;
	}

	// ensure that only one instance of PIMELauncher can be running
	singleInstanceMutex_ = ::CreateMutex(NULL, FALSE, singleInstanceMutexName_);
	if (GetLastError() == ERROR_ALREADY_EXISTS) {
		// mutex already exists: found an existing process.
		return 0;
	}

	// get the PIME installation directory
	wchar_t exeFilePathBuf[MAX_PATH];
	DWORD len = GetModuleFileNameW(NULL, exeFilePathBuf, MAX_PATH);
	exeFilePathBuf[len] = '\0';

	// Ask Windows to restart our process when crashes happen.
	RegisterApplicationRestart(exeFilePathBuf, 0);

	// strip the filename part to get dir path
	wchar_t* p = wcsrchr(exeFilePathBuf, '\\');
	if (p)
		*p = '\0';
	topDirPath_ = exeFilePathBuf;

	// must set CWD to our dir. otherwise the backends won't launch.
	::SetCurrentDirectoryW(topDirPath_.c_str());

	// this is the first instance
	initBackendServers(topDirPath_);

	// preparing for the server pipe
	SECURITY_ATTRIBUTES* sa = nullptr;
	if (Ime::WindowsVersion().isWindows8Above()) {
		// Setting special security attributes to the named pipe is only needed 
		// for Windows >= 8 since older versions do not have app containers (metro apps) 
		// in which connecting to pipes are blocked by default permission settings.
		initSecurityAttributes();
		sa = &securityAttributes_;
	}
	// initialize the server pipe
	initPipe(&serverPipe_, "Launcher", sa);

	// listen to events from clients
	uv_listen(reinterpret_cast<uv_stream_t*>(&serverPipe_), 32, [](uv_stream_t* server, int status) {
		PipeServer* _this = (PipeServer*)server->data;
		_this->onNewClientConnected(server, status);
	});

	// run GUI message loop in another worker thread
	uv_thread_t uiThread;
	uv_thread_create(&uiThread, [](void* arg) {
		reinterpret_cast<PipeServer*>(arg)->runGuiThread();
	}, this);

	// run the main loop
	uv_run(uv_default_loop(), UV_RUN_DEFAULT);

	uv_thread_join(&uiThread);  // wait for the GUI message loop to quit
	return 0;
}

// Window procedure of the main window
// this method is called from an worker thread other than the main thread
LRESULT PipeServer::wndProc(UINT msg, WPARAM wp, LPARAM lp) {
	switch (msg) {
	case WM_CREATE:
		return TRUE;
	case WM_SHELL_NOTIFY_ICON:
		// shell tray notification icon events
		// reference: https://www.codeproject.com/Articles/4768/Basic-use-of-Shell-NotifyIcon-in-Win32
		switch (LOWORD(lp)) {
		case WM_RBUTTONDOWN:
			showPopupMenu();
			return 0;
		}
		break;
	case WM_COMMAND:
		switch (LOWORD(wp)) {
		case ID_RESTART_PIME_BACKENDS:
			restartAllBackends();
			return 0;
		case ID_ENABLE_DEBUG_LOG:
			// toggle between log_level: warning <--> debug
			logLevel_ = (logLevel_ <= spdlog::level::debug) ? spdlog::level::warn : spdlog::level::debug;
			logger_->set_level(logLevel_);
			saveConfig();
			break;
		case ID_SHOW_DEBUG_LOGS:
			// show logs dir
			::ShellExecuteW(hwnd_, L"open", (dataDirPath_ + L"\\Log").c_str(), nullptr, nullptr, SW_SHOWNORMAL);
			break;
		}
		break;
	default:
		return ::DefWindowProc(hwnd_, msg, wp, lp);
	}
	return 0;
}

LPCTSTR PipeServer::registerWndClass(WNDCLASSEX& wndClass) const {
	std::memset(&wndClass, 0, sizeof(wndClass));
	wndClass.cbSize = sizeof(wndClass);
	wndClass.hInstance = HINSTANCE(::GetModuleHandle(NULL));
	wndClass.lpszClassName = wndClassName_;
	wndClass.lpfnWndProc = [](HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) -> LRESULT {
		if (msg == WM_NCCREATE) {
			auto cs = reinterpret_cast<CREATESTRUCT*>(lp);
			::SetWindowLongPtr(hwnd, GWL_USERDATA, LONG_PTR(cs->lpCreateParams));
			return TRUE;
		}
		else {
			auto pObj = reinterpret_cast<PipeServer*>(::GetWindowLongPtr(hwnd, GWL_USERDATA));
			if (pObj) {
				return pObj->wndProc(msg, wp, lp);
			}
		}
		return 0;
	};

	auto wndClassAtom = ::RegisterClassEx(&wndClass);
	return LPCTSTR(wndClassAtom);
}

void PipeServer::createShellNotifyIcon() {
	memset(&shellNotifyIconData_, 0, sizeof(shellNotifyIconData_));
	shellNotifyIconData_.cbSize = sizeof(shellNotifyIconData_);
	shellNotifyIconData_.uVersion = NOTIFYICON_VERSION_4; // newer version after Windows Vista
	shellNotifyIconData_.hWnd = hwnd_;
	shellNotifyIconData_.uID = MAIN_SHELL_NOTIFY_ICON_ID;
	shellNotifyIconData_.uFlags = NIF_ICON | NIF_TIP | NIF_MESSAGE;
	shellNotifyIconData_.uCallbackMessage = WM_SHELL_NOTIFY_ICON;
	// auto hinstance = HINSTANCE(::GetModuleHandle(NULL));
	// shellNotifyIconData_.hIcon = ::LoadIcon(hinstance, IDI_APPLICATION);
	shellNotifyIconData_.hIcon = ::LoadIcon(NULL, IDI_APPLICATION);

	// FIXME: make this translatable later
	wcscpy(shellNotifyIconData_.szTip, L"PIME Launcher");

	::Shell_NotifyIcon(NIM_ADD, &shellNotifyIconData_);
}

void PipeServer::destroyShellNotifyIcon() {
	::Shell_NotifyIcon(NIM_DELETE, &shellNotifyIconData_);
}

void PipeServer::showPopupMenu() const {
	// NOTE: according to the API doc of NOTIFYICONDATA, we should able to get x & y pos from WPARAM.
	// However, it does not work in Windows 10 during my experiment. So we get cursor pos instead.
	POINT pos;
	::GetCursorPos(&pos);

	HMENU hmenu = ::CreatePopupMenu();
	// FIXME: make this translatable later
	bool debugEnabled = logLevel_ <= spdlog::level::debug;
	::AppendMenu(hmenu, MF_STRING|MF_ENABLED|(debugEnabled ? MF_CHECKED : 0), ID_ENABLE_DEBUG_LOG, L"Enable Debug Log");
	::AppendMenu(hmenu, MF_STRING | MF_ENABLED, ID_SHOW_DEBUG_LOGS, L"Show Debug Logs");
	::AppendMenu(hmenu, MF_SEPARATOR, 0, 0);
	::AppendMenu(hmenu, MF_STRING | MF_ENABLED, ID_RESTART_PIME_BACKENDS, L"Restart PIME");

	::SetForegroundWindow(hwnd_);
	::TrackPopupMenu(hmenu, TPM_LEFTALIGN| TPM_BOTTOMALIGN, pos.x, pos.y, 0, hwnd_, NULL);
	::DestroyMenu(hmenu);
}


// Main Windows UI message loop
void PipeServer::runGuiThread() {
	// this method is called from an worker thread other than the main thread
	// For libuv, it's only safe to use uv_aysnc_*() from within this thread.

	WNDCLASSEX wndClass;
	auto wndClassAtom = registerWndClass(wndClass);
	hwnd_ = ::CreateWindowEx(0, LPCTSTR(wndClassAtom), NULL, 0, 0, 0, 0, 0, HWND_DESKTOP, NULL, wndClass.hInstance, this);

	createShellNotifyIcon();

	MSG msg;
	while (::GetMessage(&msg, NULL, 0, 0)) {
		::TranslateMessage(&msg);
		::DispatchMessage(&msg);
	}

	destroyShellNotifyIcon();

	::ExitProcess(0);
}


} // namespace PIME
