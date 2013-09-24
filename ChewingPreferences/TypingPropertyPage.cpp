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

#include "TypingPropertyPage.h"
#include "resource.h"
#include <WindowsX.h>

namespace Chewing {

TypingPropertyPage::TypingPropertyPage(Config* config):
	Ime::PropertyPage((LPCTSTR)IDD_TYPING),
	config_(config) {
}

TypingPropertyPage::~TypingPropertyPage(void) {
}

// virtual
bool TypingPropertyPage::onInitDialog() {

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
	CheckDlgButton(hwnd_, IDC_SHIFT_UPPERCASE, config_->upperCaseWithShift);
	CheckDlgButton(hwnd_, IDC_ENABLE_Simp, config_->outputSimpChinese);
	CheckDlgButton(hwnd_, IDC_DEFAULT_ENG, config_->defaultEnglish);
	CheckDlgButton(hwnd_, IDC_DEFAULT_FS, config_->defaultFullSpace);

	HWND combo = GetDlgItem(hwnd_, IDC_SELKEYS);
	for(const wchar_t** pselkeys = config_->selKeys; *pselkeys; ++pselkeys)
		ComboBox_AddString(combo, *pselkeys);
	ComboBox_SetCurSel(combo, config_->selKeyType);
	return PropertyPage::onInitDialog();
}

// virtual
void TypingPropertyPage::onOK() {


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
	config_->upperCaseWithShift = IsDlgButtonChecked(hwnd_, IDC_SHIFT_UPPERCASE);
	config_->outputSimpChinese = IsDlgButtonChecked(hwnd_, IDC_ENABLE_Simp);
	config_->defaultEnglish = IsDlgButtonChecked(hwnd_, IDC_DEFAULT_ENG);
	config_->defaultFullSpace = IsDlgButtonChecked(hwnd_, IDC_DEFAULT_FS);
	PropertyPage::onOK();
}

} // namespace Chewing
