#include "TypingPage.h"
#include "resource.h"

using namespace Chewing;

TypingPage::TypingPage(void):
	Ime::PropertyPage((LPCTSTR)IDD_TYPING) {
}

TypingPage::~TypingPage(void) {
}

LRESULT TypingPage::wndProc(UINT msg, WPARAM wp, LPARAM lp) {

	return FALSE;
}