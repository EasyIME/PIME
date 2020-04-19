//
//	Copyright (C) 2020 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
//
//  This header-only library is a thin wrapper around libuv pipes.
//
//	This library is free software; you can redistribute it and/or
//	modify it under the terms of the GNU Library General Public
//	License as published by the Free Software Foundation; either
//	version 2 of the License, or (at your option) any later version.
//
//	This library is distributed in the hope that it will be useful,
//	but WITHOUT ANY WARRANTY; without even the implied warranty of
//	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
//	Library General Public License for more details.
//
//	You should have received a copy of the GNU Library General Public
//	License along with this library; if not, write to the
//	Free Software Foundation, Inc., 51 Franklin St, Fifth Floor,
//	Boston, MA  02110-1301, USA.
//

#pragma once

#include <uv.h>
#include <string>
#include <functional>

// Define this flag to use a patched libuv to support Windows named pipe with security attributes.
#ifdef HAVE_UV_NAMED_PIPE
#include <Windows.h>
#endif

namespace uv {

class Pipe {
public:
    Pipe(uv_loop_t* loop = uv_default_loop()) {
        uv_pipe_init(loop, &pipe_, 0);
        pipe_.data = this;
    }

#ifdef HAVE_UV_NAMED_PIPE
    // NOTE: When sa is not null, Pipe does not take ownership of the object.
    // The caller is responsible for making sure the memory buffer remain valid
    // throughout the life-span of the Pipe object.
    Pipe(DWORD pipeMode, SECURITY_ATTRIBUTES* sa, uv_loop_t* loop = uv_default_loop()) {
        uv_pipe_init_windows_named_pipe(loop, &pipe_, 0, pipeMode, sa);
        pipe_.data = this;
    }
#endif

    virtual ~Pipe() {
    }

    void setBlocking(bool blocking) {
        uv_stream_set_blocking(streamHandle(), blocking ? 1 : 0);
    }

    void setReadCallback(std::function<void(const char*, size_t)> callback) {
        readCallback_ = std::move(callback);
    }

    void setReadErrorCallback(std::function<void(int)> callback) {
        readErrorCallback_ = std::move(callback);
    }

    void setWriteCallback(std::function<void(int)> callback) {
        writeCallback_ = std::move(callback);
    }

    void setCloseCallback(std::function<void()> callback) {
        closeCallback_ = std::move(callback);
    }

    void startRead() {
        uv_read_start(
            streamHandle(),
            [](uv_handle_t* handle, size_t suggested_size, uv_buf_t* buf) {
                buf->base = new char[suggested_size];
                buf->len = suggested_size;
            },
            [](uv_stream_t* stream, ssize_t nread, const uv_buf_t* buf) {
                auto this_ = reinterpret_cast<Pipe*>(stream->data);
                if (nread != UV_ECANCELED && this_ != nullptr) {
                    if (nread > 0) {
                        if (this_->readCallback_) {
                            this_->readCallback_(buf->base, size_t(nread));
                        }
                    }
                    else if (nread < 0) {
                        if (this_->readErrorCallback_) {
                            this_->readErrorCallback_(nread);
                        }
                    }
                }

                if (buf->base) {
                    delete[]buf->base;
                }
            });
    }

    void stopRead() {
        uv_read_stop(streamHandle());
    }

    void write(const char* data, size_t len) {
        write(std::string(data, len));
    }

    template<typename Buffer>
    void write(Buffer&& dataToWrite) {
        struct WriteReqData {
            uv_write_t req;
            Buffer dataToWrite;
            Pipe* pipe;
        };
        auto writeReqData = new WriteReqData();
        writeReqData->req.data = writeReqData;
        writeReqData->dataToWrite = std::move(dataToWrite);
        writeReqData->pipe = this;

        uv_buf_t buf;
        buf.len = writeReqData->dataToWrite.size();
        buf.base = const_cast<char*>(writeReqData->dataToWrite.data());

        uv_write(&writeReqData->req,
            streamHandle(), &buf, 1,
            [](uv_write_t* req, int status) {
                auto writeReqData = reinterpret_cast<WriteReqData*>(req->data);
                if (status != UV_ECANCELED) {
                    auto this_ = writeReqData->pipe;
                    if (this_->writeCallback_) {
                        this_->writeCallback_(status);
                    }
                }
                delete writeReqData;
            });
    }

    void close() {
        if (uv_is_closing(handle())) {
            return;
        }

        uv_close(handle(),
            [](uv_handle_t* handle) {
                // All other read/write callbacks will be called with UV_ECANCELED before the close callback.
                // So this should be the last callback called on the handle.
                auto this_ = reinterpret_cast<Pipe*>(handle->data);
                if (this_->closeCallback_) {
                    // The close callback may delete `this', which frees the function object.
                    // So we make a copy here to be safe.
                    auto closeCallback = this_->closeCallback_;
                    closeCallback();
                }
            }
        );
    }

    uv_pipe_t* pipeHandle() {
        return &pipe_;
    }

    uv_stream_t* streamHandle() {
        return (uv_stream_t*)(&pipe_);
    }

    uv_handle_t* handle() {
        return (uv_handle_t*)(&pipe_);
    }

private:
    uv_pipe_t pipe_;
    std::function<void(const char*, size_t)> readCallback_;
    std::function<void(int)> readErrorCallback_;
    std::function<void(int)> writeCallback_;
    std::function<void()> closeCallback_;
};

} // namespace uv
