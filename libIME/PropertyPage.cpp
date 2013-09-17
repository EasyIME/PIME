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

#include "PropertyPage.h"

namespace Ime {

PropertyPage::PropertyPage(LPCTSTR dialogId):
	Dialog(),
	dialogId_(dialogId) {
}

PropertyPage::~PropertyPage(void) {
}

void PropertyPage::setup(PROPSHEETPAGE& page) {
	memset(&page, 0, sizeof(PROPSHEETPAGE));
	page.dwSize = sizeof(PROPSHEETPAGE);
	page.dwFlags = PSP_DEFAULT;

	page.pszTemplate = (LPCTSTR)dialogId_;
	page.pfnDlgProc  = (DLGPROC)_dlgProc;
	page.lParam = (LPARAM)this;
}

// static
INT_PTR CALLBACK PropertyPage::_dlgProc(HWND hwnd , UINT msg, WPARAM wp , LPARAM lp) {
	if(msg == WM_INITDIALOG) {
		PROPSHEETPAGE* page = (PROPSHEETPAGE*)lp;
		PropertyPage* pThis = (PropertyPage*)page->lParam;
		pThis->hwnd_ = hwnd;
		hwndMap_[hwnd] = pThis;
		pThis->wndProc(msg, wp, lp);
		return TRUE;
	}
	return Dialog::_dlgProc(hwnd, msg, wp, lp);
}

// virtual
LRESULT PropertyPage::wndProc(UINT msg, WPARAM wp, LPARAM lp) {
	switch(msg) {
	case WM_NOTIFY:
		switch(LPNMHDR(lp)->code) {
		case PSN_APPLY:
			onOK();
			return TRUE;
		case PSN_QUERYCANCEL:
			onCancel();
			return TRUE;
		}
	}
	return Dialog::wndProc(msg, wp, lp);
}

// virtual
void PropertyPage::onOK() {
	::SetWindowLongPtr(hwnd_, DWLP_MSGRESULT, PSNRET_NOERROR);
}

// virtual
void PropertyPage::onCancel() {
	::SetWindowLongPtr(hwnd_, DWLP_MSGRESULT, PSNRET_NOERROR);
}

} // namespace Ime
