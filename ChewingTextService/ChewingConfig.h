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

	static const char* selKeys[];
};

}

#endif
