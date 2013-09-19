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

#include "KeyEvent.h"

namespace Ime {

KeyEvent::KeyEvent(UINT type, WPARAM wp, LPARAM lp):
	type_(type),
	keyCode_(wp),
	lParam_(lp) {

	if(!::GetKeyboardState(keyStates_)) // get state of all keys
		::memset(keyStates_, 0, sizeof(keyStates_));

	// try to convert the key event to an ASCII character
	// ToAscii API tries to convert Ctrl + printable characters to
	// ASCII 0x00 - 0x31 non-printable escape characters, which we don't want
	// So here is a hack: pretend that Ctrl key is not pressed
	WORD result[2] = {0, 0};
	BYTE ctrlState = keyStates_[VK_CONTROL];
	keyStates_[VK_CONTROL] = 0;
	if(::ToAscii(keyCode_, scanCode(), keyStates_, result, 0) == 1)
		charCode_ = (UINT)result[0];
	else
		charCode_ = 0;
	keyStates_[VK_CONTROL] = ctrlState;
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

} // namespace Ime
