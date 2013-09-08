#pragma once

#include <memory>

#include <chewing.h>

class ChewingWrapper {
public:
	ChewingWrapper();
	~ChewingWrapper();

	void handle_key(int key);
	void handle_enter();
	void handle_space();
	void handle_esc();

	void handle_delete();
	void handle_backspace();

	void handle_home();
	void handle_end();

	void handle_ctrl_num(int code);

	void handle_up();
	void handle_down();
	void handle_left();
	void handle_right();

	void handle_shift_left();
	void handle_shift_right();
	void handle_shift_space();

	void handle_tab();

	bool has_commit();
	std::unique_ptr<wchar_t> get_commit();

	bool has_bopomofo();
	std::unique_ptr<wchar_t> get_bopomofo();

	bool has_preedit();
	std::unique_ptr<wchar_t> get_preedit();

private:
	ChewingWrapper(const ChewingWrapper&);
	ChewingWrapper& operator=(const ChewingWrapper&);
	std::unique_ptr<wchar_t> convert_utf8_to_utf16(std::unique_ptr<char, void(*)(void*)>&& input);
	std::unique_ptr<ChewingContext, void (*)(ChewingContext*)> m_ctx;
};
