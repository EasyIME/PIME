#ifndef IME_UTILS_H
#define IME_UTILS_H

wchar_t* utf8ToUtf16(const char* text, int* outLen = 0);

char* utf16ToUtf8(const wchar_t* wtext, int* outLen = 0);

#endif
