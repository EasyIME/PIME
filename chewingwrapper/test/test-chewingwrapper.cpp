#include <iostream>
#include <memory>

#include <windows.h>

#include <chewingwrapper.hpp>

int main()
{
	// XXX: Use SetEnvironmentVariableA here will cause crash in Visual Studio.
	_putenv("CHEWING_PATH="CHEWING_PATH);
	_putenv("CHEWING_USER_PATH="CHEWING_USER_PATH);

	const wchar_t EXPECT[] = { 0x6e2c, 0x8a66, 0 /* 測試 */ };
	const wchar_t EXPECT_BOPOMOFO[] = { 0x3118, 0x311c, 0 /* ㄘㄜ */ };

	ChewingWrapper ctx;

	ctx.handle_key('h');
	ctx.handle_key('k');

	if (!ctx.has_bopomofo()) {
		std::cerr << "has_bopomofo shall return true" << std::endl;
		return -1;
	}

	std::unique_ptr<wchar_t> bopomofo_string(ctx.get_bopomofo());
	if (wcscmp(bopomofo_string.get(), EXPECT_BOPOMOFO)) {
		std::cerr << "get_bopomofo shall return " << EXPECT_BOPOMOFO << std::endl;
		return -1;
	}

	ctx.handle_key('4');
	ctx.handle_key('g');
	ctx.handle_key('4');

	if (!ctx.has_preedit()) {
		std::cerr << "has_preedit shall return true" << std::endl;
		return -1;
	}

	std::unique_ptr<wchar_t> preedit_string(ctx.get_preedit());
	if (wcscmp(preedit_string.get(), EXPECT)) {
		std::cerr << "get_preedit shall return " << EXPECT << std::endl;
		return -1;
	}

	ctx.handle_enter();

	if (!ctx.has_commit()) {
		std::cerr << "has_commit shall return true" << std::endl;
		return -1;
	}

	std::unique_ptr<wchar_t> commit_string(ctx.get_commit());
	if (wcscmp(commit_string.get(), EXPECT)) {
		std::cerr << "get_commit shall return " << EXPECT << std::endl;
		return -1;
	}

	return 0;
}
