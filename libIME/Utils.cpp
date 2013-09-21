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

std::wstring utf8ToUtf16(const char* text) {
	std::wstring wtext;
	int wlen = ::MultiByteToWideChar(CP_UTF8, 0, text, -1, NULL, 0);
	if(wlen > 1) { // length includes terminating null
		wtext.resize(wlen - 1);
		// well, this is a little bit dirty, but it works!
		wlen = ::MultiByteToWideChar(CP_UTF8, 0, text, -1, &wtext[0], wlen);
	}
	return wtext;
}

std::string utf16ToUtf8(const wchar_t* wtext) {
	std::string text;
	int len = ::WideCharToMultiByte(CP_UTF8, 0, wtext, -1, NULL, 0, NULL, NULL);
	if(len > 1) { // length includes terminating null
		text.resize(len - 1);
		// well, this is a little bit dirty, but it works!
		len = ::WideCharToMultiByte(CP_UTF8, 0, wtext, -1, &text[0], len, NULL, NULL);
	}
	return text;
}
