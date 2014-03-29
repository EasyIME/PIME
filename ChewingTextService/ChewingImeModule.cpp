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
	config_(windowsVersion()) {

	config_.load(); // load configurations

	// override default location of chewing data directories
	std::wstring env;
	wchar_t path[MAX_PATH];

	HRESULT result;
}

ImeModule::~ImeModule(void) {
}

// virtual
Ime::TextService* ImeModule::createTextService() {
	TextService* service = new Chewing::TextService(this);
	return service;
}

// virtual
bool ImeModule::onConfigure(HWND hwndParent) {
	// launch ChewingPreferences
	std::wstring path = programDir_;
	path += L"\\ChewingPreferences.exe";
	::ShellExecuteW(hwndParent, L"open", path.c_str(), NULL, NULL, SW_SHOWNORMAL);
	return true;
}


} // namespace Chewing
