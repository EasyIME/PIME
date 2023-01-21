#include "PipeServer.h"

#include <windows.h>

#include "PipeClient.h"

namespace pime {

namespace {

bool CreateAndConnectInstance() {
}

}  // namespace

PipeServer::PipeServer(std::wstring pipe_path) : pipePath_(std::move(pipe_path))
{
    connectOverlapped_.hEvent = CreateEvent(/*lpEventAttributes=*/nullptr, /*bManualReset=*/TRUE, /*bInitialState=*/FALSE, /*lpName=*/nullptr);
}

PipeServer::~PipeServer() {
    CloseHandle(connectOverlapped_.hEvent);
}

bool PipeServer::waitForNextClient() {

}

void PipeServer::run() {
    nextClientPending_ = CreateAndConnectPipe(&nextClientPipe_, &connectOverlapped_);

    bool pending_io = CreateAndConnectInstance(&pipe_handle, &connectOverlapped_);
    while (true) {
        DWORD wait_event_status = WaitForSingleObjectEx(connectOverlapped_.hEvent, INFINITE, /*bAlertable=*/TRUE);
        switch (wait_event_status) {
        case WAIT_OBJECT_0:
            // new pipe client connected.
            if (pending_io) {
                if (!GetOverlappedResult(pipe_handle)) {
                    // REPORT ERROR!!
                    return;
                }
            }

            // Create new client object.
            auto pipe_client = std::make_unique<PipeClient>(pipe_handle);
            pipe_client->asyncRead();

            // prepare the next pipe client.
            break;
        case WAIT_IO_COMPLETION:
            break;
        default:
            printf("WaitForSingleObjectEx (%d)\n", GetLastError());
            return;
        }
    }
}

}  // namespace pime
