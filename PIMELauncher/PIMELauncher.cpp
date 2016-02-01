//
//	Copyright (C) 2015 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
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
#include <cstring>
#include <string>

using namespace std;

static const int MAX_CRASHES = 10;
static const int MAX_FAILURES = 10;

int WINAPI WinMain(HINSTANCE hinst, HINSTANCE hprev, LPSTR cmd, int show) {
	// FIXME: we should only allow running one instance of PIMELauncher
	bool debug = false;
	if (cmd && strstr(cmd, "/debug"))
		debug = true;

	int n_failures = 0;
	int n_crashes = 0;
	wchar_t dir_path[MAX_PATH];
	DWORD len = GetModuleFileNameW(NULL, dir_path, MAX_PATH);
	dir_path[len] = '\0';
	wchar_t* p = wcsrchr(dir_path, '\\');
	if (!p)
		return 1;
	*p = '\0';

	// when debugging, we use the console version of python
	wchar_t python_path[MAX_PATH];
	wcscpy(python_path, dir_path);
	wcscat(python_path, debug ? L"\\python\\python.exe" : L"\\python\\pythonw.exe");
	// build the full path of the server directory
	wcscat(dir_path, L"\\server");

	// build the full path of the server.py file and make it quoted
	wchar_t server_path[MAX_PATH + 3];
	wsprintf(server_path, L"\"%s\\server.py\"", dir_path);

	// launch the python server again if it crashes
	for (;;) {
		SHELLEXECUTEINFOW info = { 0 };
		info.cbSize = sizeof(info);
		info.fMask = SEE_MASK_NOCLOSEPROCESS;
		info.lpVerb = L"open";
		info.lpFile = python_path;
		info.lpParameters = server_path;
		info.lpDirectory = dir_path;
		info.nShow = SW_SHOWNORMAL;

		if (ShellExecuteExW(&info)) {
			// wait for the python server process to terminate
			WaitForSingleObject(info.hProcess, INFINITE);
			DWORD code;
			GetExitCodeProcess(info.hProcess, &code);
			CloseHandle(info.hProcess);
			if (code != 0) {
				++n_crashes; // the server crashes
				Sleep(500); // sleep for 500 ms
				if (n_crashes > MAX_CRASHES) { // crash too many times
					return 1;
				}
			}
		}
		else { // launching the server failed
			MessageBox(0, L"Launching PIME server failed.", 0, 0);
			++n_failures;
			Sleep(500); // sleep for 500 ms
			if (n_failures > MAX_FAILURES) { // fail too many times
				return 1;
			}
		}
	}
	return 0;
}
