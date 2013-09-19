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

// FIXME: this class is taken from old ChewingIME and the 
// interface really needs some redesign. It's not ready for use yet.

#ifndef IME_TOOLTIP_H
#define IME_TOOLTIP_H

#include "imewindow.h"
#include <string>

namespace Ime {

class Tooltip :	public ImeWindow {
public:
	Tooltip(void);
	virtual ~Tooltip(void);
	void showTip(int x, int y, std::wstring tip_text, int duration = 0);
	void hideTip(void);
	void setAutoDestroy(bool autoDestroy = true) {
		autoDestroy_ = autoDestroy;
	}

protected:
	LRESULT wndProc(UINT msg, WPARAM wp, LPARAM lp);
	void onPaint(PAINTSTRUCT& ps);

private:
	UINT timerId_;
	std::wstring text;
	bool autoDestroy_;
};

}

#endif
