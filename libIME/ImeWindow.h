#pragma once

#include <windows.h>
#include "window.h"

namespace Ime {

// base class for all IME windows (candidate, tooltip, ...etc)
class ImeWindow: public Window {
public:
	ImeWindow();
	virtual ~ImeWindow(void);
	void move(int x, int y);

	static bool workingArea(RECT* rc, HWND app_wnd);

protected:
	void onLButtonDown(WPARAM wp, LPARAM lp);
	void onLButtonUp(WPARAM wp, LPARAM lp);
	void onMouseMove(WPARAM wp, LPARAM lp);

protected:
	POINTS oldPos;
};

}
