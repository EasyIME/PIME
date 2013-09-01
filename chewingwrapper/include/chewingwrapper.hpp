#pragma once

#include <memory>

#include <chewing.h>

class ChewingWrapper {
public:
    ChewingWrapper();
    ~ChewingWrapper();

    bool has_commit();
    std::unique_ptr<wchar_t> get_commit();

private:
    ChewingWrapper(const ChewingWrapper&);
    ChewingWrapper& operator=(const ChewingWrapper&);
    std::unique_ptr<wchar_t> convert_utf8_to_utf16(std::unique_ptr<char>&& input);
    ChewingContext *m_ctx;
};
