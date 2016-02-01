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

#include "ComUtils.h"

static void DispatchPendingMessages_Helper(void)
{
	for(int i = 0; i < 16; i++)
	{
		MSG msg; bool flag = false;
		while(PeekMessage(&msg, NULL, 0, 0, PM_REMOVE))
		{
			DispatchMessage(&msg);
			flag = true;
		}
		if(flag) 
		{
			Sleep(0);
			continue;
		}
		break;
	}
}

/*
 * Each single-threaded apartment (STA) must have a message loop to handle calls from other processes and apartments within the same process!
 * In order to avoid deadlock or crash, we use CoWaitForMultipleHandles() to dispatch the pending messages, as it will perform "message pumping" while waiting.
 * Source: http://msdn.microsoft.com/en-us/library/windows/desktop/ms680112%28v=vs.85%29.aspx | http://msdn.microsoft.com/en-us/library/ms809971.aspx
 */
void DispatchPendingMessages(const DWORD &dwTimeout)
{
#ifndef DISABLE_DISPATCH_DELAY
	const DWORD dwMaxTicks = GetTickCount() + (10 * dwTimeout);
	for(;;)
	{
		DispatchPendingMessages_Helper();
		const DWORD dwReturn = MsgWaitForMultipleObjects(0, NULL, FALSE, dwTimeout, QS_ALLINPUT | QS_ALLPOSTMESSAGE);
		if((dwReturn == WAIT_TIMEOUT) || (dwReturn == WAIT_FAILED) || (GetTickCount() > dwMaxTicks))
		{
			break; /*no more messages received*/
		}
	}
#endif //DISABLE_DISPATCH_DELAY
	DispatchPendingMessages_Helper();
}
