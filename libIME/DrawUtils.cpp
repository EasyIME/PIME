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

#include "DrawUtils.h"

void FillSolidRect(HDC dc, LPRECT rc, COLORREF color) {
	SetBkColor(dc, color);
	::ExtTextOut(dc, 0, 0, ETO_OPAQUE, rc, NULL, 0, NULL);
}

void FillSolidRect(HDC dc, int l, int t, int w, int h, COLORREF color) {
	RECT rc;
	rc.left = l;
	rc.top = t;
	rc.right = rc.left + w;
	rc.bottom = rc.top + h;
	SetBkColor(dc, color);
	::ExtTextOut(dc, 0, 0, ETO_OPAQUE, &rc, NULL, 0, NULL);
}

void Draw3DBorder(HDC hdc, LPRECT rc, COLORREF light, COLORREF dark, int width) {
	MoveToEx(hdc, rc->left, rc->bottom, NULL);

	HPEN light_pen = CreatePen(PS_SOLID|PS_INSIDEFRAME, width, light);
	HGDIOBJ oldPen = SelectObject(hdc, light_pen);
	LineTo(hdc, rc->left, rc->top);
	LineTo(hdc, rc->right-width, rc->top);
	SelectObject(hdc, oldPen);
	DeleteObject(light_pen);

	HPEN dark_pen = CreatePen(PS_SOLID|PS_INSIDEFRAME, width, dark);
	oldPen = SelectObject(hdc, dark_pen);
	LineTo(hdc, rc->right-width, rc->bottom-width);
	LineTo(hdc, rc->left, rc->bottom-width);
	DeleteObject(dark_pen);
	SelectObject(hdc, oldPen);
}

void DrawBitmap(HDC dc, HBITMAP bmp, int x, int y, int w, int h, int srcx, int srcy) {
	HDC memdc = CreateCompatibleDC(dc);
	HGDIOBJ oldobj = SelectObject(memdc, bmp);
	BitBlt(dc, x, y, w, h, memdc, srcx, srcy, SRCCOPY);
	SelectObject(memdc, oldobj);
	DeleteDC(memdc);
}