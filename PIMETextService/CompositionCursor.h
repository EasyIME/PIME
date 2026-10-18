// Generated with assistance from Codex (GPT-6).
#pragma once

#include <string>

namespace PIME {

inline bool isHighSurrogate(wchar_t value) {
	return value >= 0xD800 && value <= 0xDBFF;
}

inline bool isLowSurrogate(wchar_t value) {
	return value >= 0xDC00 && value <= 0xDFFF;
}

inline int compositionCursorToUtf16Position(const std::wstring& compositionString, int compositionCursor) {
	int utf16Position = 0;
	int characterPosition = 0;
	const int compositionLength = static_cast<int>(compositionString.size());

	while (characterPosition < compositionCursor && utf16Position < compositionLength) {
		const wchar_t current = compositionString[utf16Position];
		++characterPosition;
		++utf16Position;

		if (isHighSurrogate(current) &&
			utf16Position < compositionLength &&
			isLowSurrogate(compositionString[utf16Position])) {
			++utf16Position;
		}
	}

	return utf16Position;
}

} // namespace PIME
