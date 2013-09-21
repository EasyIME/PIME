#ifndef CHEWING_ABOUT_DIALOG_H
#define CHEWING_ABOUT_DIALOG_H
#pragma once

#include <libIME\Dialog.h>

namespace Chewing {

class AboutDialog :	public Ime::Dialog {
public:
	AboutDialog(void);
	virtual ~AboutDialog(void);

protected:
	bool onInitDialog();
	LRESULT wndProc(UINT msg, WPARAM wp, LPARAM lp);
};

}

#endif
