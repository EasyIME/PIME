#pragma once

#include <string>
#include <memory>
#include <functional>
#include <vector>

#include <windows.h>

namespace pime {

class PipeClient
{
public:
    explicit PipeClient(HANDLE pipe_handle);

    ~PipeClient();

    static std::unique_ptr<PipeClient> Create(std::wstring path);

    // Poll connection status.
    bool waitForConnection();

    using ReadCallback = std::function<void(const char* buffer, size_t len)>;

    bool asyncRead(ReadCallback callback);

    using WriteCallback = std::function<void(bool)>;

    bool asyncWrite(WriteCallback callback);

    void close();

    HANDLE pipeHandle() const {
        return pipeHandle_;
    }

private:
    struct OverlappedInfo : public OVERLAPPED {
        PipeClient* client;
    };

private:
    HANDLE pipeHandle_;
    std::vector<char> readBuffer_;
    std::vector<char> writeBuffer_;
    OverlappedInfo overlapped_;
};

}  // namespace pime
