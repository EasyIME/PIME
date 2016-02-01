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

/*
 * Both, NULL and INVALID_HANDLE_VALUE, are *reserved* by the system and therefore can *never* be a valid HANDLE or HWND value.
 * However, due to historical reasons, the Win32 API is very inconsistent and may return either NULL or INVALID_HANDLE_VALUE to indicate errors!
 * The actual error value can differ from function to function. For the sake of simplicity/safety, we check for *both* Non-Handle values.
 *
 * Source: http://blogs.msdn.com/b/oldnewthing/archive/2004/03/02/82639.aspx
 */
#define VALID_HANDLE(H) (((H) != NULL) && ((H) != INVALID_HANDLE_VALUE))

/*
 * Close Win32 Handler
 */
#define CLOSE_HANDLE(H) do \
{ \
	if(VALID_HANDLE((H))) { CloseHandle((H)); (H) = NULL; } \
} \
while(0)

/*
 * MIN and MAX functions
 */
template<class T> static const T &MAX_VAL(const T &a, const T &b)
{
	return (a > b) ? a : b;
}
template<class T> static const T &MIN_VAL(const T &a, const T &b)
{
	return (a < b) ? a : b;
}

/*
 * Check for file existence
 */
static bool FILE_EXISTS(const TCHAR *const filePath)
{
	if(GetFileAttributes(filePath) == INVALID_FILE_ATTRIBUTES)
	{
		return false;
	}
	return true;
}
