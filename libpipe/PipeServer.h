#pragma once

#include <string>

namespace pime {

class PipeServer {
public:
    explicit PipeServer(std::wstring pipe_path);

    ~PipeServer();

    void run();

private:
    bool waitForNextClient();

private:
    std::wstring pipePath_;
    HANDLE nextClientPipe_ = INVALID_HANDLE_VALUE;
    OVERLAPPED connectOverlapped_;
    bool nextClientPending_ = false;
};

}
