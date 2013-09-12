#include "CandidateWindow.h"
#include "DrawUtils.h"
#include "TextService.h"
#include "EditSession.h"

#include <tchar.h>
#include <windows.h>

using namespace Ime;
using namespace std;

void CandidateWindow::updateFont() {
/*
    if (font_size==g_FontSize)
        return;
    
    font_size = g_FontSize;
    if (font != NULL)
        DeleteObject(font);
	font = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
	LOGFONT lf;
	GetObject(font, sizeof(lf), &lf);
	lf.lfHeight = font_size;
	font = CreateFontIndirect(&lf);
*/
}

CandidateWindow::CandidateWindow(TextService* service, EditSession* session):
	fontSize_(16),
	isImmersive_(service->isImmersive()) {

	if(isImmersive_) { // windows 8 app mode
		margin_ = 10;
		spacing_ = 8;
	}
	else { // desktop mode
		margin_ = 5;
		spacing_ = 4;
	}

	font_ = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
	LOGFONT lf;
	GetObject(font_, sizeof(lf), &lf);
	lf.lfHeight = fontSize_;
	lf.lfWeight = FW_NORMAL;
	font_ = CreateFontIndirect(&lf);

	HWND parent;
	if(isImmersive_)
		parent = service->compositionWindow(session);
	else
		parent = HWND_DESKTOP;
	create(parent, WS_POPUP|WS_CLIPCHILDREN, WS_EX_TOOLWINDOW);
}

CandidateWindow::~CandidateWindow(void) {
	::DeleteObject(font_);
}

LRESULT CandidateWindow::wndProc(UINT msg, WPARAM wp , LPARAM lp) {
	switch (msg) {
		case WM_PAINT:
			onPaint(wp, lp);
			break;
		case WM_ERASEBKGND:
			return TRUE;
			break;
		case WM_LBUTTONDOWN:
			onLButtonDown(wp, lp);
			break;
		case WM_MOUSEMOVE:
			onMouseMove(wp, lp);
			break;
		case WM_LBUTTONUP:
			onLButtonUp(wp, lp);
			break;
		case WM_MOUSEACTIVATE:
			return MA_NOACTIVATE;
		default:
			return Window::wndProc(msg, wp, lp);
	}
	return 0;
}

void CandidateWindow::onPaint(WPARAM wp, LPARAM lp) {
	// TODO: check isImmersive_, and draw the window differently
	// in Windows 8 app immersive mode to follow windows 8 UX guidelines

/*
	if (g_isWinLogon)
		return;
*/
	PAINTSTRUCT ps;
	BeginPaint(hwnd_, &ps);
	HDC hDC = ps.hdc;
	HFONT oldFont;
	RECT rc;

    updateFont();
	oldFont = (HFONT)SelectObject(hDC, font_);

	GetClientRect(hwnd_,&rc);
	SetTextColor(hDC, GetSysColor(COLOR_WINDOWTEXT));
	SetBkColor(hDC, GetSysColor(COLOR_WINDOW));

	// draw a flat black border in Windows 8 app immersive mode
	// draw a 3d border in desktop mode
	if(isImmersive_) {
		HPEN pen = ::CreatePen(PS_SOLID, 3, RGB(0, 0, 0));
		HGDIOBJ oldPen = ::SelectObject(hDC, pen);
		::Rectangle(hDC, rc.left, rc.top, rc.right, rc.bottom);
		::SelectObject(hDC, oldPen);
		::DeleteObject(pen);
	}
	else {
		// draw a 3d border in desktop mode
		::FillSolidRect(ps.hdc, rc.left, rc.top, rc.right - rc.left, rc.bottom - rc.top, GetSysColor(COLOR_WINDOW));
		::Draw3DBorder(hDC, &rc, GetSysColor(COLOR_3DFACE), 0);
	}

	RECT textRect = {margin_, margin_, rc.right - margin_, 0};
	vector<wstring>::const_iterator it;
	for(int i = 0, n = items_.size(); i < n; ++i) {
		wstring& item = items_.at(i);
		wchar_t numStr[10];
		wstring line = _itow(i + 1, numStr, 10);
		line += L". ";
		line += item;

		SIZE size;
		::GetTextExtentPoint32W(hDC, line.c_str(), line.length(), &size);
		textRect.bottom = textRect.top + size.cy;
		::ExtTextOut(hDC, textRect.left, textRect.top, ETO_OPAQUE, &textRect, line.c_str(), line.length(), NULL);
		textRect.top = textRect.bottom + spacing_;
	}

	SelectObject(hDC, oldFont);
	EndPaint(hwnd_, &ps);
}

void CandidateWindow::recalculateSize() {
	HDC hDC = ::GetWindowDC(hwnd());
	int height = 0;
	int width = 0;

	HGDIOBJ oldFont = ::SelectObject(hDC, font_);
	vector<wstring>::const_iterator it;
	for(int i = 0, n = items_.size(); i < n; ++i) {
		wstring& item = items_.at(i);
		wchar_t numStr[10];
		wstring line = _itow(i + 1, numStr, 10);
		line += L". ";
		line += item;

		SIZE size;
		::GetTextExtentPoint32W(hDC, line.c_str(), line.length(), &size);
		height += size.cy;
		height += spacing_;

		if(size.cx > width)
			width = size.cx;
	}
	width += margin_ * 2;
	height += margin_ * 2;
	::SelectObject(hDC, oldFont);
	::ReleaseDC(hwnd(), hDC);
	resize(width, height);
}
