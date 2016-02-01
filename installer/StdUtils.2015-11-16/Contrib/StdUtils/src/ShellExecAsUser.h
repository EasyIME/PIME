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

#pragma once

#ifndef _WINDOWS_
#include <Windows.h>
#endif

typedef enum
{
	SHELL_EXEC_AS_USER_SUCCESS     = 0,
	SHELL_EXEC_AS_USER_FAILED      = 1,
	SHELL_EXEC_AS_USER_TIMEOUT     = 2,
	SHELL_EXEC_AS_USER_UNSUPPORTED = 3,
	SHELL_EXEC_AS_USER_NOT_FOUND   = 4,
	SHELL_EXEC_AS_USER_FALLBACK    = 5
}
shell_exec_as_user_err_t;

int ShellExecAsUser(const TCHAR *const pcOperation, const TCHAR *const pcFileName, const TCHAR *const pcParameters, const HWND &hwnd, const bool &threaded = true);
