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

#ifndef __STDUTILS_H__
#define __STDUTILS_H__

#define WIN32_LEAN_AND_MEAN 1
#include <Windows.h>
#include <Shellapi.h>
#include "nsis/pluginapi.h"
#include "msvc_utils.h"

#define NSISFUNC(name) extern "C" void __declspec(dllexport) name(HWND hWndParent, int string_size, TCHAR* variables, stack_t** stacktop, extra_parameters* extra)

#define MAKESTR(VAR,LEN) \
	TCHAR *VAR = new TCHAR[LEN]; \
	memset(VAR, 0, sizeof(TCHAR) * LEN)

#define REGSITER_CALLBACK(INST) do \
{ \
	if(!g_bCallbackRegistred) g_bCallbackRegistred = (extra->RegisterPluginCallback((HMODULE)(INST), PluginCallback) == 0); \
} \
while(0)

#endif //__STDUTILS_H__
