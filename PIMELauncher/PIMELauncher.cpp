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
#include <algorithm>
#include "../libpipe/libpipe.h"

BackendServer::~BackendServer() {
	terminate();
}

static HANDLE launchProcess(const wchar_t* file, const wchar_t* params, const wchar_t* workingDir) {
	HANDLE process = INVALID_HANDLE_VALUE;
	SHELLEXECUTEINFOW info = { 0 };
	info.cbSize = sizeof(info);
	info.fMask = SEE_MASK_NOCLOSEPROCESS;
	info.lpVerb = L"open";
	info.lpFile = file;
	info.lpParameters = params;
	info.lpDirectory = workingDir;
	info.nShow = SW_SHOWNORMAL;
	if (ShellExecuteExW(&info))
		process = info.hProcess;
	DWORD err = GetLastError();
	return process;
}

void BackendServer::start() {
	if(process_ == INVALID_HANDLE_VALUE)
		process_ = launchProcess(command_.c_str(), params_.c_str(), workingDir_.c_str());
}

void BackendServer::terminate() {
	if (isRunning()) {
		char buf[16];
		DWORD rlen;
		::CallNamedPipeA(pipeName_.c_str(), "quit", 4, buf, sizeof(buf) - 1, &rlen, 1000); // wait for 1 sec.
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


PIMELauncher* PIMELauncher::singleton_ = nullptr;

PIMELauncher::PIMELauncher():
	quit_(false) {
	// this can only be assigned once
	assert(singleton_ == nullptr);
	singleton_ = this;
}

PIMELauncher::~PIMELauncher() {
}

string PIMELauncher::getPipeName(const char* base_name) {
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

// initialize info of supported backends
bool PIMELauncher::initBackends() {
	// get the PIME directory
	DWORD len = GetModuleFileNameW(NULL, topDirPath_, MAX_PATH);
	topDirPath_[len] = '\0';
	wchar_t* p = wcsrchr(topDirPath_, '\\');
	if (!p)
		return false;
	*p = '\0';

	// the python backend
	BackendServer& backend = backends_[0];
	backend.name_ = "python";
	backend.pipeName_ = getPipeName("python");

	backend.command_ = topDirPath_;
	backend.command_ += L"\\python\\pythonw.exe";

	backend.workingDir_ = topDirPath_;
	backend.workingDir_ += L"\\server";

	backend.params_ = L"\"" + backend.workingDir_ + L"\\server.py\"";

	// TODO: node.js backend
	BackendServer& backend2 = backends_[1];
	backend2.name_ = "node";
	backend2.pipeName_ = getPipeName("node");
	return true;
}

BackendServer* PIMELauncher::findBackend(const char* name) {
	// for such a small list, linear search is often faster than hash table or map
	int n_backends = sizeof(backends_) / sizeof(BackendServer);
	for (int i = 0; i < n_backends; ++i) {
		BackendServer& backend = backends_[i];
		if (backend.name_ == name)
			return &backend;
	}
	return nullptr;
}

// initialize language profiles
bool PIMELauncher::initProfiles() {
	// FIXME: load from files instead of hard code
	mapProfilesToBackends_["{F80736AA-28DB-423A-92C9-5540F501C939}"] = findBackend("python");
	mapProfilesToBackends_["{F828D2DC-81BE-466E-9CFE-24BB03172693}"] = findBackend("python");
	return true;
}

void PIMELauncher::parseCommandLine(LPSTR cmd) {
	int argc;
	wchar_t** argv = CommandLineToArgvW(GetCommandLine(), &argc);
	// parse command line options
	for (int i = 1; i < argc; ++i) {
		const wchar_t* arg = argv[i];
		if (wcscmp(arg, L"/quit") == 0)
			quit_ = true;
	}
	LocalFree(argv);
}

// send IPC message "quit" to the existing PIME Launcher process.
void PIMELauncher::terminateExistingLauncher() {
	string pipe_name = getPipeName("Launcher");
	char buf[16];
	DWORD rlen;
	::CallNamedPipeA(pipe_name.c_str(), "quit", 4, buf, sizeof(buf) - 1, &rlen, 1000); // wait for 1 sec.
}

/*
bool PIMELauncher::pingBackendServer(const string& pipe_name) {
	// make sure the backend server is running
	char buf[16];
	DWORD rlen;
	bool success = ::CallNamedPipeA(pipe_name.c_str(), "ping", 4, buf, sizeof(buf) - 1, &rlen, 1000); // wait for 1 sec.
	if (success) {
	}
	return success;
}
*/

string PIMELauncher::handleMessage(const string& msg) {
	string reply;
	if (msg == "quit") { // quit PIME
		// try to terminate launched backend server processes
		for (int i = 0; i < 2; ++i)
			backends_[i].terminate();
		ExitProcess(0); // quit PIMELauncher
	}
	else { // query for the backend pipe address of the language profile GUID
		// msg is a language profile GUID
		auto it = mapProfilesToBackends_.find(msg);
		if (it != mapProfilesToBackends_.end()) { // found a backend
			BackendServer* backend = it->second;
			reply = backend->pipeName_;  // reply with the pipe name of the backend server
			// ensure that the backend server is running...
			if(!backend->isRunning()) {
				backend->start();  // launch the backend server process
			}
		}
	}
	return reply;
}

// called from a worker thread to read the incoming data from the connected pipe
DWORD WINAPI PIMELauncher::clientPipeThread(LPVOID param) {
	HANDLE client_pipe = reinterpret_cast<HANDLE>(param);
	bool running = true;
	while (running) { // run the loop to read data from the pipe
		char buf[512];
		DWORD err;
		bool read_more = true;
		string msg;
		do {
			int rlen = read_pipe(client_pipe, buf, sizeof(buf) - 1, &err);
			if (rlen > 0) {
				buf[rlen] = '\0';
				msg += buf;
			}

			switch (err) {
			case 0: // finish of this message
				read_more = false;
				break;
			case ERROR_MORE_DATA: // need further reads
			case ERROR_IO_PENDING:
				read_more = true;
				break;
			default: // the pipe is broken, disconnect!
				running = false;
				read_more = false;
			}
		} while (read_more);

		// finish reading an incoming message, handle it!
		singleton_->lock();
		// only handle message from one pipe thread at a time
		string reply = singleton_->handleMessage(msg);
		if (!reply.empty()) {
			write_pipe(client_pipe, reply.c_str(), reply.length(), &err);
		}
		singleton_->unlock();
		running = false; // Currently, we only handle one message.
	}
	close_pipe(client_pipe);
	// notify the server that we're done. (maybe using PostThreadMessage? or event?)

	return 0;
}


int PIMELauncher::exec(LPSTR cmd) {
	parseCommandLine(cmd);
	if (quit_) { // terminate existing launcher process
		terminateExistingLauncher();
		return 0;
	}

	// this is the first instance
	if (!initBackends())
		return 1;
	if (!initProfiles())
		return 1;

	// main server loop
	::InitializeCriticalSection(&serverLock_);
	for (;;) {
		// wait for incoming pipe connection
		HANDLE client_pipe = connect_pipe("Launcher"); // this is a blocking call
		if (client_pipe != INVALID_HANDLE_VALUE) { // client connected
			// ::EnterCriticalSection(&lock); // lock mutex
			// clients.push_back(client);
			// ::LeaveCriticalSection(&lock); // unlock mutex
			// run a separate thread for this client
			HANDLE thread = ::CreateThread(NULL, 0, clientPipeThread, reinterpret_cast<LPVOID>(client_pipe), 0, NULL);
		}
	}
	return 0;
}

int WINAPI WinMain(HINSTANCE hinst, HINSTANCE hprev, LPSTR cmd, int show) {
	PIMELauncher launcher;
	return launcher.exec(cmd);
}
