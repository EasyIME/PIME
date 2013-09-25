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

#ifndef IME_IME_WINDOW_H
#define IME_IME_WINDOW_H

#include <windows.h>
#include "window.h"
#include "TextService.h"

namespace Ime {

class TextService;

// base class for all IME windows (candidate, tooltip, ...etc)
class ImeWindow: public Window {
public:
	ImeWindow(TextService* service);
	virtual ~ImeWindow(void);
	void move(int x, int y);
	bool isImmersive() {
		return textService_->isImmersive();
	}

	void setFont(HFONT f);
	virtual void recalculateSize();

protected:
	void onLButtonDown(WPARAM wp, LPARAM lp);
	void onLButtonUp(WPARAM wp, LPARAM lp);
	void onMouseMove(WPARAM wp, LPARAM lp);

protected:
	TextService* textService_;
	POINTS oldPos;
	HFONT font_;
	int margin_;
};

}

#endif
