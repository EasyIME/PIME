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
	selKeyWidth_(0),
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
		SIZE selKeySize;
		int lineHeight = 0;
		// the selection key string
		wchar_t selKey[] = L"?. ";
		selKey[0] = selKeys_[i];
		::GetTextExtentPoint32W(hDC, selKey, 3, &selKeySize); // calculate size
		textRect.left = margin_;
		textRect.bottom = textRect.top + selKeySize.cy;
		textRect.right = textRect.left + selKeyWidth_;
		// FIXME: make the color of strings configurable.
		COLORREF oldColor = ::SetTextColor(hDC, RGB(0, 0, 255));
		// paint the selection key
		::ExtTextOut(hDC, textRect.left, textRect.top, ETO_OPAQUE, &textRect, selKey, 3, NULL);
		::SetTextColor(hDC, oldColor);

		// the candidate string
		SIZE candidateSize;
		wstring& item = items_.at(i);
		::GetTextExtentPoint32W(hDC, item.c_str(), item.length(), &candidateSize);
		textRect.left += selKeyWidth_;
		textRect.bottom = textRect.top + candidateSize.cy;
		// paint the candidate string
		::ExtTextOut(hDC, textRect.left, textRect.top, ETO_OPAQUE, &textRect, item.c_str(), item.length(), NULL);

		textRect.top += max(candidateSize.cy, selKeySize.cy);
		textRect.top += spacing_;
	}

	SelectObject(hDC, oldFont);
	EndPaint(hwnd_, &ps);
}

void CandidateWindow::recalculateSize() {
	if(items_.empty()) {
		resize(margin_ * 2, margin_ * 2);
	}

	HDC hDC = ::GetWindowDC(hwnd());
	int height = 0;
	int width = 0;
	selKeyWidth_ = 0;

	HGDIOBJ oldFont = ::SelectObject(hDC, font_);
	vector<wstring>::const_iterator it;
	for(int i = 0, n = items_.size(); i < n; ++i) {
		SIZE selKeySize;
		int lineHeight = 0;
		// the selection key string
		wchar_t selKey[] = L"?. ";
		selKey[0] = selKeys_[i];
		::GetTextExtentPoint32W(hDC, selKey, 3, &selKeySize);
		if(selKeySize.cx > selKeyWidth_)
			selKeyWidth_ = selKeySize.cx;

		// the candidate string
		SIZE candidateSize;
		wstring& item = items_.at(i);
		::GetTextExtentPoint32W(hDC, item.c_str(), item.length(), &candidateSize);
		height += max(candidateSize.cy, selKeySize.cy);
		height += spacing_;

		if(candidateSize.cx > width)
			width = candidateSize.cx;
	}
	width += (margin_ * 2 + selKeyWidth_);
	height += margin_ * 2;
	::SelectObject(hDC, oldFont);
	::ReleaseDC(hwnd(), hDC);
	resize(width, height);
}
