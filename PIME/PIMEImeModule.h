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

#ifndef NODE_IME_MODULE_H
#define NODE_IME_MODULE_H

#include <LibIME/ImeModule.h>
#include <string>
#include <json/json.h>

namespace PIME {

class ImeModule : public Ime::ImeModule {
public:
	ImeModule(HMODULE module);
	virtual ~ImeModule(void);

	virtual Ime::TextService* createTextService();

	std::wstring& userDir () {
		return userDir_;
	}

	std::wstring& programDir() {
		return programDir_;
	}

	// called when config dialog needs to be launched
	virtual bool onConfigure(HWND hwndParent, LANGID langid, REFGUID rguidProfile);

	bool loadImeInfo(const std::string&, std::wstring& filePath, Json::Value& content);

public:
	static const wchar_t* ImeModule::backendDirs_[2];

private:
	std::wstring userDir_;
	std::wstring programDir_;
};

}

#endif
