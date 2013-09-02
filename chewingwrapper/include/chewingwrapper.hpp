#pragma once

#include <memory>

#include <chewing.h>

class ChewingWrapper {
public:
    ChewingWrapper();
    ~ChewingWrapper();

    void handle_default(int key);
    void handle_enter();

    bool has_commit();
    std::unique_ptr<wchar_t> get_commit();

private:
    ChewingWrapper(const ChewingWrapper&);
    ChewingWrapper& operator=(const ChewingWrapper&);
    std::unique_ptr<wchar_t> convert_utf8_to_utf16(std::unique_ptr<char, void(*)(void*)>&& input);
    ChewingContext *m_ctx;
};
