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

TypingPage::TypingPage(void):
	Ime::PropertyPage((LPCTSTR)IDD_TYPING) {
}

TypingPage::~TypingPage(void) {
}

LRESULT TypingPage::wndProc(UINT msg, WPARAM wp, LPARAM lp) {
#if 0
	switch(msg) {
	case WM_INITDIALOG: {
			CheckRadioButton(hwnd_, IDC_KB1, IDC_KB9, IDC_KB1 + g_keyboardLayout);

			CheckDlgButton(hwnd_, IDC_SPACESEL, g_spaceAsSelection);
			CheckDlgButton(hwnd_, IDC_ENABLE_SHIFT, g_enableShift);
			CheckDlgButton(hwnd_, IDC_SHIFT_CAPITAL, g_shiftCapital);
			CheckDlgButton(hwnd_, IDC_ADD_PHRASE_FORWARD, g_addPhraseForward);
			CheckDlgButton(hwnd_, IDC_ADV_AFTER_SEL, g_AdvanceAfterSelection);
			CheckDlgButton(hwnd_, IDC_CURSOR_CANDLIST, g_cursorCandList);
			CheckDlgButton(hwnd_, IDC_ENABLE_CAPSLOCK, g_enableCapsLock);
			CheckDlgButton(hwnd_, IDC_SHIFT_FULLSHAPE, g_shiftFullShape);
			CheckDlgButton(hwnd_, IDC_ESC_CLEAN_ALL_BUF, g_escCleanAllBuf);
			CheckDlgButton(hwnd_, IDC_SHIFT_SYMBOL, g_shiftSymbol);
			CheckDlgButton(hwnd_, IDC_CTRL_SYMBOL, g_ctrlSymbol);
			CheckDlgButton(hwnd_, IDC_ENABLE_Simp, g_enableSimp);

			HWND combo = GetDlgItem(hwnd_, IDC_SELKEYS);
			const TCHAR** pselkeys = g_selKeyNames;
			while(*pselkeys)
				ComboBox_AddString(combo, *(pselkeys++));
			ComboBox_SetCurSel(combo, g_selKeyType);
		}
		return TRUE;
	case WM_NOTIFY:
		if(LPNMHDR(lp)->code == PSN_APPLY) {
			for(UINT id = IDC_KB1; id <= IDC_KB9; ++id)	{
				if(IsDlgButtonChecked(hwnd_, id))	{
					g_keyboardLayout = (id - IDC_KB1);
					break;
				}
			}

			g_selKeyType = ComboBox_GetCurSel(GetDlgItem(hwnd_, IDC_SELKEYS));
			if(g_selKeyType < 0)
				g_selKeyType = 0;

			g_spaceAsSelection = IsDlgButtonChecked(hwnd_, IDC_SPACESEL);
			g_enableShift = IsDlgButtonChecked(hwnd_, IDC_ENABLE_SHIFT);
			g_shiftCapital = IsDlgButtonChecked(hwnd_, IDC_SHIFT_CAPITAL);
			g_addPhraseForward = IsDlgButtonChecked(hwnd_, IDC_ADD_PHRASE_FORWARD);
			g_AdvanceAfterSelection = IsDlgButtonChecked(hwnd_, IDC_ADV_AFTER_SEL);
			g_cursorCandList = IsDlgButtonChecked(hwnd_, IDC_CURSOR_CANDLIST);
			g_enableCapsLock = IsDlgButtonChecked(hwnd_, IDC_ENABLE_CAPSLOCK);
			g_shiftFullShape = IsDlgButtonChecked(hwnd_, IDC_SHIFT_FULLSHAPE);
			g_escCleanAllBuf = IsDlgButtonChecked(hwnd_, IDC_ESC_CLEAN_ALL_BUF);
			if (g_chewing!=NULL)
				g_chewing->SetAdvanceAfterSelection((g_AdvanceAfterSelection!=0)?true: false);
			g_shiftSymbol = IsDlgButtonChecked(hwnd_, IDC_SHIFT_SYMBOL);
			g_ctrlSymbol = IsDlgButtonChecked(hwnd_, IDC_CTRL_SYMBOL);
			g_enableSimp = IsDlgButtonChecked(hwnd_, IDC_ENABLE_Simp);

			SetWindowLongPtr(hwnd_, DWLP_MSGRESULT, PSNRET_NOERROR);
			return TRUE;
		}
			break;
	}
#endif
	return PropertyPage::wndProc(msg, wp, lp);
}
