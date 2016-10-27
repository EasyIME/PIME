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
#include "../libpipe/libpipe.h"
#include "BackendServer.h"

BackendServer::~BackendServer() {
	terminate();
}


void BackendServer::start() {
	if(process_ == INVALID_HANDLE_VALUE) {
		// Use I/O redirection to control the stdio of the child process
		// Reference: https://msdn.microsoft.com/zh-tw/library/windows/desktop/ms682499(v=vs.85).aspx

		// set up the pipe handles for the stdio of the child process.
		SECURITY_ATTRIBUTES sa;
		sa.nLength = sizeof(sa);
		sa.bInheritHandle = TRUE;
		sa.lpSecurityDescriptor = NULL;

		// create a pipe for the child stdout
		HANDLE childStdoutR = INVALID_HANDLE_VALUE;
		HANDLE childStdoutW = INVALID_HANDLE_VALUE;
		bool pipesCreated = CreatePipe(&childStdoutR, &childStdoutW, &sa, 0);

		// our read end of the pipe should not be inherited by the child
		if(pipesCreated)
			pipesCreated = SetHandleInformation(childStdoutR, HANDLE_FLAG_INHERIT, 0);

		// create a pipe for the child stdin
		HANDLE childStdinR = INVALID_HANDLE_VALUE;
		HANDLE childStdinW = INVALID_HANDLE_VALUE;
		if (pipesCreated)
			pipesCreated = CreatePipe(&childStdinR, &childStdinW, &sa, 0);

		// our write end of the pipe should not be inherited by the child
		if(pipesCreated)
			pipesCreated = SetHandleInformation(childStdinW, HANDLE_FLAG_INHERIT, 0);

		if (pipesCreated) { // pipes are correctly created
			// create the child process
			PROCESS_INFORMATION pi;
			memset(&pi, 0, sizeof(pi));

			STARTUPINFO si;
			memset(&si, 0, sizeof(si));
			si.cb = sizeof(si);
			si.hStdInput = childStdinR;
			si.hStdOutput = childStdoutW;
			si.hStdError = childStdoutW;  // FIXME: use a different fd from stdout
			si.wShowWindow = SW_HIDE;
			si.dwFlags = STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;

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

		CloseHandle(childStdinR);
		CloseHandle(childStdoutW);
		if (process_ != INVALID_HANDLE_VALUE) { // process created
			stdin_ = childStdinW;
			stdout_ = childStdoutR;
		}
		else {  // process creation fails
			CloseHandle(childStdinW);
			CloseHandle(childStdoutR);
		}
	}
}

void BackendServer::terminate() {
	if (isRunning()) {
		char buf[16];
		DWORD rlen;
		if (!::CallNamedPipeA(pipeName_.c_str(), "quit", 4, buf, sizeof(buf) - 1, &rlen, 1000)) { // wait for 1 sec.
			// the RPC call fails, force termination
			::TerminateProcess(process_, 0);
		}
		::WaitForSingleObject(process_, 3000); // wait for 3 seconds
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
	// make sure the backend server is running
	char buf[16];
	DWORD rlen;
	bool success = ::CallNamedPipeA(pipeName_.c_str(), "ping", 4, buf, sizeof(buf) - 1, &rlen, timeout);
	if (success) {
	}
	return success;
}

