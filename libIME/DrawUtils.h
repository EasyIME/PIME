#ifndef _DRAW_UTIL_H_
#define _DRAW_UTIL_H_

#include <windows.h>

void FillSolidRect( HDC dc, LPRECT rc, COLORREF color );
void FillSolidRect( HDC dc, int l, int t, int w, int h, COLORREF color );
void Draw3DBorder(HDC hdc, LPRECT rc, COLORREF light, COLORREF dark, int width = 1);
void DrawBitmap(HDC dc, HBITMAP bmp, int x, int y, int w, int h, int srcx, int srcy );

#endif