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

#include "CandidateWindow.h"
#include "DrawUtils.h"
#include "TextService.h"
#include "EditSession.h"

#include <tchar.h>
#include <windows.h>

using namespace std;

namespace Ime {

CandidateWindow::CandidateWindow(TextService* service, EditSession* session):
	ImeWindow(service),
	candPerRow_(1),
	textWidth_(0),
	itemHeight_(0),
	selKeyWidth_(0) {

	HWND parent;
	if(isImmersive())
		parent = service->compositionWindow(session);
	else
		parent = HWND_DESKTOP;
	create(parent, WS_POPUP|WS_CLIPCHILDREN, WS_EX_TOOLWINDOW);
}

CandidateWindow::~CandidateWindow(void) {
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
	PAINTSTRUCT ps;
	BeginPaint(hwnd_, &ps);
	HDC hDC = ps.hdc;
	HFONT oldFont;
	RECT rc;

	oldFont = (HFONT)SelectObject(hDC, font_);

	GetClientRect(hwnd_,&rc);
	SetTextColor(hDC, GetSysColor(COLOR_WINDOWTEXT));
	SetBkColor(hDC, GetSysColor(COLOR_WINDOW));

	// draw a flat black border in Windows 8 app immersive mode
	// draw a 3d border in desktop mode
	if(isImmersive()) {
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

	RECT textRect = {margin_, margin_, rc.right - margin_, margin_ + itemHeight_};
	vector<wstring>::const_iterator it;
	int col = 0;
	for(int i = 0, n = items_.size(); i < n; ++i) {
		SIZE selKeySize;
		int lineHeight = 0;
		// the selection key string
		wchar_t selKey[] = L"?. ";
		selKey[0] = selKeys_[i];
		textRect.right = textRect.left + selKeyWidth_;
		// FIXME: make the color of strings configurable.
		COLORREF oldColor = ::SetTextColor(hDC, RGB(0, 0, 255));
		// paint the selection key
		::ExtTextOut(hDC, textRect.left, textRect.top, ETO_OPAQUE, &textRect, selKey, 3, NULL);
		::SetTextColor(hDC, oldColor); // restore text color
		// paint the candidate string
		SIZE candidateSize;
		wstring& item = items_.at(i);
		textRect.left += selKeyWidth_;
		textRect.right = textRect.left + textWidth_;
		// paint the candidate string
		::ExtTextOut(hDC, textRect.left, textRect.top, ETO_OPAQUE, &textRect, item.c_str(), item.length(), NULL);
		++col; // go to next column
		if(col >= candPerRow_) {
			col = 0;
			textRect.left = margin_;
			textRect.top = textRect.bottom + spacing_;
			textRect.bottom = textRect.top + itemHeight_;
		}
		else {
			textRect.left = textRect.right + spacing_;
		}
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
	textWidth_ = 0;
	itemHeight_ = 0;

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
		if(candidateSize.cx > textWidth_)
			textWidth_ = candidateSize.cx;
		int itemHeight = max(candidateSize.cy, selKeySize.cy);
		if(itemHeight > itemHeight_)
			itemHeight_ = itemHeight;
	}
	::SelectObject(hDC, oldFont);
	::ReleaseDC(hwnd(), hDC);

	if(items_.size() <= candPerRow_) {
		width = items_.size() * (selKeyWidth_ + textWidth_);
		width += spacing_ * (items_.size() - 1);
		width += margin_ * 2;
		height = itemHeight_ + margin_ * 2;
	}
	else {
		width = candPerRow_ * (selKeyWidth_ + textWidth_);
		width += spacing_ * (candPerRow_ - 1);
		width += margin_ * 2;
		int rowCount = items_.size() / candPerRow_;
		if(items_.size() % candPerRow_)
			++rowCount;
		height = itemHeight_ * rowCount + spacing_ * (rowCount - 1) + margin_ * 2;
	}
	resize(width, height);
}

void CandidateWindow::setCandPerRow(int n) {
	if(n != candPerRow_) {
		candPerRow_ = n;
		recalculateSize();
	}
}


} // namespace Ime
