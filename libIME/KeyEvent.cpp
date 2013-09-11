#include "KeyEvent.h"

using namespace Ime;

KeyEvent::KeyEvent(UINT type, WPARAM wp, LPARAM lp):
	type_(type),
	keyCode_(wp),
	lParam_(lp) {

	if(!::GetKeyboardState(keyStates_)) // get state of all keys
		::memset(keyStates_, 0, sizeof(keyStates_));

	// try to convert the key event to an ASCII character
	WORD result[2] = {0, 0};
	if(::ToAscii(keyCode_, scanCode(), keyStates_, result, 0) == 1)
		charCode_ = (UINT)result[0];
	else
		charCode_ = 0;
}

KeyEvent::KeyEvent(const KeyEvent& other):
	type_(other.type_),
	keyCode_(other.keyCode_),
	charCode_(other.charCode_),
	lParam_(other.lParam_) {

	::memcpy(keyStates_, other.keyStates_, sizeof(keyStates_));
}

KeyEvent::~KeyEvent(void) {
}
