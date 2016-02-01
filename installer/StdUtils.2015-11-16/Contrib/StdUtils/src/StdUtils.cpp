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

#include "StdUtils.h"
#include "ShellExecAsUser.h"
#include "ParameterParser.h"
#include "InvokeShellVerb.h"
#include "UnicodeSupport.h"
#include "DetectOsVersion.h"
#include "WinUtils.h"
#include "FileUtils.h"
#include "HashUtils.h"
#include "TimerUtils.h"
#include "CleanUp.h"

//External
bool g_bStdUtilsVerbose = false;
RTL_CRITICAL_SECTION g_pStdUtilsMutex;
HINSTANCE g_StdUtilsInstance = NULL;

//Global
static volatile bool g_bCallbackRegistred = false;

///////////////////////////////////////////////////////////////////////////////
// DLL MAIN
///////////////////////////////////////////////////////////////////////////////

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved)
{
	if(fdwReason == DLL_PROCESS_ATTACH)
	{
		InitializeCriticalSection(&g_pStdUtilsMutex);
		g_bCallbackRegistred = false;
		g_bStdUtilsVerbose = false;
		g_StdUtilsInstance = hinstDLL;
	}
	else if(fdwReason == DLL_PROCESS_DETACH)
	{
		cleanup_execute_tasks();
		DeleteCriticalSection(&g_pStdUtilsMutex);
	}
	return TRUE;
}

static UINT_PTR PluginCallback(enum NSPIM msg)
{
	switch(msg)
	{
	case NSPIM_UNLOAD:
	case NSPIM_GUIUNLOAD:
		break;
	default:
		OutputDebugStringA("StdUtils: Unknown callback message. Take care!\n");
		break;
	}

	return 0;
}

///////////////////////////////////////////////////////////////////////////////
// TIME UTILS
///////////////////////////////////////////////////////////////////////////////

static const unsigned __int64 FTIME_SECOND = 10000000ui64;
static const unsigned __int64 FTIME_MINUTE = 60ui64 * FTIME_SECOND;
static const unsigned __int64 FTIME_HOUR   = 60ui64 * FTIME_MINUTE;
static const unsigned __int64 FTIME_DAY    = 24ui64 * FTIME_HOUR;

static unsigned __int64 getFileTime(void)
{
	SYSTEMTIME systime;
	GetSystemTime(&systime);
	
	FILETIME filetime;
	if(!SystemTimeToFileTime(&systime, &filetime))
	{
		return 0;
	}

	ULARGE_INTEGER uli;
	uli.LowPart = filetime.dwLowDateTime;
	uli.HighPart = filetime.dwHighDateTime;

	return uli.QuadPart;
}

NSISFUNC(Time)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	long t = time(NULL);
	pushint(t);
}

NSISFUNC(GetMinutes)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	unsigned __int64 ftime = getFileTime() / FTIME_MINUTE;
	pushint(static_cast<int>(ftime));
}

NSISFUNC(GetHours)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	unsigned __int64 ftime = getFileTime() / FTIME_HOUR;
	pushint(static_cast<int>(ftime));
}

NSISFUNC(GetDays)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	unsigned __int64 ftime = getFileTime() / FTIME_DAY;
	pushint(static_cast<int>(ftime));
}

///////////////////////////////////////////////////////////////////////////////
// PRNG FUNCTIONS
///////////////////////////////////////////////////////////////////////////////

#include "RandUtils.h"

NSISFUNC(Rand)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	unsigned int r = next_rand() % static_cast<unsigned int>(INT_MAX);
	pushint(r);
}

NSISFUNC(RandMax)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	int m = abs(popint()) + 1;
	unsigned int r = next_rand() % static_cast<unsigned int>(m);
	pushint(r);
}

NSISFUNC(RandMinMax)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	int max = popint();
	int min = popint();
	
	if(min > max)
	{
		MessageBoxW(NULL, L"RandMinMax() was called with bad arguments!", L"StdUtils::RandMinMax", MB_ICONERROR | MB_TASKMODAL);
		pushint(0);
	}

	int diff = abs(max - min) + 1;
	unsigned int r = next_rand() % static_cast<unsigned int>(diff);
	pushint(r + min);
}

NSISFUNC(RandList)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	int count = popint();
	int max = popint() + 1;
	int done = 0;

	if(count > max)
	{
		if(g_bStdUtilsVerbose)
		{
			MessageBoxW(NULL, L"RandList() was called with bad arguments!", L"StdUtils::RandList", MB_ICONERROR | MB_TASKMODAL);
		}
		pushstring(T("EOL"));
		return;
	}

	bool *list = new bool[max];
	for(int idx = 0; idx < max; idx++)
	{
		list[idx] = false;
	}

	while(done < count)
	{
		unsigned int rnd = next_rand() % static_cast<unsigned int>(max);
		if(!list[rnd])
		{
			list[rnd] = true;
			done++;
		}
	}

	pushstring(T("EOL"));
	for(int idx = max-1; idx >= 0; idx--)
	{
		if(list[idx])
		{
			pushint(idx);
		}
	}
}

///////////////////////////////////////////////////////////////////////////////
// STRING FUNCTIONS
///////////////////////////////////////////////////////////////////////////////

NSISFUNC(FormatStr)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(fmt, g_stringsize);
	MAKESTR(out, g_stringsize);

	int v = popint();
	popstringn(fmt, 0);

	if(SNPRINTF(out, g_stringsize, fmt, v) < 0)
	{
		out[g_stringsize-1] = T('\0');
	}

	pushstring(out);
	delete [] fmt;
	delete [] out;
}

NSISFUNC(FormatStr2)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(fmt, g_stringsize);
	MAKESTR(out, g_stringsize);

	int v2 = popint();
	int v1 = popint();
	popstringn(fmt, 0);

	if(SNPRINTF(out, g_stringsize, fmt, v1, v2) < 0)
	{
		out[g_stringsize-1] = T('\0');
	}

	pushstring(out);
	delete [] fmt;
	delete [] out;
}

NSISFUNC(FormatStr3)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(fmt, g_stringsize);
	MAKESTR(out, g_stringsize);

	int v3 = popint();
	int v2 = popint();
	int v1 = popint();
	popstringn(fmt, 0);

	if(SNPRINTF(out, g_stringsize, fmt, v1, v2, v3) < 0)
	{
		out[g_stringsize-1] = T('\0');
	}

	pushstring(out);
	delete [] fmt;
	delete [] out;
}

///////////////////////////////////////////////////////////////////////////////

NSISFUNC(ScanStr)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(in, g_stringsize);
	MAKESTR(fmt, g_stringsize);

	int def = popint();
	popstringn(in, 0);
	popstringn(fmt, 0);
	int out = 0;

	if(SSCANF(in, fmt, &out) != 1)
	{
		out = def;
	}

	pushint(out);
	delete [] fmt;
	delete [] in;
}

NSISFUNC(ScanStr2)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(in, g_stringsize);
	MAKESTR(fmt, g_stringsize);

	int def2 = popint();
	int def1 = popint();
	popstringn(in, 0);
	popstringn(fmt, 0);
	int out1 = 0;
	int out2 = 0;
	int result = 0;

	result = SSCANF(in, fmt, &out1, &out2);
	
	if(result != 2)
	{
		if(result != 1)
		{
			out1 = def1;
		}
		out2 = def2;
	}

	pushint(out2);
	pushint(out1);
	delete [] fmt;
	delete [] in;
}

NSISFUNC(ScanStr3)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(in, g_stringsize);
	MAKESTR(fmt, g_stringsize);

	int def3 = popint();
	int def2 = popint();
	int def1 = popint();
	popstringn(in, 0);
	popstringn(fmt, 0);
	int out1 = 0;
	int out2 = 0;
	int out3 = 0;
	int result = 0;

	result = SSCANF(in, fmt, &out1, &out2, &out3);
	
	if(result != 3)
	{
		if(result == 0)
		{
			out1 = def1;
			out2 = def2;
		}
		else if(result == 1)
		{
			out2 = def2;
		}
		out3 = def3;
	}

	pushint(out3);
	pushint(out2);
	pushint(out1);
	delete [] fmt;
	delete [] in;
}

///////////////////////////////////////////////////////////////////////////////

NSISFUNC(TrimStr)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(str, g_stringsize);
	
	popstringn(str, 0);
	pushstring(STRTRIM(str));

	delete [] str;
}

NSISFUNC(TrimStrLeft)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(str, g_stringsize);
	
	popstringn(str, 0);
	pushstring(STRTRIM_LEFT(str));

	delete [] str;
}

NSISFUNC(TrimStrRight)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(str, g_stringsize);
	
	popstringn(str, 0);
	pushstring(STRTRIM_RIGHT(str));

	delete [] str;
}

///////////////////////////////////////////////////////////////////////////////

NSISFUNC(RevStr)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(str, g_stringsize);
	
	popstringn(str, 0);

	if(str[0] != T('\0'))
	{
		size_t left = 0;
		size_t right = STRLEN(str) - 1;
		while(left < right)
		{
			TCHAR tmp = str[left];
			str[left++] = str[right];
			str[right--] = tmp;
		}
	}

	pushstring(str);
	delete [] str;
}

///////////////////////////////////////////////////////////////////////////////

NSISFUNC(ValidFileName)
{
	static const TCHAR *const RESERVED = T("<>:\"/\\|?*");

	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(str, g_stringsize);

	popstringn(str, 0);

	bool flag = true;
	TCHAR last = 0x0;

	if(!str[0])
	{
		flag = false;
		goto exit209;
	}

	for(size_t i = 0; str[i]; i++)
	{
		if(ISCNTRL(str[i]))
		{
			flag = false;
			goto exit209;
		}
		for(size_t j = 0; RESERVED[j]; j++)
		{
			if(str[i] == RESERVED[j])
			{
				flag = false;
				goto exit209;
			}
		}
		last = str[i];
	}

	if((last == T(' ')) || (last == T('.')))
	{
		flag = false;
	}

exit209:
	pushstring(flag ? T("ok") : T("invalid"));
	delete [] str;
}

NSISFUNC(ValidPathSpec)
{
	static const TCHAR *const RESERVED = T("<>\"|?*");

	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(str, g_stringsize);

	popstringn(str, 0);

	bool flag = true;
	TCHAR last = 0x0;

	if(!str[0])
	{
		flag = false;
		goto exit209;
	}

	for(size_t i = 0; str[i]; i++)
	{
		if(ISCNTRL(str[i]))
		{
			flag = false;
			goto exit209;
		}
		for(size_t j = 0; RESERVED[j]; j++)
		{
			if(str[i] == RESERVED[j])
			{
				flag = false;
				goto exit209;
			}
		}
		if(((i == 0) && (!ISALPHA(str[i]))) || ((i == 1) && (str[i] != T(':'))) || ((i != 1) && (str[i] == T(':'))) || ((i == 2) && (str[i] != T('/')) && (str[i] != T('\\'))))
		{
			flag = false;
			goto exit209;
		}
		last = str[i];
	}

	if((last == T(' ')) || (last == T('.')))
	{
		flag = false;
	}

exit209:
	pushstring(flag ? T("ok") : T("invalid"));
	delete [] str;
}

///////////////////////////////////////////////////////////////////////////////
// SHELL FILE FUNCTIONS
///////////////////////////////////////////////////////////////////////////////

NSISFUNC(SHFileMove)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(from, g_stringsize);
	MAKESTR(dest, g_stringsize);

	SHFILEOPSTRUCT fileop;
	SecureZeroMemory(&fileop, sizeof(SHFILEOPSTRUCT));

	HWND hwnd = (HWND) popint();
	popstringn(dest, 0);
	popstringn(from, 0);

	fileop.hwnd = hwnd;
	fileop.wFunc = FO_MOVE;
	fileop.pFrom = from;
	fileop.pTo = dest;
	fileop.fFlags = FOF_NOCONFIRMATION | FOF_NOERRORUI | FOF_NOCONFIRMMKDIR;
	if(hwnd == 0) fileop.fFlags |= FOF_SILENT;

	int result = SHFileOperation(&fileop);
	pushstring((result == 0) ? (fileop.fAnyOperationsAborted ? T("ABORTED") : T("OK")) : T("ERROR"));

	if((result != 0) && g_bStdUtilsVerbose)
	{
		char temp[1024];
		_snprintf(temp, 1024, "Failed with error code: 0x%X", result);
		temp[1023] = '\0';
		MessageBoxA(NULL, temp, "StdUtils::SHFileMove", MB_TOPMOST|MB_ICONERROR);
	}

	delete [] from;
	delete [] dest;
}

NSISFUNC(SHFileCopy)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(from, g_stringsize);
	MAKESTR(dest, g_stringsize);

	SHFILEOPSTRUCT fileop;
	SecureZeroMemory(&fileop, sizeof(SHFILEOPSTRUCT));

	HWND hwnd = (HWND) popint();
	popstringn(dest, 0);
	popstringn(from, 0);

	fileop.hwnd = hwnd;
	fileop.wFunc = FO_COPY;
	fileop.pFrom = from;
	fileop.pTo = dest;
	fileop.fFlags = FOF_NOCONFIRMATION | FOF_NOERRORUI | FOF_NOCONFIRMMKDIR;
	if(hwnd == 0) fileop.fFlags |= FOF_SILENT;

	int result = SHFileOperation(&fileop);
	pushstring((result == 0) ? (fileop.fAnyOperationsAborted ? T("ABORTED") : T("OK")) : T("ERROR"));

	if((result != 0) && g_bStdUtilsVerbose)
	{
		char temp[1024];
		_snprintf(temp, 1024, "Failed with error code: 0x%X", result);
		temp[1023] = '\0';
		MessageBoxA(NULL, temp, "StdUtils::SHFileCopy", MB_TOPMOST|MB_ICONERROR);
	}

	delete [] from;
	delete [] dest;
}

///////////////////////////////////////////////////////////////////////////////
// APPEND TO FILE
///////////////////////////////////////////////////////////////////////////////

NSISFUNC(AppendToFile)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(from, g_stringsize);
	MAKESTR(dest, g_stringsize);

	const DWORD maxlen = static_cast<DWORD>(MAX_VAL(0, popint()));
	const DWORD offset = static_cast<DWORD>(MAX_VAL(0, popint()));
	popstringn(dest, 0);
	popstringn(from, 0);
	
	unsigned long long bytesCopied = 0;
	if(AppendToFile(from, dest, offset, maxlen, &bytesCopied))
	{
		pushint(static_cast<int>(MIN_VAL(bytesCopied, static_cast<unsigned long long>(INT_MAX))));
	}
	else
	{
		pushstring(T("error"));
	}

	delete [] from;
	delete [] dest;
}

///////////////////////////////////////////////////////////////////////////////
// EXEC SHELL AS USER
///////////////////////////////////////////////////////////////////////////////

NSISFUNC(ExecShellAsUser)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(file, g_stringsize);
	MAKESTR(verb, g_stringsize);
	MAKESTR(args, g_stringsize);

	popstringn(args, 0);
	popstringn(verb, 0);
	popstringn(file, 0);
	
	if(_tcslen(file) < 1) { delete [] file; file = NULL; }
	if(_tcslen(verb) < 1) { delete [] verb; verb = NULL; }
	if(_tcslen(args) < 1) { delete [] args; args = NULL; }

	if(!(file))
	{
		pushstring(T("einval"));
		if(file) delete [] file;
		if(verb) delete [] verb;
		if(args) delete [] args;
		return;
	}

	int result = ShellExecAsUser(verb, file, args, hWndParent, true);
	
	switch(result)
	{
	case SHELL_EXEC_AS_USER_SUCCESS:
		pushstring(T("ok"));
		break;
	case SHELL_EXEC_AS_USER_FAILED:
		pushstring(T("error"));
		break;
	case SHELL_EXEC_AS_USER_TIMEOUT:
		pushstring(T("timeout"));
		break;
	case SHELL_EXEC_AS_USER_UNSUPPORTED:
		pushstring(T("unsupported"));
		break;
	case SHELL_EXEC_AS_USER_FALLBACK:
		pushstring(T("fallback"));
		break;
	case SHELL_EXEC_AS_USER_NOT_FOUND:
		pushstring(T("not_found"));
		break;
	default:
		pushstring(T("unknown"));
		break;
	}

	if(file) delete [] file;
	if(verb) delete [] verb;
	if(args) delete [] args;
}

///////////////////////////////////////////////////////////////////////////////
// INVOKE SHELL VERB
///////////////////////////////////////////////////////////////////////////////

NSISFUNC(InvokeShellVerb)
{
	static const DWORD ID_LUT[][3] =
	{
		{ 5386, MAXDWORD },
		{ 5387, MAXDWORD },
		{ 51201, 5381, MAXDWORD },
		{ 51394, 5382, MAXDWORD }
	};

	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(path, g_stringsize);
	MAKESTR(file, g_stringsize);

	const int verb = popint();
	popstringn(file, 0);
	popstringn(path, 0);
	
	if(_tcslen(file) < 1) { delete [] file; file = NULL; }
	if(_tcslen(path) < 1) { delete [] path; path = NULL; }

	if(!(file && path))
	{
		if(g_bStdUtilsVerbose)
		{
			MessageBox(NULL, T("Specified file name and/or path is missing!"), T("StdUtils::InvokeShellVerb"), MB_TOPMOST | MB_ICONSTOP);
		}
		pushstring(T("einval"));
		if(file) delete [] file;
		if(path) delete [] path;
		return;
	}

	if((verb < 0) || (verb > 3))
	{
		if(g_bStdUtilsVerbose)
		{
			MessageBox(NULL, T("And invalid verb id has been specified!"), T("StdUtils::InvokeShellVerb"), MB_TOPMOST | MB_ICONSTOP);
		}
		pushstring(T("einval"));
		if(file) delete [] file;
		if(path) delete [] path;
		return;
	}

	int result = MyInvokeShellVerb(path, file, ID_LUT[verb], true);
	
	switch(result)
	{
	case INVOKE_SHELLVERB_SUCCESS:
		pushstring(T("ok"));
		break;
	case INVOKE_SHELLVERB_FAILED:
		pushstring(T("error"));
		break;
	case INVOKE_SHELLVERB_TIMEOUT:
		pushstring(T("timeout"));
		break;
	case INVOKE_SHELLVERB_UNSUPPORTED:
		pushstring(T("unsupported"));
		break;
	case INVOKE_SHELLVERB_NOT_FOUND:
		pushstring(T("not_found"));
		break;
	default:
		pushstring(T("unknown"));
		break;
	}

	if(file) delete [] file;
	if(path) delete [] path;
}

///////////////////////////////////////////////////////////////////////////////
// EXEC SHELL WAIT
///////////////////////////////////////////////////////////////////////////////

NSISFUNC(ExecShellWaitEx)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(file, g_stringsize);
	MAKESTR(verb, g_stringsize);
	MAKESTR(args, g_stringsize);
	
	popstringn(args, 0);
	popstringn(verb, 0);
	popstringn(file, 0);

	SHELLEXECUTEINFO shInfo;
	memset(&shInfo, 0, sizeof(SHELLEXECUTEINFO));
	shInfo.cbSize = sizeof(SHELLEXECUTEINFO);
	shInfo.hwnd = hWndParent;
	shInfo.fMask = SEE_MASK_NOASYNC | SEE_MASK_NOCLOSEPROCESS;
	shInfo.lpFile = file;
	shInfo.lpVerb = (_tcslen(verb) > 0) ? verb : NULL;
	shInfo.lpParameters = (_tcslen(args) > 0) ? args : NULL;
	shInfo.nShow = SW_SHOWNORMAL;

	if(ShellExecuteEx(&shInfo) != FALSE)
	{
		if(VALID_HANDLE(shInfo.hProcess))
		{
			TCHAR out[32];
			SNPRINTF(out, 32, T("hProc:%08X"), shInfo.hProcess);
			pushstring(out);
			pushstring(_T("ok"));
		}
		else
		{
			pushint(0);
			pushstring(T("no_wait"));
		}
	}
	else
	{
		pushint(GetLastError());
		pushstring(T("error"));
	}

	delete [] file;
	delete [] verb;
	delete [] args;
}

NSISFUNC(WaitForProcEx)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(temp, g_stringsize);
	popstringn(temp, 0);

	HANDLE hProc = NULL;
	int result = SSCANF(temp, T("hProc:%X"), &hProc);

	DWORD dwExitCode = 0;
	bool success = false;

	if(result == 1)
	{
		if(hProc != NULL)
		{
			if(WaitForSingleObject(hProc, INFINITE) == WAIT_OBJECT_0)
			{
				success = (GetExitCodeProcess(hProc, &dwExitCode) != FALSE);
			}
			CloseHandle(hProc);
		}
	}

	if(success)
	{
		pushint(dwExitCode);
	}
	else
	{
		pushstring(T("error"));
	}

	delete [] temp;
}


///////////////////////////////////////////////////////////////////////////////
// GET COMMAND-LINE PARAMS
///////////////////////////////////////////////////////////////////////////////

NSISFUNC(GetParameter)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(aval, g_stringsize);
	MAKESTR(name, g_stringsize);

	popstringn(aval, 0);
	popstringn(name, 0);
	commandline_get_arg(STRTRIM(name), aval, g_stringsize);
	pushstring(STRTRIM(aval));

	delete [] aval;
	delete [] name;
}

NSISFUNC(TestParameter)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(name, g_stringsize);

	popstringn(name, 0);
	pushstring(commandline_get_arg(STRTRIM(name), NULL, 0) ? T("true") : T("false"));

	delete [] name;
}

NSISFUNC(ParameterStr)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(value, g_stringsize);

	const int index = popint();
	if(commandline_get_raw(index, value, g_stringsize))
	{
		pushstring(STRTRIM(value));
	}
	else
	{
		pushstring(T("error"));
	}

	delete [] value;
}

NSISFUNC(ParameterCnt)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);

	const int index = commandline_get_cnt();
	if(index >= 0)
	{
		pushint(index);
		return;
	}

	pushstring(T("error"));
}

NSISFUNC(GetAllParameters)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	int truncate = popint();
	const TCHAR *cmd = commandline_get_all();

	if((STRLEN(cmd) < g_stringsize) || truncate)
	{
		pushstring(cmd);
	}
	else
	{
		pushstring(T("too_long"));
	}
}

///////////////////////////////////////////////////////////////////////////////
// GET REAL OS VERSION
///////////////////////////////////////////////////////////////////////////////

NSISFUNC(GetRealOsVersion)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);

	bool flag;
	unsigned int version[3];

	if(get_real_os_version(&version[0], &version[1], &version[2], &flag))
	{
		pushint(version[2]);
		pushint(version[1]);
		pushint(version[0]);
	}
	else
	{
		pushstring(T("error"));
		pushstring(T("error"));
		pushstring(T("error"));
	}
}

NSISFUNC(GetRealOsBuildNo)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);

	bool flag;
	unsigned int buildNumber;

	if(get_real_os_buildNo(&buildNumber, &flag))
	{
		pushint(buildNumber);
	}
	else
	{
		pushstring(T("error"));
	}
}

NSISFUNC(VerifyRealOsVersion)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);

	bool flag;
	unsigned int expectedVersion[3];
	unsigned int detectedVersion[3];

	expectedVersion[2] = abs(popint());
	expectedVersion[1] = abs(popint());
	expectedVersion[0] = abs(popint());

	if(!get_real_os_version(&detectedVersion[0], &detectedVersion[1], &detectedVersion[2], &flag))
	{
		pushstring(T("error"));
		return;
	}

	//Majaor version
	for(size_t i = 0; i < 3; i++)
	{
		if(detectedVersion[i] > expectedVersion[i])
		{
			pushstring(T("newer"));
			return;
		}
		if(detectedVersion[i] < expectedVersion[i])
		{
			pushstring(T("older"));
			return;
		}
	}

	pushstring(T("ok"));
}

NSISFUNC(VerifyRealOsBuildNo)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);

	bool flag;
	unsigned int expectedBuildNo;
	unsigned int detectedBuildNo;

	expectedBuildNo = abs(popint());
	
	if(!get_real_os_buildNo(&detectedBuildNo, &flag))
	{
		pushstring(T("error"));
		return;
	}

	if(detectedBuildNo > expectedBuildNo)
	{
		pushstring(T("newer"));
		return;
	}
	if(detectedBuildNo < expectedBuildNo)
	{
		pushstring(T("older"));
		return;
	}

	pushstring(T("ok"));
}

NSISFUNC(GetRealOsName)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);

	bool flag;
	unsigned int detectedVersion[3];

	if(!get_real_os_version(&detectedVersion[0], &detectedVersion[1], &detectedVersion[2], &flag))
	{
		pushstring(T("error"));
		return;
	}

	pushstring(get_os_friendly_name(detectedVersion[0], detectedVersion[1]));
}

NSISFUNC(GetOsEdition)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);

	bool isServerEdition;
	if(!get_os_server_edition(isServerEdition))
	{
		pushstring(T("error"));
		return;
	}

	pushstring(isServerEdition ? T("server") : T("workstation"));
}

///////////////////////////////////////////////////////////////////////////////
// HASH COMPUTATION
///////////////////////////////////////////////////////////////////////////////

static int GetHashType(const TCHAR *const type)
{
	static const struct
	{
		const TCHAR *const name;
		const int id;
	}
	HASH_ALGO_MAPPING[] =
	{
		{ T("CRC-32"),     STD_HASHTYPE_CRC_32   },
		{ T("MD5-128"),    STD_HASHTYPE_MD5_128  },
		{ T("SHA1-160"),   STD_HASHTYPE_SHA1_160 },
		{ T("SHA2-224"),   STD_HASHTYPE_SHA2_224 },
		{ T("SHA2-256"),   STD_HASHTYPE_SHA2_256 },
		{ T("SHA2-384"),   STD_HASHTYPE_SHA2_384 },
		{ T("SHA2-512"),   STD_HASHTYPE_SHA2_512 },
		{ T("SHA3-224"),   STD_HASHTYPE_SHA3_224 },
		{ T("SHA3-256"),   STD_HASHTYPE_SHA3_256 },
		{ T("SHA3-384"),   STD_HASHTYPE_SHA3_384 },
		{ T("SHA3-512"),   STD_HASHTYPE_SHA3_512 },
		{ T("BLAKE2-224"), STD_HASHTYPE_BLK2_224 },
		{ T("BLAKE2-256"), STD_HASHTYPE_BLK2_256 },
		{ T("BLAKE2-384"), STD_HASHTYPE_BLK2_384 },
		{ T("BLAKE2-512"), STD_HASHTYPE_BLK2_512 },
		{ NULL, -1 }
	};

	for(size_t i = 0; HASH_ALGO_MAPPING[i].name; i++)
	{
		if(STRICMP(type, HASH_ALGO_MAPPING[i].name) == 0)
		{
			return HASH_ALGO_MAPPING[i].id;
		}
	}

	if(g_bStdUtilsVerbose)
	{
		MessageBox(NULL, T("And invalid hash function has been specified!"), T("StdUtils::GetHashType"), MB_TOPMOST | MB_ICONSTOP);
	}

	return -1;
}

NSISFUNC(HashFile)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(file, g_stringsize);
	MAKESTR(temp, g_stringsize);

	popstringn(file, 0);
	popstringn(temp, 0);

	const int hashType = GetHashType(STRTRIM(temp));
	if(hashType >= 0)
	{
		if(ComputeHash_FromFile(hashType, file, temp, g_stringsize))
		{
			pushstring(temp);
		}
		else
		{
			pushstring(T("error"));
		}
	}
	else
	{
		pushstring(T("invalid"));
	}

	delete [] file;
	delete [] temp;
}

NSISFUNC(HashText)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(temp, g_stringsize);
	MAKESTR(text, g_stringsize);

	popstringn(text, 0);
	popstringn(temp, 0);

	const int hashType = GetHashType(STRTRIM(temp));
	if(hashType >= 0)
	{
		if(ComputeHash_FromText(hashType, text, temp, g_stringsize))
		{
			pushstring(temp);
		}
		else
		{
			pushstring(T("error"));
		}
	}
	else
	{
		pushstring(T("invalid"));
	}

	delete [] text;
	delete [] temp;
}

///////////////////////////////////////////////////////////////////////////////
// CREATE/DESTROY TIMER
///////////////////////////////////////////////////////////////////////////////

NSISFUNC(TimerCreate)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);

	const int interval = popint();
	const int procAddress = popint();

	UINT_PTR id;
	if(timer_create(procAddress, interval, hWndParent, extra, id))
	{
		TCHAR out[32];
		SNPRINTF(out, 32, T("TimerId:%08X"), id);
		pushstring(out);
	}
	else
	{
		pushstring(T("error"));
	}
}

NSISFUNC(TimerDestroy)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	MAKESTR(temp, g_stringsize);

	popstringn(temp, 0);
	UINT_PTR id;
	bool success = false;

	if(SSCANF(temp, T("TimerId:%X"), &id) == 1)
	{
		success = timer_destroy(id);
	}

	pushstring(success ? T("ok") : T("error"));
	delete [] temp;
}

///////////////////////////////////////////////////////////////////////////////
// FOR DEBUGGING
///////////////////////////////////////////////////////////////////////////////

NSISFUNC(EnableVerboseMode)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	g_bStdUtilsVerbose = true;
}

NSISFUNC(DisableVerboseMode)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	g_bStdUtilsVerbose = false;
}

///////////////////////////////////////////////////////////////////////////////

#include "resource.h"

static const TCHAR *dllTimeStamp = T(__DATE__) T(", ") T(__TIME__);
static const TCHAR *dllVerString = T(DLL_VERSION_STRING);

NSISFUNC(GetLibVersion)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
	pushstring(dllTimeStamp);
	pushstring(dllVerString);
}

///////////////////////////////////////////////////////////////////////////////

NSISFUNC(Dummy)
{
	EXDLL_INIT();
	REGSITER_CALLBACK(g_StdUtilsInstance);
}
