#ifndef IME_PROPERTY_PAGE_H
#define IME_PROPERTY_PAGE_H

#include "Dialog.h"
#include <Prsht.h>

namespace Ime {

class PropertyPage: public Dialog {
public:
	friend class PropertyDialog;

	PropertyPage(LPCTSTR dialogId);
	virtual ~PropertyPage(void);

protected:
	void setup(PROPSHEETPAGE& page);
	static INT_PTR CALLBACK _dlgProc(HWND hwnd , UINT msg, WPARAM wp , LPARAM lp);

private:
	LPCTSTR dialogId_;
};

}

#endif
