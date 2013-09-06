#include "ImeWindow.h"

using namespace Ime;

ImeWindow::ImeWindow() {
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

	RECT rc;
	workingArea( &rc, hwnd_);
	if( x < rc.left )
		x = rc.left;
	else if( (x + w) > rc.right )
		x = rc.right - w;

	if( y < rc.top )
		y = rc.top;
	else if( (y + h) > rc.bottom )
		y = rc.bottom - h;
	::MoveWindow(hwnd_, x, y, w, h, TRUE);
}

bool ImeWindow::workingArea(RECT* rc, HWND app_wnd) {
	HMONITOR mon = MonitorFromWindow( app_wnd, MONITOR_DEFAULTTONEAREST);
	MONITORINFO mi;
	mi.cbSize = sizeof(mi);
	if( GetMonitorInfo(mon, &mi) )
		*rc = mi.rcWork;
	return true;
}
