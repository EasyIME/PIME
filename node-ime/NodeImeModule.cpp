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

#include "NodeImeModule.h"
#include "NodeTextService.h"
#include <string>
#include <ShlObj.h>
#include <cpprest/json.h>

namespace Node {

// CLSID of our Text service
// {13F2EF08-575C-4D8C-88E0-F67BB8052B84}
const CLSID g_textServiceClsid = {
	0x13f2ef08, 0x575c, 0x4d8c, { 0x88, 0xe0, 0xf6, 0x7b, 0xb8, 0x5, 0x2b, 0x84 }
};

ImeModule::ImeModule(HMODULE module):
	Ime::ImeModule(module, g_textServiceClsid) {

	// override default location of chewing data directories
	std::wstring env;
	wchar_t path[MAX_PATH];

	HRESULT result;

	// get user profile directory
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

	// get the program data directory
	// try C:\program files (x86) first
	result = ::SHGetFolderPathW(NULL, CSIDL_PROGRAM_FILESX86, NULL, 0, path);
	if(result != S_OK) // failed, fall back to C:\program files
		result = ::SHGetFolderPathW(NULL, CSIDL_PROGRAM_FILES, NULL, 0, path);
	if(result == S_OK) { // program files folder is found
		programDir_ = path;
		programDir_ += L"\\ChewingTextService";
		env = L"CHEWING_PATH=";
		// prepend user dir path to program path, so user-specific files, if they exist,
		// can take precedence over built-in ones. (for ex: symbols.dat)
		env += userDir_;
		env += ';'; // add ; to separate two dir paths
		// add program dir after user profile dir
		env += programDir_;
		env += L"\\Dictionary";
		_wputenv(env.c_str());
	}

}

ImeModule::~ImeModule(void) {
}

// virtual
Ime::TextService* ImeModule::createTextService() {
	TextService* service = new Node::TextService(this);
	return service;
}

// virtual
bool ImeModule::onConfigure(HWND hwndParent) {
	// launch ChewingPreferences
	// ::ShellExecuteW(hwndParent, L"open", path.c_str(), NULL, NULL, SW_SHOWNORMAL);
	return true;
}


} // namespace Chewing
