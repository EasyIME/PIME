#ifndef KEY_EVENT_H
#define KEY_EVENT_H

#include <Windows.h>

namespace Ime {

class KeyEvent {
public:
	KeyEvent(UINT type = WM_KEYDOWN);
	KeyEvent(WPARAM wParam, LPARAM lParam, UINT type = WM_KEYDOWN);
	~KeyEvent(void);

private:
	UINT type_;
	long keyCode_;
	bool isShiftDown_;
	bool isCtrlDown_;
	bool isAltDown_;
	int repeat_;
};

}

#endif
