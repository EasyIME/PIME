//
//	Copyright (C) 2015 - 2018 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
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

#include "BackendServer.h"

using namespace std;

namespace PIME {

static wstring_convert<codecvt_utf8<wchar_t>> utf8Codec;

// default to 30 seconds
static constexpr std::uint64_t BACKEND_REQUEST_TIMEOUT_MS = 30 * 1000;


PipeClient::PipeClient(PipeServer* server, DWORD pipeMode, SECURITY_ATTRIBUTES* securityAttributes) :
	backend_(nullptr),
	server_{ server } {

	// setup pipe
	uv_pipe_init_windows_named_pipe(uv_default_loop(), &pipe_, 0, pipeMode, securityAttributes);
	pipe_.data = this;
	uv_stream_set_blocking((uv_stream_t*)&pipe_, 0);

	// generate a new uuid for client ID
	UUID uuid;
	UuidCreate(&uuid);
	RPC_CSTR uuid_str = nullptr;
	UuidToStringA(&uuid, &uuid_str);
	clientId_ = (char*)uuid_str;
	RpcStringFreeA(&uuid_str);

	// setup a timer to detect request timeout
	uv_timer_init(uv_default_loop(), &waitResponseTimer_);
	waitResponseTimer_.data = this;
}

std::shared_ptr<spdlog::logger>& PipeClient::logger() {
	return server_->logger();
}

void PipeClient::startReadPipe() {
	uv_read_start((uv_stream_t*)&pipe_,
		[](uv_handle_t* handle, size_t suggested_size, uv_buf_t* buf) {
		buf->base = new char[suggested_size];
		buf->len = suggested_size;
	},
		[](uv_stream_t* stream, ssize_t nread, const uv_buf_t* buf) {
		auto client = (PipeClient*)stream->data;
		client->onClientDataReceived(stream, nread, buf);
	});
}

void PipeClient::writePipe(const char* data, size_t len) {
	// we got a response before request timeout, so stop the timer
	stopWaitTimer();

	// The memory pointed to by the buffers must remain valid until the callback gets called. 
	// http://docs.libuv.org/en/v1.x/stream.html
	// So we need to copy the buffer
	char* copiedData = new char[len];
	memcpy(copiedData, data, len);
	uv_buf_t buf = { len, copiedData };
	uv_write_t* req = new uv_write_t{};
	req->data = copiedData;
	uv_write(req, stream(), &buf, 1, [](uv_write_t* req, int status) {
		char* copiedData = reinterpret_cast<char*>(req->data);
		delete[]copiedData;
		delete req;
	});
}

void PipeClient::destroy() {
	uv_close((uv_handle_t*)&pipe_, [](uv_handle_t* handle) {
		auto client = (PipeClient*)handle->data;
		delete client;
	});
}

void PipeClient::onClientDataReceived(uv_stream_t* stream, ssize_t nread, const uv_buf_t* buf) {
	if (nread <= 0 || nread == UV_EOF || buf->base == nullptr) {
		if (buf->base) {
			delete[]buf->base;
		}
		// the client connection seems to be broken. close it.
		disconnectFromBackend();
		return;
	}
	if (buf->base) {
		handleClientMessage(buf->base, buf->len);
		delete[]buf->base;
	}
}

void PipeClient::handleClientMessage(const char* readBuf, size_t len) {
	if (!backend_) {
		// special handling, asked for init PIMELauncher.
		// extract backend info from the request message and find a suitable backend
		Json::Value msg;
		Json::Reader reader;
		if (reader.parse(readBuf, msg)) {
			setupBackend(msg);
		}
	}

	// pass the incoming message to the backend
	if (backend_) {
		// start a timer to see if we can get a response from backend server before timeout.
		startWaitTimer(BACKEND_REQUEST_TIMEOUT_MS);

		// really call the backend
		backend_->handleClientMessage(this, readBuf, len);
	}
}

bool PipeClient::setupBackend(const Json::Value & params) {
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

	server_->removeClient(this);

	destroy();
}

void PipeClient::startWaitTimer(std::uint64_t timeoutMs) {
	uv_timer_start(&waitResponseTimer_, [](uv_timer_t* handle) {
		auto pThis = reinterpret_cast<PipeClient*>(handle->data);
		pThis->onRequestTimeout();
	}, timeoutMs, 0);
}

void PipeClient::stopWaitTimer() {
	uv_timer_stop(&waitResponseTimer_);
}

void PipeClient::onRequestTimeout() {
	// We sent a message to the backend server, but haven't got any response before the timeout
	// Assume that the backend server is dead. => Try to restart
	if (backend_) {
		logger()->critical("Backend {} seems to be dead. Try to restart!", backend_->name());
		backend_->restartProcess();
	}
}

} // namespace PIME
