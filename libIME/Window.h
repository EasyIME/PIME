// Window.h: interface for the Window class.
//
//////////////////////////////////////////////////////////////////////

#if !defined(AFX_WINDOW_H__86D89A4E_5040_4FF8_B991_0C7D6502119D__INCLUDED_)
#define AFX_WINDOW_H__86D89A4E_5040_4FF8_B991_0C7D6502119D__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000

#include <windows.h>
#include <tchar.h>

namespace Ime {

class Window {
public:

	Window();
	virtual ~Window();

	HWND hwnd(){	return hwnd_;	}

	bool create(HWND parent = HWND_DESKTOP);
	void destroy(void);

	bool isVisible(){ return (bool)IsWindowVisible(hwnd_); }

	bool isWindow(){ return (bool)IsWindow(hwnd_); }

	void show() {
		if( hwnd_ )
			ShowWindow(hwnd_, SW_SHOWNA);
	}

	void hide(){ ShowWindow(hwnd_, SW_HIDE); }

	void refresh()	{	InvalidateRect( hwnd_, NULL, FALSE );	}

	static bool registerClass(HINSTANCE hinstance);

protected:
	static LRESULT _wndProc(HWND hwnd , UINT msg, WPARAM wp , LPARAM lp);
	LRESULT virtual wndProc(UINT msg, WPARAM wp , LPARAM lp);

protected:
	HWND hwnd_;
};

}

#endif // !defined(AFX_WINDOW_H__86D89A4E_5040_4FF8_B991_0C7D6502119D__INCLUDED_)
