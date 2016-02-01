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

#include "CleanUp.h"
#include "Mutex.h"

//Task Stack
static const size_t MAX_TASKS = 32;
static cleanup_task_t s_task_lst[MAX_TASKS];
static size_t s_task_pos = 0;

//StdLib
extern "C" __declspec(dllimport) void __cdecl abort(void);

//External
extern RTL_CRITICAL_SECTION g_pStdUtilsMutex;

///////////////////////////////////////////////////////////////////////////////
// INTERNAL FUNCTIONS
///////////////////////////////////////////////////////////////////////////////

static void task_put(const cleanup_task_t task)
{
	MutexLocker lock(&g_pStdUtilsMutex);
	if(s_task_pos < MAX_TASKS)
	{
		s_task_lst[s_task_pos++] = task;
		return;
	}
	abort();
}

static cleanup_task_t task_pop(void)
{
	MutexLocker lock(&g_pStdUtilsMutex);
	cleanup_task_t task = NULL;
	if(s_task_pos > 0)
	{
		task = s_task_lst[--s_task_pos];
	}
	return task;
}

///////////////////////////////////////////////////////////////////////////////
// PUBLIC FUNCTIONS
///////////////////////////////////////////////////////////////////////////////

void cleanup_register_task(const cleanup_task_t task)
{
	task_put(task);
}

void cleanup_execute_tasks(void)
{
	while(const cleanup_task_t task = task_pop())
	{
		task();
	}
}
