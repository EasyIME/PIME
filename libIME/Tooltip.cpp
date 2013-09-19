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

#include "Tooltip.h"
#include "DrawUtils.h"

namespace Ime {

Tooltip::Tooltip(void):
	autoDestroy_(true),
	timerId_(0) {
}

Tooltip::~Tooltip(void) {
	if(timerId_)
		KillTimer(hwnd_, timerId_);
}

LRESULT Tooltip::wndProc(UINT msg, WPARAM wp, LPARAM lp) {
	switch(msg) {
	case WM_PAINT: {
			PAINTSTRUCT ps;
			BeginPaint(hwnd_, &ps);
			onPaint(ps);
			EndPaint(hwnd_, &ps);
		}
		break;
	case WM_TIMER:
		hideTip();
		if(autoDestroy_) {
			::DestroyWindow(hwnd_);
		}
		break;
	case WM_NCDESTROY:
		if(autoDestroy_) {
			delete this;
			return 0;
		}
	case WM_MOUSEACTIVATE:
		return MA_NOACTIVATE;
	default:
		return ImeWindow::wndProc(msg, wp, lp);
	}
	return 0;
}

void Tooltip::onPaint(PAINTSTRUCT& ps) {
	int len = text.length();
	RECT rc, textrc = {0};
	GetClientRect(hwnd_, &rc);
	::FillSolidRect(ps.hdc, &rc, ::GetSysColor(COLOR_INFOBK));
	Draw3DBorder(ps.hdc, &rc, GetSysColor(COLOR_BTNFACE), GetSysColor(COLOR_3DDKSHADOW), 1);

	SetBkMode(ps.hdc, TRANSPARENT);
	SetTextColor(ps.hdc, GetSysColor(COLOR_INFOTEXT));
	HGDIOBJ old_font = SelectObject(ps.hdc, GetStockObject(DEFAULT_GUI_FONT));

	SIZE size;
	GetTextExtentPoint32W(ps.hdc, text.c_str(), len, &size);
	rc.top += (rc.bottom - size.cy)/2;
	rc.left += (rc.right - size.cx)/2;
	ExtTextOutW(ps.hdc, rc.left, rc.top, 0, &textrc, text.c_str(), len, NULL);

	SelectObject(ps.hdc, old_font);
}

void Tooltip::showTip(int x, int y, std::wstring tip_text, int duration) {
	text = tip_text;
	SIZE size = {0};
	HDC dc = GetDC(hwnd_);
	HGDIOBJ old_font = SelectObject(dc, GetStockObject(DEFAULT_GUI_FONT));
	GetTextExtentPointW(dc, text.c_str(), text.length(), &size);
	SelectObject(dc, old_font);
	ReleaseDC(hwnd_, dc);

	SetWindowPos(hwnd_, HWND_TOPMOST, x, y, size.cx + 4, size.cy + 4, SWP_NOACTIVATE);
	if(IsWindowVisible(hwnd_))
		InvalidateRect(hwnd_, NULL, TRUE);
	else
		ShowWindow(hwnd_, SW_SHOWNA);
	if(duration > 0) {
		if(timerId_)
			KillTimer(hwnd_, timerId_);
		timerId_ = SetTimer(hwnd_, 1, duration, NULL);
	}
}

void Tooltip::hideTip(void) {
	if(timerId_) {
		KillTimer(hwnd_, timerId_);
		timerId_ = 0;
	}
	hide();
}

} // namespace Ime
