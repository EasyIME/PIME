#pragma once

#include "ImeWindow.h"

namespace Ime {

class CandidateWindow : public ImeWindow {
public:
	CandidateWindow(void);
	~CandidateWindow(void);

	void setFont(HFONT f){	font = f;	}

protected:
	LRESULT wndProc(UINT msg, WPARAM wp , LPARAM lp);
	void onPaint(WPARAM wp, LPARAM lp);

public:
	void getSize(int* w, int* h);
	void updateSize(void);
    void updateFont();

    HFONT font;
    int   font_size;
};

}
