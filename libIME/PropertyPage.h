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
	virtual LRESULT wndProc(UINT msg, WPARAM wp, LPARAM lp);
	virtual void onOK();
	virtual void onCancel();

private:
	LPCTSTR dialogId_;
};

}

#endif
