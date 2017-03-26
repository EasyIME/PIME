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

#include <windows.h>
#include <tchar.h>
#include "PipeServer.h"

static wchar_t g_serviceName[] = L"PIMELauncher";
static SERVICE_STATUS g_serviceStatus = {0};
static SERVICE_STATUS_HANDLE g_statusHandle = NULL;
// HANDLE g_serviceStopEvent = INVALID_HANDLE_VALUE;


// Reference: https://msdn.microsoft.com/en-us/library/ms687414(v=vs.85).aspx
//            https://msdn.microsoft.com/en-us/library/ms681921(VS.85).aspx
static void reportServiceStatus(DWORD dwCurrentState, DWORD dwWin32ExitCode, DWORD dwWaitHint) {
	static DWORD dwCheckPoint = 1;
	// Fill in the SERVICE_STATUS structure.
	g_serviceStatus.dwCurrentState = dwCurrentState;
	g_serviceStatus.dwWin32ExitCode = dwWin32ExitCode;
	g_serviceStatus.dwWaitHint = dwWaitHint;

	if (dwCurrentState == SERVICE_START_PENDING) {
		g_serviceStatus.dwControlsAccepted = 0;
	}
	else {
		g_serviceStatus.dwControlsAccepted = SERVICE_ACCEPT_STOP;
	}

	if ((dwCurrentState == SERVICE_RUNNING) || (dwCurrentState == SERVICE_STOPPED)) {
		g_serviceStatus.dwCheckPoint = 0;
	}
	else {
		g_serviceStatus.dwCheckPoint = dwCheckPoint++;
	}
	// Report the status of the service to the SCM.
	SetServiceStatus(g_statusHandle, &g_serviceStatus);
}


static void WINAPI serviceCtrlHandler(DWORD dwCtrl) {
	// Handle the requested control code. 
	switch (dwCtrl) {
	case SERVICE_CONTROL_STOP:  // we're asked to stop our service
		reportServiceStatus(SERVICE_STOP_PENDING, NO_ERROR, 0);

		// FIXME: Signal the service to stop.

		reportServiceStatus(g_serviceStatus.dwCurrentState, NO_ERROR, 0);
		return;
	default:
		break;
	}
}


static void WINAPI serviceMain(DWORD argc, LPTSTR *argv) {

	// Register our service control handler with the SCM
	g_statusHandle = RegisterServiceCtrlHandler(g_serviceName, serviceCtrlHandler);
	if (!g_statusHandle) {
		return;
	}

	// These SERVICE_STATUS members remain as set here
	g_serviceStatus.dwServiceType = SERVICE_WIN32_OWN_PROCESS;
	g_serviceStatus.dwServiceSpecificExitCode = 0;

	// Report initial status to the SCM
	reportServiceStatus(SERVICE_START_PENDING, NO_ERROR, 3000);

	// Initialize the service
	PIME::PipeServer server;

	// Run the service
	reportServiceStatus(SERVICE_RUNNING, NO_ERROR, 0);
	server.exec();

	// stopped
	reportServiceStatus(SERVICE_STOPPED, NO_ERROR, 0);
}


int main(int argc, char** argv) {
	// Disable all Windows error reporting message boxes since
	// this will block user input. We want to handle the errors silently.
	::SetErrorMode(SEM_NOOPENFILEERRORBOX|SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX|SEM_NOALIGNMENTFAULTEXCEPT);

	// intialize windows service
	SERVICE_TABLE_ENTRY serviceTable[] = {
		{g_serviceName, (LPSERVICE_MAIN_FUNCTION)serviceMain},
		{nullptr, nullptr}
	};
	if (StartServiceCtrlDispatcher(serviceTable) == FALSE) {
		return GetLastError();
	}
	return 0;
}
