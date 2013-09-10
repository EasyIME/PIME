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
