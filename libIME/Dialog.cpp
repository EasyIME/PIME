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

#include "Dialog.h"

using namespace Ime;

Dialog::Dialog(void):
	Window() {
}

Dialog::~Dialog(void) {
}

bool Dialog::Create(HINSTANCE hinstance, UINT dialogId, HWND parent) { // modaless
	hwnd_ = ::CreateDialogParam(hinstance, LPCTSTR(dialogId), parent, _dlgProc, (LPARAM)this);
	return hwnd_ != NULL;
}

UINT Dialog::showModal(HINSTANCE hinstance, UINT dialogId, HWND parent) { // modal
	return ::DialogBoxParam(hinstance, LPCTSTR(dialogId), parent, _dlgProc, (LPARAM)this);
}

// static
INT_PTR CALLBACK Dialog::_dlgProc(HWND hwnd , UINT msg, WPARAM wp , LPARAM lp) {
	Dialog* pThis = (Dialog*)hwndMap_[hwnd];
	if(pThis) {
		INT_PTR result = pThis->wndProc(msg, wp, lp);
		if(msg == WM_NCDESTROY)
			hwndMap_.erase(hwnd);
		return result;
	}
	else {
		if(msg == WM_INITDIALOG) {
			Dialog* pThis = (Dialog*)lp;
			pThis->hwnd_ = hwnd;
			hwndMap_[hwnd] = pThis;
			pThis->wndProc(msg, wp, lp);
			return TRUE;
		}
	}
	return FALSE;
}

// virtual
LRESULT Dialog::wndProc(UINT msg, WPARAM wp , LPARAM lp) {
	switch(msg) {
	case WM_COMMAND:
		if(wp == IDOK || wp == IDCANCEL)
			endDialog(wp);
		break;
	}
	return FALSE;
}
