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

#include "MessageWindow.h"
#include "TextService.h"
#include "DrawUtils.h"

namespace Ime {

MessageWindow::MessageWindow(TextService* service, EditSession* session):
	textService_(service) {
	HWND parent;
	if(session && service->isImmersive())
		parent = service->compositionWindow(session);
	else
		parent = HWND_DESKTOP;
	create(parent, WS_POPUP|WS_CLIPCHILDREN, WS_EX_TOOLWINDOW);
}

MessageWindow::~MessageWindow(void) {
}

void MessageWindow::setText(std::wstring text) {
	// FIXMEl: use different appearance under immersive mode
	int margin = 4;
	text_ = text;
	SIZE size = {0};
	HDC dc = GetDC(hwnd_);
	HGDIOBJ old_font = SelectObject(dc, GetStockObject(DEFAULT_GUI_FONT));
	GetTextExtentPointW(dc, text_.c_str(), text_.length(), &size);
	SelectObject(dc, old_font);
	ReleaseDC(hwnd_, dc);

	SetWindowPos(hwnd_, HWND_TOPMOST, 0, 0,
		size.cx + margin * 2, size.cy + margin * 2, SWP_NOACTIVATE|SWP_NOMOVE);
	if(IsWindowVisible(hwnd_))
		InvalidateRect(hwnd_, NULL, TRUE);
}


LRESULT MessageWindow::wndProc(UINT msg, WPARAM wp, LPARAM lp) {
	switch(msg) {
	case WM_PAINT: {
			PAINTSTRUCT ps;
			BeginPaint(hwnd_, &ps);
			onPaint(ps);
			EndPaint(hwnd_, &ps);
		}
		break;
	case WM_MOUSEACTIVATE:
		return MA_NOACTIVATE;
	default:
		return ImeWindow::wndProc(msg, wp, lp);
	}
	return 0;
}

void MessageWindow::onPaint(PAINTSTRUCT& ps) {
	int len = text_.length();
	RECT rc, textrc = {0};
	GetClientRect(hwnd_, &rc);
	::FillSolidRect(ps.hdc, &rc, ::GetSysColor(COLOR_INFOBK));
	Draw3DBorder(ps.hdc, &rc, GetSysColor(COLOR_BTNFACE), GetSysColor(COLOR_3DDKSHADOW), 1);

	SetBkMode(ps.hdc, TRANSPARENT);
	SetTextColor(ps.hdc, GetSysColor(COLOR_INFOTEXT));
	HGDIOBJ old_font = SelectObject(ps.hdc, GetStockObject(DEFAULT_GUI_FONT));

	SIZE size;
	GetTextExtentPoint32W(ps.hdc, text_.c_str(), len, &size);
	rc.top += (rc.bottom - size.cy)/2;
	rc.left += (rc.right - size.cx)/2;
	ExtTextOutW(ps.hdc, rc.left, rc.top, 0, &textrc, text_.c_str(), len, NULL);

	SelectObject(ps.hdc, old_font);
}

} // namespace Ime
