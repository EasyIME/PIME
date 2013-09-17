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

#include "Window.h"

namespace Ime {

static TCHAR g_imeWindowClassName[] = _T("LibImeWindow");
static HINSTANCE g_hinstance = NULL;

std::map<HWND, Window*> Window::hwndMap_;

Window::Window():
	hwnd_(NULL) {
}

Window::~Window() {
	if(hwnd_)
		DestroyWindow(hwnd_);
}

bool Window::create(HWND parent, DWORD style, DWORD exStyle) {
	hwnd_ = CreateWindowEx(exStyle, g_imeWindowClassName, NULL, style,
					0, 0, 0, 0, parent, NULL, g_hinstance, NULL);
	if(hwnd_) {
		// associate this object with the hwnd
		hwndMap_[hwnd_] = this;
		return true;
	}
	return false;
}

void Window::destroy(void) {
	if( hwnd_ )
		DestroyWindow(hwnd_);
	hwnd_ = NULL;
}

// static
LRESULT Window::_wndProc(HWND hwnd , UINT msg, WPARAM wp , LPARAM lp) {
	// get object pointer from the hwnd
	Window* window = (Window*)hwndMap_[hwnd];
	// FIXME: we cannot handle WM_CREATE in Window::wndProc member function
	// because the message is sent before CreateWindow returns, and
	// we do SetWindowLongPtr() only after CreateWindow().
	if(window) {
		LRESULT result = window->wndProc(msg, wp, lp);
		if(msg == WM_NCDESTROY)
			hwndMap_.erase(hwnd);
		return result;
	}
	return ::DefWindowProc(hwnd, msg, wp, lp);
}

LRESULT Window::wndProc(UINT msg, WPARAM wp , LPARAM lp) {
	return ::DefWindowProc(hwnd_, msg, wp, lp);
}

bool Window::registerClass(HINSTANCE hinstance) {

	if(!g_hinstance)
		g_hinstance = hinstance;

	WNDCLASSEX wc;
	wc.cbSize         = sizeof(WNDCLASSEX);
	wc.style          = CS_IME; // FIXME: is this needed?
	wc.lpfnWndProc    = (WNDPROC)Window::_wndProc;
	wc.cbClsExtra     = 0;
	wc.cbWndExtra     = 0;
	wc.hInstance      = hinstance;
	wc.hCursor        = LoadCursor(NULL, IDC_ARROW);
	wc.hIcon          = NULL;
	wc.lpszMenuName   = (LPTSTR)NULL;
	wc.lpszClassName  = g_imeWindowClassName;
	wc.hbrBackground  = NULL;
	wc.hIconSm        = NULL;

	if(!::RegisterClassEx((LPWNDCLASSEX)&wc))
		return false;
	return true;
}

} // namespace Ime
