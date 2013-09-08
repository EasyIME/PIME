#include "KeyEvent.h"

using namespace Ime;

KeyEvent::KeyEvent(UINT type, WPARAM wp, LPARAM lp):
	type_(type),
	keyCode_(wp),
	lParam_(lp) {
	// try to convert the virtual key to char.
	charCode_ = ::MapVirtualKey((UINT)keyCode_, MAPVK_VK_TO_CHAR);
}

KeyEvent::KeyEvent(const KeyEvent& other):
	type_(other.type_),
	keyCode_(other.keyCode_),
	charCode_(other.charCode_),
	lParam_(other.lParam_) {
}

KeyEvent::~KeyEvent(void) {
}
