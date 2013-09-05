#include "CandidateWindow.h"
#include "DrawUtils.h"

#include <tchar.h>
#include <windows.h>

using namespace Ime;

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

CandidateWindow::CandidateWindow() {
    font_size = 0;
    updateFont();
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

static void _DecideCandStringcolor(DWORD &CandIndex, DWORD &CandBody, BOOL bCandPage) {
#if 0
#define RGB_CAND_CHAR_IDX       RGB(230, 20, 20)
#define RGB_CAND_CHAR_BODY      RGB(20, 20, 230)
#define RGB_CAND_BLACK          RGB(0, 0, 0)

    CandIndex = CandBody = RGB_CAND_BLACK;
    if(g_ColorCandWnd==true && bCandPage==FALSE) {
        CandIndex = RGB_CAND_CHAR_IDX;
        CandBody = RGB_CAND_CHAR_BODY;
    }
#endif
}

void CandidateWindow::onPaint(WPARAM wp, LPARAM lp) {
/*
	if (g_isWinLogon)
		return;
	IMCLock imc(hIMC);
	CandList* candList = imc.getCandList();
	if(!candList)
		return;
*/
	PAINTSTRUCT ps;
	BeginPaint(hwnd_, &ps);
	HDC hDC = ps.hdc;
	HFONT oldFont;
	RECT rc;

    updateFont();
	oldFont = (HFONT)SelectObject(hDC, font);
	GetClientRect(hwnd_,&rc);
	SetTextColor(hDC, GetSysColor(COLOR_WINDOWTEXT));
	SetBkColor(hDC, GetSysColor(COLOR_WINDOW));

	FillSolidRect(ps.hdc, rc.left, rc.top, rc.right - rc.left, rc.bottom - rc.top, GetSysColor(COLOR_WINDOW));

#if 0
	int items_per_row =  g_candPerRow;

	RECT cand_rc;	cand_rc.left = 1;	cand_rc.top = 1;	cand_rc.right = 1;

	int pageEnd = candList->getPageStart() + candList->getPageSize();
	if(pageEnd > candList->getTotalCount())
		pageEnd = candList->getTotalCount();
	int numCand = pageEnd - candList->getPageStart();
	int num = 0;

	int selkey_w = 0;
    DWORD   colorIdx, colorBody;
	SIZE candsz;
	GetTextExtentPoint32W(hDC, L"m.", 2, &candsz);
	selkey_w = candsz.cx;

	for(int i = candList->getPageStart(); i <= pageEnd; ++i) {
		++num;

		wchar_t cand[64];
		TCHAR selKey[5] = _T("1.");
		if(i < pageEnd)
		{
			LPCTSTR selKeys = g_selKeyNames[g_selKeyType];
			selKey[0] = selKeys[(i - candList->getPageStart())];
			wcscpy(cand, candList->getCand(i));
            _DecideCandStringcolor(colorIdx, colorBody, FALSE);
		}
		else
		{
			*selKey = 0;

			int page = 1 + candList->getPageStart() / candList->getPageSize();
			int totalPage = candList->getTotalCount() / candList->getPageSize();
			if(candList->getTotalCount() % candList->getPageSize())
				++totalPage;
			swprintf(cand, L"  %d/%d", page, totalPage);
            _DecideCandStringcolor(colorIdx, colorBody, TRUE);
		}

		int len = (int) wcslen(cand);
		GetTextExtentPoint32W(hDC, cand, len, &candsz);
		candsz.cx += 4;
		candsz.cy += 2;
		cand_rc.bottom = cand_rc.top + candsz.cy;

		if(*selKey)
		{
			cand_rc.right = cand_rc.left + selkey_w;
			cand_rc.bottom = cand_rc.top + candsz.cy;
			// Draw selKey
            SetTextColor(hDC, colorIdx);
			ExtTextOut(hDC, cand_rc.left+1, cand_rc.top, ETO_OPAQUE, &cand_rc, selKey, 2, NULL);
			cand_rc.left = cand_rc.right;
		}
		cand_rc.right = cand_rc.left + candsz.cx;
        SetTextColor(hDC, colorBody);
		ExtTextOutW(hDC, cand_rc.left, cand_rc.top, ETO_OPAQUE, &cand_rc, cand, 
			len, NULL);
		if(g_cursorCandList && i == candList->getSelection())
			BitBlt(hDC, cand_rc.left, cand_rc.top, font_size * len, font_size, hDC, cand_rc.left, cand_rc.top, NOTSRCCOPY);

		if(num >= items_per_row && i < pageEnd)
		{
			cand_rc.left = cand_rc.right;
			cand_rc.right = rc.right;
			ExtTextOut(hDC, cand_rc.left, cand_rc.top, ETO_OPAQUE, &cand_rc, NULL, 0, NULL);

			cand_rc.left = 1;
			cand_rc.top += candsz.cy;
			num = 0;
		}
		else
			cand_rc.left = cand_rc.right;

	}
	int rcleft = cand_rc.right;
	int rcright = rc.right;
	cand_rc.left = cand_rc.right;
	cand_rc.right = rc.right;
	ExtTextOut(hDC, cand_rc.left, cand_rc.top, ETO_OPAQUE, &cand_rc, NULL, 0, NULL);

#endif
	Draw3DBorder(hDC, &rc, GetSysColor(COLOR_3DFACE), 0);
	SelectObject(hDC, oldFont);

	EndPaint(hwnd_, &ps);
}

void CandidateWindow::getSize(int* w, int* h) {
	*w = 0; *h = 0;

#if 0
	CandList* candList = (CandList*)ImmLockIMCC(ic->hCandInfo);

	HDC hDC = GetDC(hwnd_);
	HFONT oldFont;

	oldFont = (HFONT)SelectObject(hDC, font);

	int items_per_row =  g_candPerRow;

	int pageEnd = candList->getPageStart() + candList->getPageSize();
	if(pageEnd > candList->getTotalCount())
		pageEnd = candList->getTotalCount();
	int numCand = pageEnd - candList->getPageStart();
	int num = 0;
	int width = 0, height = 0;
	int selkey_w = 0;
	SIZE candsz;
	GetTextExtentPoint32(hDC, "m.", 2, &candsz);
	selkey_w = candsz.cx;
	for(int i = candList->getPageStart(); i <= pageEnd; ++i) {
		++num;
		wchar_t cand[64];
		if(i < pageEnd)
			swprintf (cand, L"%s", candList->getCand(i));
		else
		{
			int page = 1 + candList->getPageStart() / candList->getPageSize();
			int totalPage = candList->getTotalCount() / candList->getPageSize();
			if(candList->getTotalCount() % candList->getPageSize())
				++totalPage;
			swprintf (cand, L"%d/%d", page, totalPage);
		}

		int len = (int) wcslen(cand);
		GetTextExtentPoint32W(hDC, cand, len, &candsz);
		width += candsz.cx + 4;
		width += selkey_w;

		if(candsz.cy > height)
			height = candsz.cy;
        if(num >= items_per_row && i <= pageEnd)
		{
			if(width > *w)
				*w = width;
			*h += height + 2;
			num = 0;
			width = 0;
		}
	}
	if(width > *w)
		*w = width;
	if(num > 0 && num < items_per_row)
		*h += height + 2;

	SelectObject(hDC, oldFont);
// End paint

	ReleaseDC(hwnd_, hDC);
#endif

	*w = 120;
	*h= 60;
	*w += 2;
	*h += 2;
}

void CandidateWindow::updateSize(void) {
	int w, h;
	getSize(&w, &h);
	SetWindowPos(hwnd_, NULL, 0, 0, w, h, SWP_NOACTIVATE|SWP_NOMOVE|SWP_NOZORDER);
}
