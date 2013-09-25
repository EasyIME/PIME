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

#ifndef CHEWING_IME_MODULE_H
#define CHEWING_IME_MODULE_H

#include <LibIME/ImeModule.h>
#include "ChewingConfig.h"
#include <string>

namespace Chewing {

class ImeModule : public Ime::ImeModule {
public:
	ImeModule(HMODULE module);
	virtual ~ImeModule(void);

	virtual Ime::TextService* createTextService();

	Config& config() {
		return config_;
	}

	std::wstring& userDir () {
		return userDir_;
	}

	std::wstring& programDir() {
		return programDir_;
	}

	// called when config dialog needs to be launched
	virtual bool onConfigure(HWND hwndParent);

private:
	Config config_;
	std::wstring userDir_;
	std::wstring programDir_;
};

}

#endif
