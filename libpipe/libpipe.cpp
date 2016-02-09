//
//	Copyright (C) 2016 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
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
#include <Lmcons.h> // for UNLEN
#include <Winnt.h> // for security attributes constants
#include <aclapi.h> // for ACL
#include <string>
#include <iostream>

using namespace std;

static PSECURITY_DESCRIPTOR g_securittyDescriptor = NULL;
static SECURITY_ATTRIBUTES g_securityAttributes = {0};
static PACL g_acl = NULL;
static EXPLICIT_ACCESS g_explicitAccesses[2] = {0};
static PSID g_logonSid = NULL;
static PSID g_allAppsSid = NULL;

extern "C" {

// get the Sid of the current logged on session
// Reference: https://msdn.microsoft.com/en-us/library/windows/desktop/hh448493%28v=vs.85%29.aspx
//            http://stackoverflow.com/questions/251248/how-can-i-get-the-sid-of-the-current-windows-account
static PSID getLogonSid() {
	PSID sid = nullptr;
	HANDLE token = nullptr;
	if (OpenProcessToken(GetCurrentProcess(), TOKEN_READ | TOKEN_QUERY, &token)) {
		DWORD len = 0;
		PTOKEN_GROUPS tokenGroups = nullptr;
		// get required buffer size
		if (GetTokenInformation(token, TokenLogonSid, nullptr, 0, &len)) {
			// allocate the buffer and get the data
			tokenGroups = (PTOKEN_GROUPS)malloc(len);
			if (tokenGroups != nullptr) {
				if (GetTokenInformation(token, TokenLogonSid, (LPVOID)tokenGroups, 0, &len)) {
					// Found the logon SID; make a copy of it.
					len = GetLengthSid(tokenGroups->Groups[0].Sid);
					sid = (PSID)malloc(len);
					if (sid != nullptr) {
						memset(sid, 0, len);
						if (!CopySid(len, sid, tokenGroups->Groups[0].Sid)) {
							free(sid);
							sid = nullptr;
						}
					}
				}
				free(tokenGroups);
			}
		}
		CloseHandle(token);
	}
	return sid;
}

static void inline freeLogonSid(PSID sid) {
	free(sid);
}

static void init() {
	// create security attributes for the pipe
	// http://msdn.microsoft.com/en-us/library/windows/desktop/hh448449(v=vs.85).aspx
	// define new Win 8 app related constants
	memset(&g_explicitAccesses, 0, sizeof(g_explicitAccesses));
	// Create SID for the current logon session
	// See this article for details: https://msdn.microsoft.com/en-us/library/windows/desktop/hh448493(v=vs.85).aspx
	// https://services.land.vic.gov.au/ArcGIS10.1/edESRIArcGIS10_01_01_3143/Python/pywin32/PLATLIB/win32/Demos/security/explicit_entries.py
	g_logonSid = getLogonSid();
	g_explicitAccesses[0].grfAccessPermissions = GENERIC_ALL;
	g_explicitAccesses[0].grfAccessMode = SET_ACCESS;
	g_explicitAccesses[0].grfInheritance = NO_INHERITANCE;
	g_explicitAccesses[0].Trustee.pMultipleTrustee = NULL;
	g_explicitAccesses[0].Trustee.MultipleTrusteeOperation = NO_MULTIPLE_TRUSTEE;
	g_explicitAccesses[0].Trustee.TrusteeForm = TRUSTEE_IS_SID;
	g_explicitAccesses[0].Trustee.TrusteeType = TRUSTEE_IS_USER;
	g_explicitAccesses[0].Trustee.ptstrName = (LPTSTR)g_logonSid;

	// FIXME: will this work under Windows 7 and Vista?
	// create SID for app containers
	SID_IDENTIFIER_AUTHORITY appPackageAuthority = SECURITY_APP_PACKAGE_AUTHORITY;
	AllocateAndInitializeSid(&appPackageAuthority,
		SECURITY_BUILTIN_APP_PACKAGE_RID_COUNT,
		SECURITY_APP_PACKAGE_BASE_RID,
		SECURITY_BUILTIN_PACKAGE_ANY_PACKAGE,
		0, 0, 0, 0, 0, 0, &g_allAppsSid);

	g_explicitAccesses[1].grfAccessPermissions = GENERIC_ALL;
	g_explicitAccesses[1].grfAccessMode = SET_ACCESS;
	g_explicitAccesses[1].grfInheritance = SUB_CONTAINERS_AND_OBJECTS_INHERIT;
	g_explicitAccesses[1].Trustee.pMultipleTrustee = NULL;
	g_explicitAccesses[1].Trustee.MultipleTrusteeOperation = NO_MULTIPLE_TRUSTEE;
	g_explicitAccesses[1].Trustee.TrusteeForm = TRUSTEE_IS_SID;
	g_explicitAccesses[1].Trustee.TrusteeType = TRUSTEE_IS_GROUP;
	g_explicitAccesses[1].Trustee.ptstrName = (LPTSTR)g_allAppsSid;

	// create DACL
	DWORD err = SetEntriesInAcl(2, g_explicitAccesses, NULL, &g_acl);
	if (0 == err) {
		// security descriptor
		g_securittyDescriptor = (PSECURITY_DESCRIPTOR)LocalAlloc(LPTR, SECURITY_DESCRIPTOR_MIN_LENGTH);
		InitializeSecurityDescriptor(g_securittyDescriptor, SECURITY_DESCRIPTOR_REVISION);

		// Add the ACL to the security descriptor. 
		SetSecurityDescriptorDacl(g_securittyDescriptor, TRUE, g_acl, FALSE);
	}

	g_securityAttributes.nLength = sizeof(SECURITY_ATTRIBUTES);
	g_securityAttributes.lpSecurityDescriptor = g_securittyDescriptor;
	g_securityAttributes.bInheritHandle = TRUE;
}

static void cleanup() {
	if(g_logonSid != nullptr)
		freeLogonSid(g_logonSid);
	if (g_allAppsSid != nullptr)
		FreeSid(g_allAppsSid);
	if (g_securittyDescriptor != nullptr)
		LocalFree(g_securittyDescriptor);
	if (g_acl != nullptr)
		LocalFree(g_acl);
}

// References:
// https://msdn.microsoft.com/en-us/library/windows/desktop/aa365588(v=vs.85).aspx
HANDLE connect_pipe(const char* app_name) {
	HANDLE pipe = INVALID_HANDLE_VALUE;
	char username[UNLEN + 1];
	DWORD unlen = UNLEN + 1;
	if (GetUserNameA(username, &unlen)) {
		// add username to the pipe path so it will not clash with other users' pipes.
		char pipe_name[MAX_PATH];
		sprintf(pipe_name, "\\\\.\\pipe\\%s\\%s_pipe", username, app_name);
		const size_t buffer_size = 1024;
		// create the pipe
		pipe = CreateNamedPipeA(pipe_name,
			PIPE_ACCESS_DUPLEX,
			PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE | PIPE_WAIT,
			PIPE_UNLIMITED_INSTANCES,
			buffer_size,
			buffer_size,
			NMPWAIT_USE_DEFAULT_WAIT,
			&g_securityAttributes);

		if (pipe != INVALID_HANDLE_VALUE) {
			// try to connect to the named pipe
			// NOTE: this is a blocking call
			if (FALSE == ConnectNamedPipe(pipe, NULL)) {
				// fail to connect the pipe
				CloseHandle(pipe);
				pipe = INVALID_HANDLE_VALUE;
			}
		}
	}
	return pipe;
}

void close_pipe(HANDLE pipe) {
	FlushFileBuffers(pipe);
	DisconnectNamedPipe(pipe);
	CloseHandle(pipe);
}

int read_pipe(HANDLE pipe, char* buf, unsigned long len, unsigned long* error) {
	DWORD read_len = 0;
	BOOL success = ReadFile(pipe, buf, len, &read_len, NULL);
	if (error != nullptr)
		*error = success ? 0 : (unsigned long)GetLastError();
	return (int)read_len;
}

int write_pipe(HANDLE pipe, const char* data, unsigned long len, unsigned long* error) {
	DWORD write_len = 0;
	BOOL success = WriteFile(pipe, data, len, &write_len, NULL);
	if (error != nullptr)
		*error = success ? 0 : (unsigned long)GetLastError();
	return (int)write_len;
}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD  ul_reason_for_call, LPVOID lpReserved) {
	switch (ul_reason_for_call) {
	case DLL_PROCESS_ATTACH:
		::DisableThreadLibraryCalls(hModule); // disable DllMain calls due to new thread creation
		init();
		break;
	case DLL_PROCESS_DETACH:
		cleanup();
		break;
	}
	return TRUE;
}


} // extern "C"
