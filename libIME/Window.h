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

#if !defined(AFX_WINDOW_H__86D89A4E_5040_4FF8_B991_0C7D6502119D__INCLUDED_)
#define AFX_WINDOW_H__86D89A4E_5040_4FF8_B991_0C7D6502119D__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000

#include <windows.h>
#include <tchar.h>
#include <map>

namespace Ime {

class Window {
public:

	Window();
	virtual ~Window();

	HWND hwnd(){	return hwnd_;	}

	bool create(HWND parent, DWORD style, DWORD exStyle = 0);
	void destroy(void);

	bool isVisible(){
		return !!IsWindowVisible(hwnd_);
	}

	bool isWindow(){
		return !!IsWindow(hwnd_);
	}

	void size(int* width, int* height) {
		RECT rc;
		rect(&rc);
		*width = (rc.right - rc.left);
		*height = (rc.bottom - rc.top);
	}

	void resize(int width, int height) {
		::SetWindowPos(hwnd_, HWND_TOP, 0, 0, width, height, SWP_NOZORDER|SWP_NOMOVE|SWP_NOACTIVATE);
	}

	void clientRect(RECT* rect) {
		::GetClientRect(hwnd_, rect);
	}

	void rect(RECT* rect) {
		::GetWindowRect(hwnd_, rect);
	}

	void show() {
		if( hwnd_ )
			ShowWindow(hwnd_, SW_SHOWNA);
	}

	void hide(){ ShowWindow(hwnd_, SW_HIDE); }

	void refresh()	{	InvalidateRect( hwnd_, NULL, FALSE );	}

	static bool registerClass(HINSTANCE hinstance);

	static Window* fromHwnd(HWND hwnd) {
		std::map<HWND, Window*>::iterator it = hwndMap_.find(hwnd);
		return it != hwndMap_.end() ? it->second : NULL;
	}

protected:
	static LRESULT _wndProc(HWND hwnd , UINT msg, WPARAM wp , LPARAM lp);
	virtual LRESULT wndProc(UINT msg, WPARAM wp , LPARAM lp);

protected:
	HWND hwnd_;
	static std::map<HWND, Window*> hwndMap_;
};

}

#endif // !defined(AFX_WINDOW_H__86D89A4E_5040_4FF8_B991_0C7D6502119D__INCLUDED_)
