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

namespace Chewing {

TypingPage::TypingPage(Config* config):
	Ime::PropertyPage((LPCTSTR)IDD_TYPING),
	config_(config) {
}

TypingPage::~TypingPage(void) {
}

// virtual
bool TypingPage::onInitDialog() {
	CheckRadioButton(hwnd_, IDC_KB1, IDC_KB9, IDC_KB1 + config_->keyboardLayout);

	CheckDlgButton(hwnd_, IDC_SPACESEL, config_->showCandWithSpaceKey);
	CheckDlgButton(hwnd_, IDC_ENABLE_SHIFT, config_->switchLangWithShift);
	CheckDlgButton(hwnd_, IDC_ADD_PHRASE_FORWARD, config_->addPhraseForward);
	CheckDlgButton(hwnd_, IDC_ADV_AFTER_SEL, config_->advanceAfterSelection);
	CheckDlgButton(hwnd_, IDC_CURSOR_CANDLIST, config_->cursorCandList);
	CheckDlgButton(hwnd_, IDC_ENABLE_CAPSLOCK, config_->enableCapsLock);
	CheckDlgButton(hwnd_, IDC_SHIFT_FULLSHAPE, config_->fullShapeSymbols);
	CheckDlgButton(hwnd_, IDC_ESC_CLEAN_ALL_BUF, config_->escCleanAllBuf);
	CheckDlgButton(hwnd_, IDC_SHIFT_SYMBOL, config_->easySymbolsWithShift);
	CheckDlgButton(hwnd_, IDC_CTRL_SYMBOL, config_->easySymbolsWithCtrl);
	CheckDlgButton(hwnd_, IDC_ENABLE_Simp, config_->outputSimpChinese);

	HWND combo = GetDlgItem(hwnd_, IDC_SELKEYS);
	for(const wchar_t** pselkeys = config_->selKeys; *pselkeys; ++pselkeys)
		ComboBox_AddString(combo, *pselkeys);
	ComboBox_SetCurSel(combo, config_->selKeyType);
	return PropertyPage::onInitDialog();
}

// virtual
void TypingPage::onOK() {
	for(UINT id = IDC_KB1; id <= IDC_KB9; ++id)	{
		if(IsDlgButtonChecked(hwnd_, id))	{
			config_->keyboardLayout = (id - IDC_KB1);
			break;
		}
	}

	config_->selKeyType = ComboBox_GetCurSel(GetDlgItem(hwnd_, IDC_SELKEYS));
	if(config_->selKeyType < 0)
		config_->selKeyType = 0;

	config_->showCandWithSpaceKey = IsDlgButtonChecked(hwnd_, IDC_SPACESEL);
	config_->switchLangWithShift = IsDlgButtonChecked(hwnd_, IDC_ENABLE_SHIFT);
	config_->addPhraseForward = IsDlgButtonChecked(hwnd_, IDC_ADD_PHRASE_FORWARD);
	config_->advanceAfterSelection = IsDlgButtonChecked(hwnd_, IDC_ADV_AFTER_SEL);
	config_->cursorCandList = IsDlgButtonChecked(hwnd_, IDC_CURSOR_CANDLIST);
	config_->enableCapsLock = IsDlgButtonChecked(hwnd_, IDC_ENABLE_CAPSLOCK);
	config_->fullShapeSymbols = IsDlgButtonChecked(hwnd_, IDC_SHIFT_FULLSHAPE);
	config_->escCleanAllBuf = IsDlgButtonChecked(hwnd_, IDC_ESC_CLEAN_ALL_BUF);
	config_->easySymbolsWithShift = IsDlgButtonChecked(hwnd_, IDC_SHIFT_SYMBOL);
	config_->easySymbolsWithCtrl = IsDlgButtonChecked(hwnd_, IDC_CTRL_SYMBOL);
	config_->outputSimpChinese = IsDlgButtonChecked(hwnd_, IDC_ENABLE_Simp);

	config_->save();
	PropertyPage::onOK();
}

} // namespace Chewing
