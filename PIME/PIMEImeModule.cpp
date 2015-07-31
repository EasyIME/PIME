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

#include "PIMEImeModule.h"
#include "PIMETextService.h"
#include <string>
#include <ShlObj.h>

namespace PIME {

// CLSID of our Text service
// {35F67E9D-A54D-4177-9697-8B0AB71A9E04}
const GUID g_textServiceClsid = 
{ 0x35f67e9d, 0xa54d, 0x4177, { 0x96, 0x97, 0x8b, 0xa, 0xb7, 0x1a, 0x9e, 0x4 } };

ImeModule::ImeModule(HMODULE module):
	Ime::ImeModule(module, g_textServiceClsid) {

	// override default location of chewing data directories
	std::wstring env;
	wchar_t path[MAX_PATH];

	HRESULT result;

	// get the program data directory
	// try C:\program files (x86) first
	result = ::SHGetFolderPathW(NULL, CSIDL_PROGRAM_FILESX86, NULL, 0, path);
	if(result != S_OK) // failed, fall back to C:\program files
		result = ::SHGetFolderPathW(NULL, CSIDL_PROGRAM_FILES, NULL, 0, path);
	if(result == S_OK) { // program files folder is found
		programDir_ = path;
		programDir_ += L"\\PIME";
	}
}

ImeModule::~ImeModule(void) {
}

// virtual
Ime::TextService* ImeModule::createTextService() {
	TextService* service = new PIME::TextService(this);
	return service;
}

// virtual
bool ImeModule::onConfigure(HWND hwndParent) {
	// launch ChewingPreferences
	// ::ShellExecuteW(hwndParent, L"open", path.c_str(), NULL, NULL, SW_SHOWNORMAL);
	return true;
}


} // namespace Chewing
