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

#include "UiPropertyPage.h"
#include "resource.h"
#include <Commctrl.h>
#include <windowsx.h>

namespace Chewing {

UiPropertyPage::UiPropertyPage(Config* config):
	Ime::PropertyPage((LPCTSTR)IDD_UI),
	config_(config) {
}

UiPropertyPage::~UiPropertyPage(void) {
}

// virtual
bool UiPropertyPage::onInitDialog() {
	HWND spin = GetDlgItem(hwnd_, IDC_FONT_SIZE_SPIN);
	::SendMessage(spin, UDM_SETRANGE32, 4, 64);
	::SendMessage(spin, UDM_SETPOS, 0, 
                    (LPARAM) MAKELONG ((short) config_->fontSize , 0));

	CheckDlgButton(hwnd_, IDC_PHRASE_MARK, config_->phraseMark);
	// CheckDlgButton(hwnd_, IDC_BLOCK_CURSOR, config_->ColoredCompCursor);
	CheckDlgButton(hwnd_, IDC_COLOR_CANDIDATE, config_->colorCandWnd);

	spin = GetDlgItem(hwnd_, IDC_CAND_PER_ROW_SPIN);
	::SendMessage(spin, UDM_SETRANGE32, 1, 10);
	::SendMessage(spin, UDM_SETPOS, 0, 
                    (LPARAM) MAKELONG ((short) config_->candPerRow , 0));

	spin = GetDlgItem(hwnd_, IDC_CAND_PER_PAGE_SPIN);
	::SendMessage(spin, UDM_SETRANGE32, 7, 10);
	::SendMessage(spin, UDM_SETPOS, 0, 
                    (LPARAM) MAKELONG ((short) config_->candPerPage , 0));
	return PropertyPage::onInitDialog();
}

// virtual
void UiPropertyPage::onOK() {
	HWND spin = GetDlgItem(hwnd_, IDC_FONT_SIZE_SPIN);
	int tFontSize = (int)::SendMessage(spin, UDM_GETPOS, 0, 0);
	if(tFontSize < 4)     tFontSize = 4;
	if(tFontSize > 64)	tFontSize = 64;
	config_->fontSize = tFontSize;

	config_->phraseMark = IsDlgButtonChecked(hwnd_, IDC_PHRASE_MARK);
	// config_->coloredCompCursor = IsDlgButtonChecked(hwnd_, IDC_BLOCK_CURSOR);
	config_->colorCandWnd = IsDlgButtonChecked(hwnd_, IDC_COLOR_CANDIDATE);

	spin = GetDlgItem(hwnd_, IDC_CAND_PER_ROW_SPIN);
	config_->candPerRow = (DWORD)::SendMessage(spin, UDM_GETPOS, 0, 0);
	if(config_->candPerRow < 1)	config_->candPerRow = 1;
	if(config_->candPerRow > 10)	config_->candPerRow = 10;

	spin = GetDlgItem(hwnd_, IDC_CAND_PER_PAGE_SPIN);
	config_->candPerPage = (int)::SendMessage(spin, UDM_GETPOS, 0, 0);
	PropertyPage::onOK();
}

} // namespace Chewing
