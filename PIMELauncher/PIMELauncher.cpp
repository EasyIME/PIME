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
#include <string>
#include <vector>
#include <map>
#include "../libpipe/libpipe.h"

using namespace std;

struct Backend {
	Backend():process(INVALID_HANDLE_VALUE) {
	}
	string name;
	string pipeName;
	wstring command;
	wstring param;
	wstring workingDir;
	HANDLE process;
};

static wchar_t top_dir_path[MAX_PATH];
static bool quit = false;
static map<string, Backend*> profile_to_backend;

static CRITICAL_SECTION server_lock;

static Backend backends[2];

static string getPipeName(const char* base_name) {
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
static bool initBackends() {
	// get the PIME directory
	DWORD len = GetModuleFileNameW(NULL, top_dir_path, MAX_PATH);
	top_dir_path[len] = '\0';
	wchar_t* p = wcsrchr(top_dir_path, '\\');
	if (!p)
		return false;
	*p = '\0';

	// the python backend
	Backend& backend = backends[0];
	backend.name = "python";
	backend.pipeName = getPipeName("python");

	backend.command = top_dir_path;
	backend.command += L"\\python\\python.exe";

	backend.workingDir = top_dir_path;
	backend.workingDir += L"\\server";

	backend.param = L"\"" + backend.workingDir + L"\\server.py\"";

	// TODO: node.js backend
	Backend& backend2 = backends[1];
	backend2.name = "node";
	backend2.pipeName = getPipeName("node");
	return true;
}

// initialize language profiles
static bool initProfiles() {
	// FIXME: load from files
	profile_to_backend["{F80736AA-28DB-423A-92C9-5540F501C939}"] = &backends[0];
	profile_to_backend["{F828D2DC-81BE-466E-9CFE-24BB03172693}"] = &backends[0];
	return true;
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
	DWORD err= GetLastError();
	return process;
}

static void parseCommandLine(LPSTR cmd) {
	int argc;
	wchar_t** argv = CommandLineToArgvW(GetCommandLine(), &argc);
	// parse command line options
	for (int i = 1; i < argc; ++i) {
		const wchar_t* arg = argv[i];
		if (wcscmp(arg, L"/quit") == 0)
			quit = true;
	}
	LocalFree(argv);
}

static void terminateExistingLauncher() {
	// TODO
}

static bool pingBackend(const string& pipe_name) {
	// make sure the backend server is running
	char buf[16];
	DWORD rlen;
	bool success = ::CallNamedPipeA(pipe_name.c_str(), "ping", 4, buf, sizeof(buf) - 1, &rlen, 1000); // wait for 1 sec.
	if (success) {
	}
	return success;
}

static string handleMessage(const string& msg) {
	string reply;
	if (msg == "quit") { // quit PIME
		// try to terminate launched backend server processes

		ExitProcess(0); // quit PIMELauncher
	}
	else { // query for the backend pipe address of the language profile GUID
		// msg is a language profile GUID
		auto it = profile_to_backend.find(msg);
		if (it != profile_to_backend.end()) { // found a backend
			Backend* backend = it->second;
			reply = backend->pipeName;  // reply with the pipe name of the backend server
			// ensure that the backend server is running...
			if(!pingBackend(backend->pipeName)) {
				// launch the backend server process
				backend->process = launchProcess(backend->command.c_str(), backend->param.c_str(), backend->workingDir.c_str());
			}
		}
	}
	return reply;
}

// called from a worker thread to read the incoming data from the connected pipe
static DWORD WINAPI clientPipeThread(LPVOID param) {
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
		::EnterCriticalSection(&server_lock); // acquire mutex
		// only handle message from one pipe thread at a time
		string reply = handleMessage(msg);
		if (!reply.empty()) {
			write_pipe(client_pipe, reply.c_str(), reply.length(), &err);
		}
		::LeaveCriticalSection(&server_lock); // release mutex
		running = false; // Currently, we only handle one message.
	}
	// notify the server that we're done. (maybe using PostThreadMessage? or event?)
}


int WINAPI WinMain(HINSTANCE hinst, HINSTANCE hprev, LPSTR cmd, int show) {
	parseCommandLine(cmd);
	if (quit) { // terminate existing launcher process
		terminateExistingLauncher();
		return 0;
	}

	// this is the first instance
	if (!initBackends())
		return 1;
	if (!initProfiles())
		return 1;

	// main server loop
	::InitializeCriticalSection(&server_lock);
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
