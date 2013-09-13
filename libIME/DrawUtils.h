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

#ifndef IME_DRAW_UTIL_H
#define IME_DRAW_UTIL_H

#include <windows.h>

void FillSolidRect( HDC dc, LPRECT rc, COLORREF color );
void FillSolidRect( HDC dc, int l, int t, int w, int h, COLORREF color );
void Draw3DBorder(HDC hdc, LPRECT rc, COLORREF light, COLORREF dark, int width = 1);
void DrawBitmap(HDC dc, HBITMAP bmp, int x, int y, int w, int h, int srcx, int srcy );

#endif