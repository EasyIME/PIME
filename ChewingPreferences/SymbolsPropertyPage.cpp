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

#include "SymbolsPropertyPage.h"
#include "resource.h"
#include <ShlObj.h>
#include <libIME/Utils.h>

namespace Chewing {

SymbolsPropertyPage::SymbolsPropertyPage(Config* config):
	Ime::PropertyPage((LPCTSTR)IDD_SYMBOLS),
	config_(config) {

	wchar_t path[MAX_PATH];
	// get user profile directory
	if(::GetEnvironmentVariableW(L"USERPROFILE", path, MAX_PATH)) {
		userDir_ = path;
		userDir_ += L"\\ChewingTextService";
	}
}

SymbolsPropertyPage::~SymbolsPropertyPage(void) {
}

// virtual
bool SymbolsPropertyPage::onInitDialog() {
	wchar_t basename[] = L"\\symbols.dat";
	std::wstring filename = userDir_ + basename;

	HANDLE file = CreateFile(filename.c_str(), GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, 0, NULL);
	if(file == INVALID_HANDLE_VALUE) {
		// user specific symbols file does not exists, try the built-in one in Program files
		// try C:\program files (x86) first
		wchar_t path[MAX_PATH];
		HRESULT result = ::SHGetFolderPathW(NULL, CSIDL_PROGRAM_FILESX86, NULL, 0, path);
		if(result != S_OK) // failed, fall back to C:\program files
			result = ::SHGetFolderPathW(NULL, CSIDL_PROGRAM_FILES, NULL, 0, path);
		if(result == S_OK) { // program files folder is found
			filename = path;
			filename += L"\\ChewingTextService\\Dictionary";
			filename += basename;
		}
		file = CreateFile(filename.c_str(), GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, 0, NULL);
	}
	if(file != INVALID_HANDLE_VALUE) {
		DWORD size = GetFileSize(file, NULL);
		char* buf = new char[size+1];
		DWORD rsize;
		ReadFile(file, buf, size, &rsize, NULL);
		CloseHandle(file);
		buf[size] = 0;
		std::wstring wstr = utf8ToUtf16(buf);
		delete []buf;
		::SetDlgItemTextW(hwnd_, IDC_EDIT, wstr.c_str());
	}
	return PropertyPage::onInitDialog();
}

// virtual
void SymbolsPropertyPage::onOK() {
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
		// make the directory hidden
		if(attributes != INVALID_FILE_ATTRIBUTES && (attributes & FILE_ATTRIBUTE_HIDDEN) == 0)
			::SetFileAttributesW(userDir_.c_str(), attributes|FILE_ATTRIBUTE_HIDDEN);
	}

	// save current settings
	std::wstring filename = userDir_;
	filename +=  L"\\symbols.dat";
	HANDLE file = CreateFile(filename.c_str(), GENERIC_WRITE, FILE_SHARE_READ, NULL, CREATE_ALWAYS, 0, NULL );
	if( file != INVALID_HANDLE_VALUE ) {
		HWND edit = ::GetDlgItem(hwnd_, IDC_EDIT);
		int len = ::GetWindowTextLengthW(edit) + 1;
		wchar_t* buf = new wchar_t[len];
		len = ::GetWindowText(edit, buf, len);
		buf[len] = 0;
		std::string ustr = utf16ToUtf8(buf);
		delete []buf;

		DWORD wsize;
		WriteFile( file, ustr.c_str(), ustr.length(), &wsize, NULL );
		CloseHandle(file);
	}

	PropertyPage::onOK();
}


} // namespace Chewing
