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

///////////////////////////////////////////////////////////////////////////////
// The following code was strongly inspired by the "InvokeShellVerb" plug-in
// Copyright (c) 2011 Robert Strong
// For details see: http://nsis.sourceforge.net/Invoke_Shell_Verb_plugin
///////////////////////////////////////////////////////////////////////////////

#include "InvokeShellVerb.h"
#include "ShellDispatch.h"
#include "nsis_tchar.h"

///////////////////////////////////////////////////////////////////////////////

typedef struct
{
	const DWORD *uiVerbIds;
	const TCHAR *const pcDirectoryName;
	const TCHAR *const pcFileName;
}
invoke_shellverb_param_t;

static const WCHAR *shell32 = L"shell32";

///////////////////////////////////////////////////////////////////////////////

static bool MyInvokeShellVerb_LoadResStr(const WCHAR *const libFile, const DWORD *const ids, wchar_t *const buffer, const size_t &buffSize)
{
	memset(buffer, 0, sizeof(WCHAR) * buffSize);

	bool bUnloadDll = false;
	HMODULE hMod = GetModuleHandleW(libFile); 
	if(hMod == NULL)
	{
		bUnloadDll = true;
		hMod = LoadLibraryW(libFile);
		if(hMod == NULL)
		{
			return false;
		}
	}

	bool success = false;
	for(size_t i = 0; ids[i] != MAXDWORD; i++)
	{
		if(LoadStringW(hMod, ids[i], buffer, buffSize) > 0)
		{
			success = true;
			break;
		}
	}

	if(bUnloadDll)
	{
		FreeLibrary(hMod);
		hMod = NULL;
	}

	return success;
}

static int MyInvokeShellVerb_HandlerProc(IShellDispatch2 *const dispatch, const void *const data)
{
	int iSuccess = INVOKE_SHELLVERB_FAILED;
	const invoke_shellverb_param_t *const param = (const invoke_shellverb_param_t*) data;

	WCHAR pcVerbName[256];
	if(!MyInvokeShellVerb_LoadResStr(shell32, param->uiVerbIds, pcVerbName, 256))
	{
		return (iSuccess = INVOKE_SHELLVERB_NOT_FOUND);
	}

	// ----------------------------------- //

	Folder *pFolder = NULL; FolderItem *pItem = NULL;

	variant_t vaDirectory(param->pcDirectoryName);
	HRESULT hr = dispatch->NameSpace(vaDirectory, &pFolder);
	if(FAILED(hr) || (pFolder == NULL))
	{
		return (iSuccess = INVOKE_SHELLVERB_NOT_FOUND);
	}

	variant_t vaFileName(param->pcFileName);
	hr = pFolder->ParseName(vaFileName, &pItem);
	if(FAILED(hr) || (pItem == NULL))
	{
		RELEASE_OBJ(pFolder);
		return (iSuccess = INVOKE_SHELLVERB_NOT_FOUND);
	}

	RELEASE_OBJ(pFolder);

	// ----------------------------------- //

	long iVerbCount = 0;
	FolderItemVerbs *pVerbs = NULL;
	
	hr = pItem->Verbs(&pVerbs);
	if(FAILED(hr) || (pVerbs == NULL))
	{
		RELEASE_OBJ(pItem);
		return iSuccess;
	}

	RELEASE_OBJ(pItem);

	hr = pVerbs->get_Count(&iVerbCount);
	if(FAILED(hr) || (iVerbCount < 1))
	{
		RELEASE_OBJ(pVerbs);
		return iSuccess;
	}

	DispatchPendingMessages(125);

	// ----------------------------------- //

	for(int i = 0; i < iVerbCount; i++)
	{
		variant_t vaVariantIndex(i);
		FolderItemVerb *pCurrentVerb = NULL;
		BSTR pcCurrentVerbName = NULL;

		hr = pVerbs->Item(vaVariantIndex, &pCurrentVerb);
		if (FAILED(hr) || (pCurrentVerb == NULL))
		{
			continue;
		}
		
		hr = pCurrentVerb->get_Name(&pcCurrentVerbName);
		if(FAILED(hr) || (pcCurrentVerbName == NULL))
		{
			RELEASE_OBJ(pCurrentVerb);
			continue;
		}

		if(_wcsicmp(pcCurrentVerbName, pcVerbName) == 0)
		{
			hr = pCurrentVerb->DoIt();
			if(!FAILED(hr))
			{
				iSuccess = INVOKE_SHELLVERB_SUCCESS;
			}
		}

		SysFreeString(pcCurrentVerbName);
		RELEASE_OBJ(pCurrentVerb);

		if(iSuccess == INVOKE_SHELLVERB_SUCCESS)
		{
			break; /*succeeded*/
		}
	}

	RELEASE_OBJ(pVerbs);

	// ----------------------------------- //
	
	return iSuccess;
}

int MyInvokeShellVerb(const TCHAR *const pcDirectoryName, const TCHAR *const pcFileName, const DWORD *const uiVerbIds, const bool threaded)
{
	int iSuccess = INVOKE_SHELLVERB_FAILED;

	if(TCHAR *const path = (TCHAR*) calloc(_tcsclen(pcDirectoryName) + _tcsclen(pcFileName) + 3, sizeof(TCHAR)))
	{
		_tcscat(path, pcDirectoryName);
		_tcscat(path, _T("\\"));
		_tcscat(path, pcFileName);
		const bool fileExists = FILE_EXISTS(path);
		free(path);
		if(!fileExists)
		{
			return (iSuccess = INVOKE_SHELLVERB_NOT_FOUND);
		}
	}

	OSVERSIONINFO osVersion;
	memset(&osVersion, 0, sizeof(OSVERSIONINFO));
	osVersion.dwOSVersionInfoSize = sizeof(OSVERSIONINFO);
	
	if(GetVersionEx(&osVersion))
	{
		if((osVersion.dwPlatformId == VER_PLATFORM_WIN32_NT) && ((osVersion.dwMajorVersion > 6) || ((osVersion.dwMajorVersion == 6) && (osVersion.dwMinorVersion >= 1))))
		{
			invoke_shellverb_param_t params = { uiVerbIds, pcDirectoryName, pcFileName };
			iSuccess = MyShellDispatch(MyInvokeShellVerb_HandlerProc, &params, threaded);
		}
		else
		{
			iSuccess = INVOKE_SHELLVERB_UNSUPPORTED;
		}
	}

	return iSuccess;
}
