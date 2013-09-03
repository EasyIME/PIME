#include "KeyEvent.h"

using namespace Ime;

KeyEvent::KeyEvent(WPARAM wParam, LPARAM lParam, UINT type) {
}

KeyEvent::KeyEvent(UINT type):
	type_(type),
	keyCode_(0),
	isShiftDown_(false),
	isCtrlDown_(false),
	isAltDown_(false),
	repeat_(0) {
}

KeyEvent::~KeyEvent(void) {
}
