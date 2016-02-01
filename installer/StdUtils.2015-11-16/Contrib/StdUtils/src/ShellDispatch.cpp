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

#include "ShellDispatch.h"

typedef struct
{
	int returnValue;
	const shell_dispatch_handler_t handler;
	void *const data;
}
threadParam_t;

///////////////////////////////////////////////////////////////////////////////

static unsigned __stdcall ShellTest_ThreadHelperProc(void* pArguments)
{
	HRESULT hr = CoInitialize(NULL);
	if((hr == S_OK) || (hr == S_FALSE))
	{
		if(threadParam_t *params = (threadParam_t*) pArguments)
		{
			params->returnValue = MyShellDispatch(params->handler, params->data, false);
		}
		DispatchPendingMessages(1000); //Required to avoid potential deadlock or crash on CoUninitialize() !!!
		CoUninitialize();
	}
	else
	{
		if(threadParam_t *params = (threadParam_t*) pArguments)
		{
			params->returnValue = SHELL_DISPATCH_FAILED;
		}
	}

	return EXIT_SUCCESS;
}

static void MyShellDispatch_AllowSetForegroundWindow(const HWND &hwnd)
{
	DWORD dwProcessId = 0;
	if(GetWindowThreadProcessId(hwnd, &dwProcessId))
	{
		if(dwProcessId != 0)
		{
			AllowSetForegroundWindow(dwProcessId);
		}
	}
}

static int MyShellDispatch_ShellDispatchProc(const shell_dispatch_handler_t handler, void *const data)
{
	int iSuccess = SHELL_DISPATCH_FAILED;

	IShellWindows *psw = NULL;
	HRESULT hr = CoCreateInstance(CLSID_ShellWindows, NULL, CLSCTX_LOCAL_SERVER, IID_PPV_ARGS(&psw));
	if(SUCCEEDED(hr))
	{
		HWND desktopHwnd = 0;
		IDispatch* pdisp = NULL;
		variant_t vEmpty;
		if(S_OK == psw->FindWindowSW(vEmpty, vEmpty, SWC_DESKTOP, (long*)&desktopHwnd, SWFO_NEEDDISPATCH, &pdisp))
		{
			if(VALID_HANDLE(desktopHwnd))
			{
				IShellBrowser *psb;
				hr = IUnknown_QueryService(pdisp, SID_STopLevelBrowser, IID_PPV_ARGS(&psb));
				if(SUCCEEDED(hr))
				{
					IShellView *psv = NULL;
					hr = psb->QueryActiveShellView(&psv);
					if(SUCCEEDED(hr))
					{
						IDispatch *pdispBackground = NULL;
						HRESULT hr = psv->GetItemObject(SVGIO_BACKGROUND, IID_PPV_ARGS(&pdispBackground));
						if(SUCCEEDED(hr))
						{
							MyShellDispatch_AllowSetForegroundWindow(desktopHwnd);
							IShellFolderViewDual *psfvd = NULL;
							HRESULT hr = pdispBackground->QueryInterface(IID_PPV_ARGS(&psfvd));
							if(SUCCEEDED(hr))
							{
								IDispatch *pdisp = NULL;
								hr = psfvd->get_Application(&pdisp);
								if(SUCCEEDED(hr))
								{
									IShellDispatch2 *pShellDispatch;
									hr = pdisp->QueryInterface(IID_PPV_ARGS(&pShellDispatch));
									if(SUCCEEDED(hr))
									{
										iSuccess = handler(pShellDispatch, data);
									}
									RELEASE_OBJ(pdisp);
								}
								RELEASE_OBJ(psfvd);
							}
							RELEASE_OBJ(pdispBackground);
						}
						RELEASE_OBJ(psv);
					}
					RELEASE_OBJ(psb);
				}
			}
			RELEASE_OBJ(pdisp);
		}
		RELEASE_OBJ(psw);
	}

	return iSuccess;
}

int MyShellDispatch(const shell_dispatch_handler_t handler, void *const data, const bool &threaded)
{
	int iSuccess = SHELL_DISPATCH_FAILED;

	if(threaded)
	{
		threadParam_t threadParams = { (-1), handler, data };
		HANDLE hThread = (HANDLE) _beginthreadex(NULL, 0, ShellTest_ThreadHelperProc, &threadParams, 0, NULL);
		if(VALID_HANDLE(hThread))
		{
			DWORD status = WaitForSingleObject(hThread, 30000);
			if(status == WAIT_OBJECT_0)
			{
				iSuccess = threadParams.returnValue;
			}
			else if(status == WAIT_TIMEOUT)
			{
				iSuccess = SHELL_DISPATCH_TIMEOUT;
				TerminateThread(hThread, EXIT_FAILURE);
			}
			CloseHandle(hThread);
		}
	}
	else
	{
		iSuccess = MyShellDispatch_ShellDispatchProc(handler, data);
	}
	
	return iSuccess;
}
