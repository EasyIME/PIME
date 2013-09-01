#include <chewingwrapper.hpp>

#include <stdexcept>

ChewingWrapper::ChewingWrapper()
:m_ctx(0)
{
    m_ctx = chewing_new();
    if (!m_ctx)
        throw std::runtime_error("Cannot initialize chewing instance");
}

ChewingWrapper::~ChewingWrapper()
{
    chewing_delete(m_ctx);
    m_ctx = 0;
}
