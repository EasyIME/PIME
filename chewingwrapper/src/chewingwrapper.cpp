#include <chewingwrapper.hpp>

#include <new>
#include <stdexcept>

#include <windows.h>

ChewingWrapper::ChewingWrapper()
:m_ctx(chewing_new(), chewing_delete)
{
    if (!m_ctx)
        throw std::runtime_error("Cannot initialize chewing instance");
}

ChewingWrapper::~ChewingWrapper()
{
}

void ChewingWrapper::handle_default(int key)
{
    chewing_handle_Default(m_ctx.get(), key);
}

void ChewingWrapper::handle_enter()
{
    chewing_handle_Enter(m_ctx.get());
}

bool ChewingWrapper::has_commit()
{
    return !!chewing_commit_Check(m_ctx.get());
}

std::unique_ptr<wchar_t> ChewingWrapper::get_commit()
{
    std::unique_ptr<char, void(*)(void*)> utf8_string(chewing_commit_String(m_ctx.get()), chewing_free);
    if (!utf8_string.get())
        throw std::bad_alloc();
    return convert_utf8_to_utf16(std::move(utf8_string));
}

std::unique_ptr<wchar_t> ChewingWrapper::convert_utf8_to_utf16(std::unique_ptr<char, void(*)(void*)>&& input)
{
    int len = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, input.get(), -1, 0, 0);
    if (len == 0)
        throw std::runtime_error("MultiByteToWideChar returns 0");

    std::unique_ptr<wchar_t> output(new wchar_t[len]);

    MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, input.get(), -1, output.get(), len);
    return output;
}
