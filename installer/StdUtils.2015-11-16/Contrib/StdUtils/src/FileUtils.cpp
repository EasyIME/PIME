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

#include "FileUtils.h"

//Includes
#include "WinUtils.h"
#include "UnicodeSupport.h"

//External vars
extern bool g_bStdUtilsVerbose;

static bool FileSize(const HANDLE h, long long *sizeOut)
{
	LARGE_INTEGER size;
	SecureZeroMemory(&size, sizeof(LARGE_INTEGER));
	if(GetFileSizeEx(h, &size))
	{
		*sizeOut = size.QuadPart;
		return true;
	}
	return false;
}

static bool SeekFile(const HANDLE h, const DWORD method, long long posIn)
{
	LARGE_INTEGER pos;
	SecureZeroMemory(&pos, sizeof(LARGE_INTEGER));
	pos.QuadPart = posIn;
	if(SetFilePointerEx(h, pos, NULL, method))
	{
		return true;
	}
	return false;
}

#define RETURN(X) do \
{ \
	CLOSE_HANDLE(hFrom); \
	CLOSE_HANDLE(hDest); \
	return (X); \
} \
while(0)

#define ERROR_MSG(X) do \
{ \
	if(g_bStdUtilsVerbose) \
	{ \
		MessageBox(NULL, (X), T("StdUtils::AppendToFile"), MB_ICONERROR|MB_TOPMOST); \
	} \
} \
while(0)

bool AppendToFile(const TCHAR *const from, const TCHAR *const dest, const DWORD offset, const DWORD maxlen, unsigned long long *bytesCopied)
{
	*bytesCopied = 0;
	HANDLE hFrom = NULL, hDest = NULL;

	hFrom = CreateFile(from, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, 0, NULL);
	if(!VALID_HANDLE(hFrom))
	{
		ERROR_MSG(T("Failed to open source file for reading!"));
		RETURN(false);
	}

	long long sizeFrom = 0;
	if(!FileSize(hFrom, &sizeFrom))
	{
		ERROR_MSG(T("Failed to get size of source file!"));
		RETURN(false);
	}

	if(sizeFrom <= static_cast<long long>(offset))
	{
		RETURN(true);
	}

	if(offset > 0)
	{
		if(!SeekFile(hFrom, FILE_BEGIN, offset))
		{
			ERROR_MSG(T("Failed to skip the offset bytes!"));
			RETURN(false);
		}
	}

	hDest = CreateFile(dest, FILE_APPEND_DATA, 0, NULL, OPEN_ALWAYS, 0, NULL);
	if(!VALID_HANDLE(hDest))
	{
		ERROR_MSG(T("Failed to open output file for writing!"));
		RETURN(false);
	}

	if(!SeekFile(hDest, FILE_END, 0))
	{
		ERROR_MSG(T("Failed to seek to the end of output file!"));
		RETURN(false);
	}

	const long long availableBytes = sizeFrom - static_cast<long long>(offset);
	long long bytesLeft = (maxlen > 0) ? MIN_VAL(static_cast<long long>(maxlen), availableBytes) : availableBytes;

	while(bytesLeft > 0i64)
	{
		static const size_t BUFF_SIZE = 8192;
		BYTE buffer[BUFF_SIZE];
		const DWORD bytesToRead = static_cast<DWORD>(MIN_VAL(bytesLeft, static_cast<long long>(BUFF_SIZE)));

		DWORD bytesRead = 0;
		if((!ReadFile(hFrom, &buffer[0], bytesToRead, &bytesRead, NULL)) || (bytesRead < 1))
		{
			ERROR_MSG(T("Failed to read from source file!"));
			break;
		}

		DWORD bytesWritten = 0;
		if((!WriteFile(hDest, &buffer[0], bytesRead, &bytesWritten, NULL)) || (bytesWritten != bytesRead))
		{
			ERROR_MSG(T("Failed to write to output file!"));
			break;
		}

		bytesLeft    -= static_cast<long long>(bytesWritten);
		*bytesCopied += static_cast<long long>(bytesWritten);
	}

	RETURN(bytesLeft <= 0);
}
