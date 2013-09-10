#ifndef IME_PROPERTY_DIALOG_H
#define IME_PROPERTY_DIALOG_H

#include <Windows.h>
#include <vector>
#include <Prsht.h>
#include "PropertyPage.h"

namespace Ime {

class PropertyPage;

class PropertyDialog {
public:
	PropertyDialog(void);
	virtual ~PropertyDialog(void);

	void addPage(PropertyPage* page);
	void removePage(PropertyPage* page);
	INT_PTR showModal(HINSTANCE hInstance, LPCTSTR captionId = 0, LPCTSTR iconId = 0, DWORD flags = PSH_NOAPPLYNOW | PSH_USEICONID | PSH_PROPSHEETPAGE, HWND parent = HWND_DESKTOP);

private:
	std::vector<PropertyPage*> pages_;
};

}

#endif
