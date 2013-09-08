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

void ChewingWrapper::handle_key(int key)
{
	chewing_handle_Default(m_ctx.get(), key);
}

void ChewingWrapper::handle_enter()
{
	chewing_handle_Enter(m_ctx.get());
}

void ChewingWrapper::handle_space()
{
	chewing_handle_Space(m_ctx.get());
}

void ChewingWrapper::handle_esc()
{
	chewing_handle_Esc(m_ctx.get());
}

void ChewingWrapper::handle_delete()
{
	chewing_handle_Del(m_ctx.get());
}

void ChewingWrapper::handle_backspace()
{
	chewing_handle_Backspace(m_ctx.get());
}

void ChewingWrapper::handle_home()
{
	chewing_handle_Home(m_ctx.get());
}

void ChewingWrapper::handle_end()
{
	chewing_handle_End(m_ctx.get());
}

void ChewingWrapper::handle_ctrl_num(int code)
{
	chewing_handle_CtrlNum(m_ctx.get(), code);
}

void ChewingWrapper::handle_up()
{
	chewing_handle_Up(m_ctx.get());
}

void ChewingWrapper::handle_down()
{
	chewing_handle_Down(m_ctx.get());
}

void ChewingWrapper::handle_left()
{
	chewing_handle_Left(m_ctx.get());
}

void ChewingWrapper::handle_right()
{
	chewing_handle_Right(m_ctx.get());
}

void ChewingWrapper::handle_shift_left()
{
	chewing_handle_ShiftLeft(m_ctx.get());
}

void ChewingWrapper::handle_shift_right()
{
	chewing_handle_ShiftRight(m_ctx.get());
}

void ChewingWrapper::handle_shift_space()
{
	chewing_handle_ShiftSpace(m_ctx.get());
}

void ChewingWrapper::handle_tab()
{
	chewing_handle_Tab(m_ctx.get());
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

bool ChewingWrapper::has_bopomofo()
{
	return !chewing_zuin_Check(m_ctx.get());
}

std::unique_ptr<wchar_t> ChewingWrapper::get_bopomofo()
{
	int dummy;
	std::unique_ptr<char, void(*)(void*)> utf8_string(chewing_zuin_String(m_ctx.get(), &dummy), chewing_free);
	if (!utf8_string.get())
		throw std::bad_alloc();
	return convert_utf8_to_utf16(std::move(utf8_string));
}

bool ChewingWrapper::has_preedit()
{
	return !!chewing_buffer_Check(m_ctx.get());
}

std::unique_ptr<wchar_t> ChewingWrapper::get_preedit()
{
	std::unique_ptr<char, void(*)(void*)> utf8_string(chewing_buffer_String(m_ctx.get()), chewing_free);
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

