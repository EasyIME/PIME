#include "KeyboardPropertyPage.h"
#include "resource.h"
#include <WindowsX.h>

namespace Chewing {

KeyboardPropertyPage::KeyboardPropertyPage(Config* config):
	Ime::PropertyPage((LPCTSTR)IDD_KBLAYOUT),
	config_(config) {
}

KeyboardPropertyPage::~KeyboardPropertyPage(void) {
}


// virtual
bool KeyboardPropertyPage::onInitDialog() {
	CheckRadioButton(hwnd_, IDC_KB1, IDC_KB9, IDC_KB1 + config_->keyboardLayout);

	return PropertyPage::onInitDialog();
}

// virtual
void KeyboardPropertyPage::onOK() {
	for(UINT id = IDC_KB1; id <= IDC_KB9; ++id)	{
		if(IsDlgButtonChecked(hwnd_, id))	{
			config_->keyboardLayout = (id - IDC_KB1);
			break;
		}
	}
	PropertyPage::onOK();
}


} // namespace Chewing
