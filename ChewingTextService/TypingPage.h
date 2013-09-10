#ifndef CHEWING_TYPING_PAGE_H
#define CHEWING_TYPING_PAGE_H

#include <libIME/PropertyPage.h>

namespace Chewing {

class TypingPage : public Ime::PropertyPage {
public:
	TypingPage(void);
	virtual ~TypingPage(void);

protected:
	LRESULT wndProc(UINT msg, WPARAM wp, LPARAM lp);
};

}

#endif
