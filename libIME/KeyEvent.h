#ifndef IME_KEY_EVENT_H
#define IME_KEY_EVENT_H

#include <Windows.h>

namespace Ime {

class KeyEvent {
public:
	KeyEvent(UINT type, WPARAM wp, LPARAM lp);
	KeyEvent(const KeyEvent& other);
	~KeyEvent(void);

	UINT type() {
		return type_;
	}

	UINT keyCode() {
		return keyCode_;
	}

	UINT charCode() {
		return charCode_;
	}

	bool isChar() {
		return (charCode_ != 0);
	}

	LPARAM lParam() {
		return lParam_;
	}

	unsigned short repeatCount() {
		// bits 0-15
		return (unsigned short)(lParam_ & 0xffff);
	}

	unsigned char scanCode() {
		// bits 16-23
		return (unsigned char)(lParam_ & 0xff0000);
	}

	bool isExtended() {
		// bit 24
		return (lParam_ & (1<<24)) != 0;
	}

private:
	KeyEvent(void) {}

private:
	UINT type_;
	UINT keyCode_;
	UINT charCode_;
	LPARAM lParam_;
};

class KeyState {
public:
	KeyState(int keyCode, bool sync = true) {
		state_ = ::GetKeyState(keyCode);
	}

	bool isDown() {
		return ((state_ & (1 << 16)) != 0);
	}

	bool isToggled() {
		return ((state_ & 1) != 0);
	}

	short state() {
		return state_;
	}

private:
	short state_;
};

}

#endif
