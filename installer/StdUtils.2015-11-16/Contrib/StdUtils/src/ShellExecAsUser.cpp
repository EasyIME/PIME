///////////////////////////////////////////////////////////////////////////////
// StdUtils plug-in for NSIS
// Copyright (C) 2004-2015 LoRd_MuldeR <MuldeR2@GMX.de>
//
// This library is free software; you can redistribute it and/or
// modify it under the terms of the GNU Lesser General Public
// License as published by the Free Software Foundation; either
// version 2.1 of the License, or (at your option) any later version.
//
// This library is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// Lesser General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public
// License along with this library; if not, write to the Free Software
// Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
//
// http://www.gnu.org/licenses/lgpl-2.1.txt
///////////////////////////////////////////////////////////////////////////////

#include "ShellExecAsUser.h"
#include "ShellDispatch.h"

///////////////////////////////////////////////////////////////////////////////

typedef struct
{
	const HWND parentHwnd;
	const TCHAR *const pcOperation;
	const TCHAR *const pcFileName;
	const TCHAR *const pcParameters;
}
shell_exec_as_user_param_t;

///////////////////////////////////////////////////////////////////////////////

static int ShellExecAsUser_HandlerProc(IShellDispatch2 *const dispatch, const void *const data)
{
	int iSuccess = SHELL_EXEC_AS_USER_FAILED;
	const shell_exec_as_user_param_t *const param = (const shell_exec_as_user_param_t*) data;

	DispatchPendingMessages(125);

	variant_t vEmpty;
	variant_t verb(param->pcOperation);
	variant_t file(param->pcFileName);
	variant_t para(param->pcParameters);
	variant_t show(SW_SHOWNORMAL);

	HRESULT hr = dispatch->ShellExecute(file, para, vEmpty, verb, show);
	if(SUCCEEDED(hr))
	{
		iSuccess = SHELL_EXEC_AS_USER_SUCCESS;
	}

	return iSuccess;
}

int ShellExecAsUser(const TCHAR *const pcOperation, const TCHAR *const pcFileName, const TCHAR *const pcParameters, const HWND &parentHwnd, const bool &threaded)
{
	//Make sure the destination file exists
	if(!FILE_EXISTS(pcFileName))
	{
		return SHELL_EXEC_AS_USER_NOT_FOUND;
	}

	int iSuccess = SHELL_EXEC_AS_USER_FAILED;

	OSVERSIONINFO osVersion;
	memset(&osVersion, 0, sizeof(OSVERSIONINFO));
	osVersion.dwOSVersionInfoSize = sizeof(OSVERSIONINFO);

	//Use IShellDispatch2 on supported platforms
	if(GetVersionEx(&osVersion))
	{
		if((osVersion.dwPlatformId == VER_PLATFORM_WIN32_NT) && (osVersion.dwMajorVersion >= 6))
		{
			shell_exec_as_user_param_t params = { parentHwnd, pcOperation, pcFileName, pcParameters };
			iSuccess = MyShellDispatch(ShellExecAsUser_HandlerProc, &params, threaded);
		}
		else
		{
			iSuccess = SHELL_EXEC_AS_USER_UNSUPPORTED;
		}
	}

	//Fallback mode
	if((iSuccess == SHELL_EXEC_AS_USER_FAILED) || (iSuccess == SHELL_EXEC_AS_USER_UNSUPPORTED))
	{
		HINSTANCE hInst = ShellExecute(parentHwnd, pcOperation, pcFileName, pcParameters, NULL, SW_SHOWNORMAL);
		if(((int)hInst) > 32)
		{
			iSuccess = SHELL_EXEC_AS_USER_FALLBACK;
		}
	}

	return iSuccess;
}
