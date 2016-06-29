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
#include <cstring>
#include <string>
#include "../libpipe/libpipe.h"

using namespace std;

static const int MAX_CRASHES = 10;
static const int MAX_FAILURES = 10;
static const wchar_t wnd_class_name[] = L"PIME_Launcher";

static HWND server_hwnd = NULL;
static bool debug_mode = false;
static int n_failures = 0;
static int n_crashes = 0;
static wchar_t dir_path[MAX_PATH];
static wchar_t python_path[MAX_PATH];
static wchar_t server_path[MAX_PATH + 3];
static HANDLE server_process = INVALID_HANDLE_VALUE;
static bool pending_restart = false;


static LRESULT CALLBACK wndProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp);

static HWND createWindow(HINSTANCE hinst) {
	HWND hwnd = NULL;
	WNDCLASS wc = {0};
	if (!GetClassInfo(hinst, wnd_class_name, &wc)) {
		wc.hInstance = hinst;
		wc.lpfnWndProc = wndProc;
		wc.lpszClassName = wnd_class_name;
		RegisterClass(&wc);
	}
	hwnd = CreateWindow(wnd_class_name, NULL, 0, 0, 0, 0, 0, HWND_DESKTOP, NULL, hinst, NULL);
	return hwnd;
}

static bool initPaths() {
	DWORD len = GetModuleFileNameW(NULL, dir_path, MAX_PATH);
	dir_path[len] = '\0';
	wchar_t* p = wcsrchr(dir_path, '\\');
	if (!p)
		return false;
	*p = '\0';

	// when debugging, we use the console version of python
	wcscpy(python_path, dir_path);
	wcscat(python_path, debug_mode ? L"\\python\\python.exe" : L"\\python\\pythonw.exe");
	// build the full path of the server directory
	wcscat(dir_path, L"\\server");

	// build the full path of the server.py file and make it quoted
	wsprintf(server_path, L"\"%s\\server.py\"", dir_path);

	return true;
}

static HANDLE launchProcess(wchar_t* file, wchar_t* params, wchar_t* workingDir) {
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
	return process;
}

static void scheduleRestartServer() {
	if (!pending_restart) {
		SetTimer(server_hwnd, 1, 3000, NULL);
		pending_restart = true;
	}
}

static void launchServer() {
	server_process = launchProcess(python_path, server_path, dir_path);
	if (server_process == INVALID_HANDLE_VALUE) {
		++n_failures;
		if (n_failures > MAX_FAILURES) { // fail too many times
			ExitProcess(1); // quit the launcher
		}
		else {
			scheduleRestartServer();
		}
	}
}


int WINAPI WinMain(HINSTANCE hinst, HINSTANCE hprev, LPSTR cmd, int show) {
	bool quit = false;
	int argc;
	wchar_t** argv = CommandLineToArgvW(GetCommandLine(), &argc);
	// parse command line options
	for (int i = 1; i < argc; ++i) {
		const wchar_t* arg = argv[i];
		if (wcscmp(arg, L"/debug") == 0)
			debug_mode = true;
		else if (wcscmp(arg, L"/quit") == 0)
			quit = true;
	}
	LocalFree(argv);

	HANDLE h = connect_pipe("TEST");

	// we only allow running one instance of PIMELauncher
	server_hwnd = FindWindow(wnd_class_name, NULL); // find existing instance
	if (server_hwnd) {
		if (quit) { // ask the existing instance to terminate by closing its window
			DWORD pid;
			HANDLE process = INVALID_HANDLE_VALUE;
			if (GetWindowThreadProcessId(server_hwnd, &pid)) {
				process = OpenProcess(SYNCHRONIZE, FALSE, pid);
			}
			PostMessage(server_hwnd, WM_CLOSE, 0, 0); // post a request to close the window
			if (process != INVALID_HANDLE_VALUE) {
				WaitForSingleObject(process, 10000); // wait for the existing instance to terminate
				CloseHandle(process);
			}
		}
		return 0; // only one instance of PIME launcher is allowed
	}
	else if (quit) {
		// ask for existing instance to quit, but we cannot find an existing instance.
		return 0;
	}

	// this is the first instance
	if (!initPaths())
		return 1;

	server_hwnd = createWindow(hinst); // create the server window
	launchServer(); // try to launch the server process

	// monitor the server process and launch it again on crashes
	for (;;) {
		int n_handles = 0;
		DWORD event = WAIT_OBJECT_0;
		if (server_process != INVALID_HANDLE_VALUE) {
			// NOTE:
			// https://github.com/EasyIME/PIME/issues/67
			// The use of MsgWaitForMultipleObjects() here makes Excel startup very slow for unknown reasons.
			// This happens when QS_ALLEVENTS is passed to the wait function, or when NULL is passed to
			// GetMessage() to retrieve all messages from all windows (from this thread).
			// Clearly Excel is waiting for some event handled by our process, which should not happen if Windows
			// kernel is designed correctly. So, I think it's a bug of either MsgWaitForMultipleObjects() or in Excel.
			// Either limiting the types of messages to wait for or only GetMessage() on our server window can solve this.
			n_handles = 1;
			event = MsgWaitForMultipleObjects(n_handles, &server_process, FALSE, INFINITE, QS_TIMER|QS_SENDMESSAGE|QS_POSTMESSAGE);
		}
		if (event == (WAIT_OBJECT_0 + n_handles)) { // got window messages
			MSG msg;
			if (GetMessage(&msg, server_hwnd, 0, 0)) {
				TranslateMessage(&msg);
				DispatchMessage(&msg);
			}
			else { // no more messages
				break;
			}
		}
		else if (event == (WAIT_OBJECT_0 + n_handles - 1)) { // the process is terminated
			// check the exit status of the server
			DWORD exit_code;
			GetExitCodeProcess(server_process, &exit_code);
			CloseHandle(server_process);
			server_process = INVALID_HANDLE_VALUE;
			if (exit_code != 0) { // the server crashes
				++n_crashes; 
				if (n_crashes > MAX_CRASHES) // crash too many times, stop watching and quit
					return 1;
				scheduleRestartServer(); // schedule a timer to launch it again
			}
		}
	}
	return 0;
}

static void terminateServerProcess() {
	if (server_process != INVALID_HANDLE_VALUE) {
		// Try a safer way to terminate the process
		// This is done by calling ExitProcess() in the server process
		// via CreateRemoteThread() dirty hack.
		// Reference: http://www.drdobbs.com/a-safer-alternative-to-terminateprocess/184416547
		// ExitProcess() is loaded at the same address in every process so we can do this.
		// Also, ExitProcess() happens to have the same signature as a thread start routine.
		// This is quite tricky!!
		CreateRemoteThread(server_process, NULL, 0, (LPTHREAD_START_ROUTINE)ExitProcess, NULL, 0, NULL);
		DWORD ret = WaitForSingleObject(server_process, 30 * 1000);
		if (ret != WAIT_OBJECT_0) {
			// if the safe and cleaner method fails, try the brute force one
			TerminateProcess(server_process, 0);
			// wait for the server process to terminate
			WaitForSingleObject(server_process, 30 * 1000);
		}
		CloseHandle(server_process);
		server_process = INVALID_HANDLE_VALUE;
	}
}

static LRESULT CALLBACK wndProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
	switch (msg) {
	case WM_TIMER:
		// try to restart the server
		KillTimer(server_hwnd, 1);
		pending_restart = false;
		launchServer();
		break;
	case WM_DESTROY:
		// kill the server process and then quit
		terminateServerProcess();
		PostQuitMessage(0);
		break;
	default:
		break;
	}
	return DefWindowProc(hwnd, msg, wp, lp);
}
