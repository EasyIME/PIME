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

#include "ImeWindow.h"

namespace Ime {

ImeWindow::ImeWindow(TextService* service):
	textService_(service) {

	if(service->isImmersive()) { // windows 8 app mode
		margin_ = 10;
	}
	else { // desktop mode
		margin_ = 5;
	}

	font_ = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
/*
	LOGFONT lf;
	GetObject(font_, sizeof(lf), &lf);
	lf.lfHeight = fontSize_;
	lf.lfWeight = FW_NORMAL;
	font_ = CreateFontIndirect(&lf);
*/
}

ImeWindow::~ImeWindow(void) {
}

void ImeWindow::onLButtonDown(WPARAM wp, LPARAM lp) {
	oldPos = MAKEPOINTS(lp);
	SetCapture(hwnd_);
}

void ImeWindow::onLButtonUp(WPARAM wp, LPARAM lp) {
	ReleaseCapture();
}

void ImeWindow::onMouseMove(WPARAM wp, LPARAM lp) {
	if(GetCapture() != hwnd_)
		return;
	POINTS pt = MAKEPOINTS(lp);
	RECT rc;
	GetWindowRect(hwnd_, &rc);
	OffsetRect( &rc, (pt.x - oldPos.x), (pt.y - oldPos.y) );
	move(rc.left, rc.top);
}

void ImeWindow::move(int x, int y) {
	int w, h;
	size(&w, &h);
	// ensure that the window does not fall outside of the screen.
	RECT rc = {x, y, x + w, y + h}; // current window rect
	// get the nearest monitor
	HMONITOR monitor = ::MonitorFromRect(&rc, MONITOR_DEFAULTTONEAREST);
	MONITORINFO mi;
	mi.cbSize = sizeof(mi);
	if(GetMonitorInfo(monitor, &mi))
		rc = mi.rcWork;
	if(x < rc.left)
		x = rc.left;
	else if((x + w) > rc.right)
		x = rc.right - w;

	if(y < rc.top)
		y = rc.top;
	else if((y + h) > rc.bottom)
		y = rc.bottom - h;
	::MoveWindow(hwnd_, x, y, w, h, TRUE);
}

void ImeWindow::setFont(HFONT f) {
	if(font_)
		::DeleteObject(font_);
	font_ = f;
	recalculateSize();
	if(isVisible())
		::InvalidateRect(hwnd_, NULL, TRUE);
}

// virtual
void ImeWindow::recalculateSize() {
}

} // namespace Ime

