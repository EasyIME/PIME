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

#include "TypingPage.h"
#include "resource.h"
#include <WindowsX.h>

using namespace Chewing;

TypingPage::TypingPage(Config* config):
	Ime::PropertyPage((LPCTSTR)IDD_TYPING),
	config_(config) {
}

TypingPage::~TypingPage(void) {
}

LRESULT TypingPage::wndProc(UINT msg, WPARAM wp, LPARAM lp) {
	switch(msg) {
	case WM_INITDIALOG: {
			CheckRadioButton(hwnd_, IDC_KB1, IDC_KB9, IDC_KB1 + config_->keyboardLayout);

			CheckDlgButton(hwnd_, IDC_SPACESEL, config_->spaceAsSelection);
			CheckDlgButton(hwnd_, IDC_ENABLE_SHIFT, config_->enableShift);
			CheckDlgButton(hwnd_, IDC_SHIFT_CAPITAL, config_->shiftCapital);
			CheckDlgButton(hwnd_, IDC_ADD_PHRASE_FORWARD, config_->addPhraseForward);
			CheckDlgButton(hwnd_, IDC_ADV_AFTER_SEL, config_->advanceAfterSelection);
			CheckDlgButton(hwnd_, IDC_CURSOR_CANDLIST, config_->cursorCandList);
			CheckDlgButton(hwnd_, IDC_ENABLE_CAPSLOCK, config_->enableCapsLock);
			CheckDlgButton(hwnd_, IDC_SHIFT_FULLSHAPE, config_->shiftFullShape);
			CheckDlgButton(hwnd_, IDC_ESC_CLEAN_ALL_BUF, config_->escCleanAllBuf);
			CheckDlgButton(hwnd_, IDC_SHIFT_SYMBOL, config_->shiftSymbol);
			CheckDlgButton(hwnd_, IDC_CTRL_SYMBOL, config_->ctrlSymbol);
			CheckDlgButton(hwnd_, IDC_ENABLE_Simp, config_->enableSimp);

			HWND combo = GetDlgItem(hwnd_, IDC_SELKEYS);
			// const TCHAR** pselkeys = config_->selKeyNames;
			// while(*pselkeys)
			//	ComboBox_AddString(combo, *(pselkeys++));
			// ComboBox_SetCurSel(combo, config_->selKeyType);
		}
		return TRUE;
	case WM_NOTIFY:
		if(LPNMHDR(lp)->code == PSN_APPLY) {
			for(UINT id = IDC_KB1; id <= IDC_KB9; ++id)	{
				if(IsDlgButtonChecked(hwnd_, id))	{
					config_->keyboardLayout = (id - IDC_KB1);
					break;
				}
			}

			config_->selKeyType = ComboBox_GetCurSel(GetDlgItem(hwnd_, IDC_SELKEYS));
			if(config_->selKeyType < 0)
				config_->selKeyType = 0;

			config_->spaceAsSelection = IsDlgButtonChecked(hwnd_, IDC_SPACESEL);
			config_->enableShift = IsDlgButtonChecked(hwnd_, IDC_ENABLE_SHIFT);
			config_->shiftCapital = IsDlgButtonChecked(hwnd_, IDC_SHIFT_CAPITAL);
			config_->addPhraseForward = IsDlgButtonChecked(hwnd_, IDC_ADD_PHRASE_FORWARD);
			config_->advanceAfterSelection = IsDlgButtonChecked(hwnd_, IDC_ADV_AFTER_SEL);
			config_->cursorCandList = IsDlgButtonChecked(hwnd_, IDC_CURSOR_CANDLIST);
			config_->enableCapsLock = IsDlgButtonChecked(hwnd_, IDC_ENABLE_CAPSLOCK);
			config_->shiftFullShape = IsDlgButtonChecked(hwnd_, IDC_SHIFT_FULLSHAPE);
			config_->escCleanAllBuf = IsDlgButtonChecked(hwnd_, IDC_ESC_CLEAN_ALL_BUF);
			// if (config_->chewing!=NULL)
			// 	config_->chewing->SetAdvanceAfterSelection((config_->AdvanceAfterSelection!=0)?true: false);
			config_->shiftSymbol = IsDlgButtonChecked(hwnd_, IDC_SHIFT_SYMBOL);
			config_->ctrlSymbol = IsDlgButtonChecked(hwnd_, IDC_CTRL_SYMBOL);
			config_->enableSimp = IsDlgButtonChecked(hwnd_, IDC_ENABLE_Simp);

			SetWindowLongPtr(hwnd_, DWLP_MSGRESULT, PSNRET_NOERROR);
			return TRUE;
		}
	}
	return PropertyPage::wndProc(msg, wp, lp);
}
