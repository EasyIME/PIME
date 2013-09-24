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

#include "AboutDialog.h"
#include "Commctrl.h"
#include "resource.h"

namespace Chewing {

AboutDialog::AboutDialog(void): Ime::Dialog() {
	static bool initSysLink = false;
	if(!initSysLink) {
		// we don't link to comctl32.dll directly since Win8 metro seems to block it.
		INITCOMMONCONTROLSEX icc;
		icc.dwSize = sizeof(icc);
		icc.dwICC = ICC_LINK_CLASS;
		// initialize syslink control
		initSysLink = (bool)InitCommonControlsEx(&icc);
	}
}

AboutDialog::~AboutDialog(void) {
}

bool AboutDialog::onInitDialog() {
	return Ime::Dialog::onInitDialog();
}

LRESULT AboutDialog::wndProc(UINT msg, WPARAM wp, LPARAM lp) {
	switch(msg) {
		case WM_NOTIFY: {
			NMHDR* nmhdr = (NMHDR*)lp;
			switch(nmhdr->code) {
				case NM_CLICK:
				case NM_RETURN: {
					if(nmhdr->idFrom == IDC_LGPL || nmhdr->idFrom == IDC_HOMEPAGE) {
						NMLINK* link = (NMLINK*)nmhdr;
						LITEM item = link->item;
						::ShellExecuteW(NULL, L"open", item.szUrl, NULL, NULL, SW_SHOWNORMAL);
					}
					break;
				}
			}
			break;
		}
	}
	return Ime::Dialog::wndProc(msg, wp, lp);
}

} // namespace Chewing
