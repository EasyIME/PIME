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

#ifndef CHEWING_CONFIG_H
#define CHEWING_CONFIG_H

#include <Windows.h>

namespace Chewing {

class Config {
public:
	Config(void);
	~Config(void);

	void load();
	void save();

public:
	// Configuration
	DWORD keyboardLayout;
	DWORD candPerRow;
	DWORD defaultEnglish;
	DWORD defaultFullSpace;
	DWORD spaceAsSelection;
	DWORD enableShift;
	DWORD shiftCapital;
	DWORD enableSimp;
	DWORD addPhraseForward;
	DWORD hideStatusWnd;
	DWORD fixCompWnd;
	DWORD colorCandWnd;
	DWORD coloredCompCursor;
	DWORD advanceAfterSelection;
	DWORD fontSize;
	DWORD selKeyType;
	//DWORD selAreaLen;
	DWORD candPerPage;
	DWORD cursorCandList;
	DWORD enableCapsLock;
	DWORD shiftFullShape;
	DWORD phraseMark;
	DWORD escCleanAllBuf;
	DWORD shiftSymbol;
	DWORD ctrlSymbol;
	DWORD checkNewVersion;	// Enable update notifier

	static const wchar_t* selKeys[];
};

}

#endif
