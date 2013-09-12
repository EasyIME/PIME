#ifndef IME_PROPERTY_DIALOG_H
#define IME_PROPERTY_DIALOG_H

#include <Windows.h>
#include <vector>
#include <Prsht.h>
#include "PropertyPage.h"

namespace Ime {

class PropertyPage;

// Create a property sheet which contains tabbed interface
// for a configuration dialog
// This class should only be used in desktop app mode.
// Otherwise, your IME might be blocked by Windows 8. (not sure?)

class PropertyDialog {
public:
	PropertyDialog(void);
	virtual ~PropertyDialog(void);

	void addPage(PropertyPage* page);
	void removePage(PropertyPage* page);
	INT_PTR showModal(HINSTANCE hInstance, LPCTSTR captionId = 0, LPCTSTR iconId = 0, HWND parent = HWND_DESKTOP, DWORD flags = PSH_NOAPPLYNOW | PSH_USEICONID | PSH_PROPSHEETPAGE);

private:
	std::vector<PropertyPage*> pages_;
};

}

#endif
