//
//	Copyright (C) 2015 - 2020 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
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

#include "PipeClient.h"
#include "PipeServer.h"
#include "Utils.h"
#include "BackendServer.h"


using namespace std;

namespace PIME {

static wstring_convert<codecvt_utf8<wchar_t>> utf8Codec;

// default to 30 seconds
static constexpr std::uint64_t BACKEND_REQUEST_TIMEOUT_MS = 30 * 1000;


PipeClient::PipeClient(PipeServer* server, DWORD pipeMode, SECURITY_ATTRIBUTES* securityAttributes) :
    server_{ server },
    backend_(nullptr),
    // generate a new uuid for client ID
    clientId_{ generateUuidStr() },
    pipe_{ pipeMode, securityAttributes },
    waitResponseTimer_{ std::make_unique<uv_timer_t>() } {

    pipe_.setBlocking(false);

    pipe_.setReadCallback(
        [this](const char* data, size_t len) {
            handleClientMessage(data, len);
        }
    );
    pipe_.setReadErrorCallback(
        [this](int status) {
            onReadError(status);
        }
    );
    pipe_.setCloseCallback(
        [this]() {
            server_->removeClient(this);
        }
    );

    // setup a timer to detect request timeout
	uv_timer_init(uv_default_loop(), waitResponseTimer_.get());
	waitResponseTimer_->data = this;
}

PipeClient::~PipeClient() {
    stopRequestTimeoutTimer();

    // Close the uv timer and free its resources.
    // NOTE: The operation is async and it's not safe to free the memory here.
    // We release the ownership to the unique_ptr and delete the raw pointer in the callback of uv_close().
    waitResponseTimer_->data = nullptr;  // Avoid referencing to this since this object is destructing.
    uv_close(reinterpret_cast<uv_handle_t*>(waitResponseTimer_.release()), [](uv_handle_t* handle) {
        delete reinterpret_cast<uv_timer_t*>(handle);
        }
    );
}

std::shared_ptr<spdlog::logger>& PipeClient::logger() {
	return server_->logger();
}

void PipeClient::close() {
    pipe_.close();
}

void PipeClient::onReadError(int error) {
    // the client connection seems to be broken. close it.
    disconnectFromBackend();
    close();
}

void PipeClient::handleClientMessage(const char* readBuf, size_t len) {
    // NOTE: readBuf is not null terminated.
	if (!backend_) {
		// special handling, asked for init PIMELauncher.
		// extract backend info from the request message and find a suitable backend
		Json::Value msg;
		Json::Reader reader;
		if (reader.parse(readBuf, readBuf + len, msg)) {
			initBackend(msg);
		}
	}

	// pass the incoming message to the backend
	if (backend_) {
		// start a timer to see if we can get a response from backend server before timeout.
		startRequestTimeoutTimer(BACKEND_REQUEST_TIMEOUT_MS);
		backend_->handleClientMessage(this, readBuf, len);
	}
}

bool PipeClient::initBackend(const Json::Value & params) {
	const char* method = params["method"].asCString();
	if (method != nullptr && strcmp(method, "init") == 0) {  // the client connects to us the first time
		// find a backend for the client text service
		const char* guid = params["id"].asCString();
		backend_ = server_->backendFromLangProfileGuid(guid);
		if (backend_ != nullptr) {
			// FIXME: write some response to indicate the failure
			return true;
		}
		else {
			logger()->critical("Backend is not found for text service: {}", guid);
		}
	}
	return false;
}

void PipeClient::disconnectFromBackend() {
	if (backend_ != nullptr) {
		// FIXME: client->backend_->removeClient(client->clientId_);
		// notify the backend server to remove the client
		const char msg[] = "{\"method\":\"close\"}";
		backend_->handleClientMessage(this, msg, strlen(msg));
	}
}

void PipeClient::startRequestTimeoutTimer(std::uint64_t timeoutMs) {
	uv_timer_start(waitResponseTimer_.get(), [](uv_timer_t* handle) {
        if (handle->data) {
            auto pThis = reinterpret_cast<PipeClient*>(handle->data);
            pThis->onRequestTimeout();
        }
	}, timeoutMs, 0);
}

void PipeClient::stopRequestTimeoutTimer() {
	uv_timer_stop(waitResponseTimer_.get());
}

void PipeClient::onRequestTimeout() {
	// We sent a message to the backend server, but haven't got any response before the timeout
	// Assume that the backend server is dead. => Try to restart
	if (backend_) {
		logger()->critical("Backend {} seems to be dead. Try to restart!", backend_->name());
		backend_->restartProcess();
	}

    // FIXME: do we need to close the pipe or write some error response?
}

} // namespace PIME
