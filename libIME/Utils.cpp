//
//	Copyright (C) 2013 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
//
//	This library is free software; you can redistribute it and/or
//	modify it under the terms of the GNU Library General Public
//	License as published by the Free Software Foundation; either
//	version 2 of the License, or (at your option) any later version.
//
//	This library is distributed in the hope that it will be useful,
//	but WITHOUT ANY WARRANTY; without even the implied warranty of
//	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
//	Library General Public License for more details.
//
//	You should have received a copy of the GNU Library General Public
//	License along with this library; if not, write to the
//	Free Software Foundation, Inc., 51 Franklin St, Fifth Floor,
//	Boston, MA  02110-1301, USA.
//

#include "Utils.h"
#include <Windows.h>

wchar_t* utf8ToUtf16(const char* text, int* outLen) {
	wchar_t *wtext = NULL;
	int wlen = ::MultiByteToWideChar(CP_UTF8, 0, text, -1, NULL, 0);
	wtext = new WCHAR[wlen];
	wlen = ::MultiByteToWideChar(CP_UTF8, 0, text, -1, wtext, wlen);
	if(wlen > 0) {
		--wlen; // wlen includes the terminating null char
		wtext[wlen] = 0;
	}
	if(outLen)
		*outLen = wlen;
	return wtext;
}

char* utf16ToUtf8(const wchar_t* wtext, int* outLen) {
	char *text = NULL;
	int len = ::WideCharToMultiByte(CP_UTF8, 0, wtext, -1, NULL, 0, NULL, NULL);
	text = new char[len];
	len = ::WideCharToMultiByte(CP_UTF8, 0, wtext, -1, text, len, NULL, NULL);
	if(len > 0) {
		--len; // len includes the terminating null char
		text[len] = 0;
	}
	if(outLen)
		*outLen = len;
	return text;
}
