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

#include "TimerUtils.h"

#include "Mutex.h"
#include "UnicodeSupport.h"
#include "CleanUp.h"

//const
static const unsigned __int64 MARKER_VALUE = 0x71D7D671BB14DE73ui64;

//External
extern RTL_CRITICAL_SECTION g_pStdUtilsMutex;
extern HINSTANCE g_StdUtilsInstance;

//Typedef
typedef struct _timer_data_t
{
	unsigned __int64 marker;
	HWND hWndMsgHandler;
	HWND hWndParent;
	int (NSISCALL *pExecuteCodeSegment)(int, HWND);
	int procAddress;
}
timer_data_t;

//Globals
static volatile LONG g_counter;
static volatile ATOM g_wndClass = 0;

//CRT
extern "C"
{
	size_t __cdecl _msize(void *_Memory);
	typedef intptr_t (__cdecl *get_heap_handle_t)(void);
}

///////////////////////////////////////////////////////////////////////////////
// GET HEAP HANDLER
///////////////////////////////////////////////////////////////////////////////

static bool get_heap_handle(HANDLE &heap_handle)
{
	heap_handle = NULL;
	if(const HMODULE mod_msvcrt = GetModuleHandle(T("msvcrt")))
	{
		if(const get_heap_handle_t p_get_heap_handle = (get_heap_handle_t) GetProcAddress(mod_msvcrt, "_get_heap_handle"))
		{
			heap_handle = (HANDLE) p_get_heap_handle();
			return true;
		}
	}
	return false;
}

static bool is_valid_ptr(void *const ptr, const size_t size)
{
	HANDLE heap_handle = NULL;
	if(get_heap_handle(heap_handle))
	{
		if(HeapValidate(heap_handle, 0, ptr))
		{
			return (_msize(ptr) >= size);
		}
		return false;
	}
	return true;
}

///////////////////////////////////////////////////////////////////////////////
// CALLBACK FUNCTIONS
///////////////////////////////////////////////////////////////////////////////

static LRESULT CALLBACK MyWindowProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
	return 1;
}

static VOID CALLBACK MyTimerProc(HWND hwnd, UINT uMsg, UINT_PTR idEvent, DWORD dwTime)
{
	const timer_data_t *const data = (const timer_data_t*) idEvent;
	data->pExecuteCodeSegment((data->procAddress - 1), data->hWndParent);
}

///////////////////////////////////////////////////////////////////////////////
// INITIALIZATION FUNCTIONS
///////////////////////////////////////////////////////////////////////////////

static void free_wndclass(void)
{
	MutexLocker locker(&g_pStdUtilsMutex);
	if(g_wndClass != 0)
	{
		if(InterlockedExchange(&g_counter, 0) != 0)
		{
			MessageBox(NULL, T("Whoops: Plug-in unloaded before all timers were destroyed!"), T("StdUtils::TimerCreate"), MB_ICONERROR|MB_TOPMOST);
		}
		UnregisterClass((PTCHAR)DWORD(g_wndClass), g_StdUtilsInstance);
		g_wndClass = 0;
	}
}

static bool init_wndclass(void)
{
	MutexLocker locker(&g_pStdUtilsMutex);
	if(g_wndClass == 0)
	{
		WNDCLASS wndClass;
		ZeroMemory(&wndClass, sizeof(WNDCLASS));
		wndClass.hInstance = g_StdUtilsInstance;
		wndClass.lpfnWndProc = MyWindowProc;
		wndClass.lpszClassName = T("{05D27C4B-7159-4291-8843-01FC5DA4A7DC}");
		g_wndClass = RegisterClass(&wndClass);
		if(g_wndClass != 0)
		{
			cleanup_register_task(free_wndclass);
			return true;
		}
		return false;
	}
	return true;
}

///////////////////////////////////////////////////////////////////////////////
// PUBLIC FUNCTIONS
///////////////////////////////////////////////////////////////////////////////

bool timer_create(const int procAddress, const int interval, const HWND hWndParent, const extra_parameters *const extra, UINT_PTR &id_out)
{
	id_out = NULL;

	if((procAddress <= 0) || (interval <= 0))
	{
		return false;
	}

	if(!((g_wndClass != 0) || init_wndclass()))
	{
		return false;
	}

	const HWND hWndMsgHandler = CreateWindow((PTCHAR)DWORD(g_wndClass), NULL, 0, 0, 0,  1, 1, HWND_MESSAGE, NULL, g_StdUtilsInstance, 0);
	if(hWndMsgHandler == NULL)
	{
		return false;
	}

	timer_data_t *data = new timer_data_t;
	memset(data, 0, sizeof(timer_data_t));

	data->marker = MARKER_VALUE;
	data->hWndMsgHandler = hWndMsgHandler;
	data->hWndParent = hWndParent;
	data->pExecuteCodeSegment = extra->ExecuteCodeSegment;
	data->procAddress = procAddress;

	if(SetTimer(hWndMsgHandler, UINT_PTR(data), 1500, MyTimerProc) == 0)
	{
		DestroyWindow(hWndMsgHandler);
		delete data;
		return false;
	}

	id_out = UINT_PTR(data);
	InterlockedIncrement(&g_counter);
	return true;
}

bool timer_destroy(const UINT_PTR id)
{
	bool success = false;
	if(timer_data_t *data = (timer_data_t*) id)
	{
		if(is_valid_ptr(data, sizeof(timer_data_t)) && (data->marker == MARKER_VALUE))
		{
			const BOOL ok1 = KillTimer(data->hWndMsgHandler, id);
			const BOOL ok2 = DestroyWindow(data->hWndMsgHandler);
			if(ok1 && ok2)
			{
				InterlockedDecrement(&g_counter);
				success = true;
			}
			memset(data, 0, sizeof(timer_data_t));
			delete data;
		}
		else
		{
			MessageBox(NULL, T("Whoops: Double destruction detected and prevented!"), T("StdUtils::TimerDestroy"), MB_ICONSTOP | MB_TOPMOST);
		}
	}
	return success;
}
