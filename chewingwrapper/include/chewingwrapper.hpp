#pragma once

#include <chewing.h>

class ChewingWrapper {
public:
    ChewingWrapper();
    ~ChewingWrapper();
private:
    ChewingWrapper(const ChewingWrapper&) = delete;
    ChewingWrapper& operator=(const ChewingWrapper&) = delete;
    ChewingContext *m_ctx;
};
