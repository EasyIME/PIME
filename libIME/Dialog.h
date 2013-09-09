#ifndef IME_DIALOG_H
#define IME_DIALOG_H

#include "Window.h"
#include <windows.h>

namespace Ime {

class Dialog : public Window {
public:
	Dialog(void);
	virtual ~Dialog(void);

	bool Create(HINSTANCE hinstance, UINT dialogId, HWND parent = HWND_DESKTOP); // modaless
	UINT showModal(HINSTANCE hinstance, UINT dialogId, HWND parent = HWND_DESKTOP); // modal

	void endDialog(UINT result) {
		::EndDialog(hwnd_, result);
	}

protected:
	static INT_PTR CALLBACK _dlgProc(HWND hwnd , UINT msg, WPARAM wp , LPARAM lp);
	virtual LRESULT wndProc(UINT msg, WPARAM wp , LPARAM lp);

private:
};

}

#endif
