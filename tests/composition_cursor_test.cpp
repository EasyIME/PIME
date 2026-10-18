// Generated with assistance from Codex (GPT-6).
#include "CompositionCursor.h"

#include <iostream>
#include <string>

int main() {
	const auto expectPosition = [](const std::wstring& compositionString, int compositionCursor, int expected) {
		const int actual = PIME::compositionCursorToUtf16Position(compositionString, compositionCursor);
		if (actual != expected) {
			std::cerr << "Expected UTF-16 position " << expected << " for cursor " << compositionCursor
				<< ", got " << actual << '\n';
			return false;
		}
		return true;
	};

	const std::wstring adjacentSurrogatePairs = L"\U0001F600\U0001F642";
	if (!expectPosition(adjacentSurrogatePairs, 0, 0) ||
		!expectPosition(adjacentSurrogatePairs, 1, 2) ||
		!expectPosition(adjacentSurrogatePairs, 2, 4) ||
		!expectPosition(adjacentSurrogatePairs, 3, 4)) {
		return 1;
	}

	const std::wstring mixedCharacters = L"A\U0001F600B";
	if (!expectPosition(mixedCharacters, 1, 1) ||
		!expectPosition(mixedCharacters, 2, 3) ||
		!expectPosition(mixedCharacters, 3, 4)) {
		return 1;
	}

	std::wstring unpairedSurrogate;
	unpairedSurrogate.push_back(static_cast<wchar_t>(0xD83D));
	unpairedSurrogate.push_back(L'x');
	if (!expectPosition(unpairedSurrogate, 1, 1) ||
		!expectPosition(unpairedSurrogate, 2, 2) ||
		!expectPosition(mixedCharacters, -1, 0)) {
		return 1;
	}

	return 0;
}
