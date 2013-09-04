#include "Utils.h"

#include <Windows.h>

wchar_t* utf8ToUtf16(const char* text, int* outLen) {
	wchar_t *wtext = NULL;
	int wlen = MultiByteToWideChar(CP_UTF8, 0, text, -1, NULL, 0);
	wtext = new WCHAR[wlen + 1];
	wlen = MultiByteToWideChar(CP_UTF8, 0, text, -1, wtext, wlen);
	wtext[wlen] = 0;
	if(outLen)
		*outLen = wlen;
	return wtext;
}

char* utf16ToUtf8(const wchar_t* wtext, int* outLen) {
	char *text = NULL;
	int len = WideCharToMultiByte(CP_UTF8, 0, wtext, -1, NULL, 0, NULL, NULL);
	text = new char[len + 1];
	len = WideCharToMultiByte(CP_UTF8, 0, wtext, -1, text, len, NULL, NULL);
	text[len] = 0;
	if(outLen)
		*outLen = len;
	return text;
}
