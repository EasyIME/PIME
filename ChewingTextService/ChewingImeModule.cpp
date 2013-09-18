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

#include "ChewingImeModule.h"
#include "ChewingTextService.h"
#include <string>
#include <ShlObj.h>

namespace Chewing {

// CLSID of our Text service
// {13F2EF08-575C-4D8C-88E0-F67BB8052B84}
const CLSID g_textServiceClsid = {
	0x13f2ef08, 0x575c, 0x4d8c, { 0x88, 0xe0, 0xf6, 0x7b, 0xb8, 0x5, 0x2b, 0x84 }
};

ImeModule::ImeModule(HMODULE module):
	Ime::ImeModule(module, g_textServiceClsid),
	config_(this) {

	// override default location of chewing data directories
	std::wstring env;
	wchar_t path[MAX_PATH];
	if(::SHGetFolderPathW(NULL, CSIDL_PROGRAM_FILESX86, NULL, 0, path) == S_OK) {
		wcscat(path, L"\\ChewingTextService\\Dictionary");
		env = L"CHEWING_PATH=";
		env += path;
		_wputenv(env.c_str());
	}

	if(::GetEnvironmentVariableW(L"USERPROFILE", path, MAX_PATH)) {
		userDir_ = path;
		userDir_ += L"\\ChewingTextService";
		// create the user directory if not exists
		// NOTE: this call will fail in Windows 8 store apps
		// We need a way to create the dir in desktop mode and
		// set proper ACL, so later we can access it inside apps.
		DWORD attributes = ::GetFileAttributesW(userDir_.c_str());
		if(attributes == INVALID_FILE_ATTRIBUTES) {
			// create the directory if it does not exist
			if(::GetLastError() == ERROR_FILE_NOT_FOUND) {
				::CreateDirectoryW(userDir_.c_str(), NULL);
				attributes = ::GetFileAttributesW(userDir_.c_str());
			}
		}

		// make the directory hidden
		if(attributes != INVALID_FILE_ATTRIBUTES && (attributes & FILE_ATTRIBUTE_HIDDEN) == 0)
			::SetFileAttributesW(userDir_.c_str(), attributes|FILE_ATTRIBUTE_HIDDEN);

		env = L"CHEWING_USER_PATH=";
		env += userDir_;
		_wputenv(env.c_str());
	}
}

ImeModule::~ImeModule(void) {
}

// virtual
Ime::TextService* ImeModule::createTextService() {
	TextService* service = new Chewing::TextService(this);
	return service;
}

} // namespace Chewing
