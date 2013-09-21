#include "AboutDialog.h"
#include "Commctrl.h"
#include "resource.h"

namespace Chewing {

typedef BOOL (*InitCommonControlsExFunc)(const LPINITCOMMONCONTROLSEX lpInitCtrls);
static InitCommonControlsExFunc pInitCommonControlsEx = NULL;
static HMODULE comctl = NULL;

AboutDialog::AboutDialog(void): Ime::Dialog() {
	// we don't link to comctl32.dll directly since Win8 metro seems to block it.
	if(!comctl) {
		comctl = ::LoadLibraryW(L"Comctl32.dll");
		if(comctl) {
			pInitCommonControlsEx = (InitCommonControlsExFunc)::GetProcAddress(comctl, "InitCommonControlsEx");
			INITCOMMONCONTROLSEX icc;
			icc.dwSize = sizeof(icc);
			icc.dwICC = ICC_LINK_CLASS;
			// initialize syslink control
			::InitCommonControlsEx(&icc);
		}
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
