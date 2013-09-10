#include "PropertyPage.h"

using namespace Ime;

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
