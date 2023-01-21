#include "PipeClient.h"

namespace pime {

namespace {

HANDLE createPipe() {
}

bool connectPipe() {
}

}  // namespace

PipeClient::PipeClient(HANDLE pipe_handle): pipeHandle_(pipe_handle) {
}

PipeClient::~PipeClient() {
    close();
}

std::unique_ptr<PipeClient> PipeClient::Create(std::wstring path) {
    HANDLE pipe_handle = CreatePipe();
    if (pipe_handle == INVALID_HANDLE_VALUE) {
        return nullptr;
    }
    return std::make_unique<PipeClient>(pipe_handle);
}

bool PipeClient::waitForConnection() {
}

bool PipeClient::asyncRead(ReadCallback callback) {
    BOOL fRead = FALSE;
    fRead = ReadFileEx(
        pipeHandle_,
        readBuffer_.data(),
        readBuffer_.size(),
        (LPOVERLAPPED)&overlapped_,
        (LPOVERLAPPED_COMPLETION_ROUTINE)[](DWORD dwErr, DWORD cbBytesRead,
            LPOVERLAPPED lpOverLap) {
                auto info = static_cast<OverlappedInfo*>(lpOverLap);
                info->client;
        });
}

bool PipeClient::asyncWrite(WriteCallback callback) {
    BOOL fWrite = WriteFileEx(
        pipeHandle_,
        lpPipeInst->chReply,
        lpPipeInst->cbToWrite,
        (LPOVERLAPPED)lpPipeInst,
        (LPOVERLAPPED_COMPLETION_ROUTINE)CompletedWriteRoutine);
    return fWrite;
}

void PipeClient::close() {
    if (pipeHandle_ != INVALID_HANDLE_VALUE) {
        // FIXME: Do we need to flush pipe here?
        DisconnectNamedPipe(pipeHandle_);
        CloseHandle(pipeHandle_);
    }
    pipeHandle_ = INVALID_HANDLE_VALUE;
}

}  // namespace pime
