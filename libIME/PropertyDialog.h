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

#ifndef IME_PROPERTY_DIALOG_H
#define IME_PROPERTY_DIALOG_H

#include <Windows.h>
#include <vector>
#include <Prsht.h>
#include "PropertyPage.h"

namespace Ime {

class PropertyPage;

// Create a property sheet which contains tabbed interface
// for a configuration dialog
// This class should only be used in desktop app mode.
// Otherwise, your IME might be blocked by Windows 8. (not sure?)

class PropertyDialog {
public:
	PropertyDialog(void);
	virtual ~PropertyDialog(void);

	void addPage(PropertyPage* page);
	void removePage(PropertyPage* page);
	INT_PTR showModal(HINSTANCE hInstance, LPCTSTR captionId = 0, LPCTSTR iconId = 0, HWND parent = HWND_DESKTOP, DWORD flags = PSH_NOAPPLYNOW | PSH_USEICONID | PSH_PROPSHEETPAGE);

private:
	std::vector<PropertyPage*> pages_;
};

}

#endif
