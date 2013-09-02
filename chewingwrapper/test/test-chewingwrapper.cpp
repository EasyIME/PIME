#include <iostream>
#include <memory>

#include <windows.h>

#include <chewingwrapper.hpp>

int main()
{
    SetEnvironmentVariable("CHEWING_PATH", CHEWING_PATH);
    SetEnvironmentVariable("CHEWING_USER_PATH", CHEWING_USER_PATH);

    const wchar_t EXPECT[] = { 0x6e2c, 0x8a66, 0 /* 測試 */ };

    ChewingWrapper ctx;

    ctx.handle_default('h');
    ctx.handle_default('k');
    ctx.handle_default('4');
    ctx.handle_default('g');
    ctx.handle_default('4');
    ctx.handle_enter();

    if (!ctx.has_commit()) {
        std::cerr << "has_commit shall return true" << std::endl;
        return -1;
    }

    std::unique_ptr<wchar_t> commit_string(ctx.get_commit());
    if (wcscmp(commit_string.get(), EXPECT)) {
        std::cerr << "commit_string shall return " << EXPECT << std::endl;
        return -1;
    }

    return 0;
}
