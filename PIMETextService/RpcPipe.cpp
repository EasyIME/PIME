//
//	Copyright (C) 2026 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
//
//	API design and architecture by Hong Jen Yee (PCMan).
//	Implementation generated with AI assistance from Google Antigravity (Gemini 3.8 Flash).
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

#include "RpcPipe.h"
#include <memory>
#include <utility>

namespace PIME {

RpcPipe::RpcPipe() = default;

RpcPipe::RpcPipe(HANDLE pipe)
	: pipe_(pipe) {
}

RpcPipe::~RpcPipe() {
	close();
}

RpcPipe::RpcPipe(RpcPipe&& other) noexcept
	: pipe_(other.pipe_),
	  ioEvent_(other.ioEvent_),
	  readBuffer_(std::move(other.readBuffer_)) {
	other.pipe_ = INVALID_HANDLE_VALUE;
	other.ioEvent_ = NULL;
}

RpcPipe& RpcPipe::operator=(RpcPipe&& other) noexcept {
	if (this != &other) {
		close();
		pipe_ = other.pipe_;
		ioEvent_ = other.ioEvent_;
		readBuffer_ = std::move(other.readBuffer_);
		other.pipe_ = INVALID_HANDLE_VALUE;
		other.ioEvent_ = NULL;
	}
	return *this;
}

void RpcPipe::close() noexcept {
	if (pipe_ != INVALID_HANDLE_VALUE) {
		CloseHandle(pipe_);
		pipe_ = INVALID_HANDLE_VALUE;
	}
	if (ioEvent_ && ioEvent_ != INVALID_HANDLE_VALUE) {
		CloseHandle(ioEvent_);
		ioEvent_ = NULL;
	}
	readBuffer_.clear();
}

RpcPipe RpcPipe::connect(const wchar_t* pipeName, int timeoutMs) {
	HANDLE pipe = INVALID_HANDLE_VALUE;
	if (WaitNamedPipeW(pipeName, timeoutMs)) {
		pipe = CreateFileW(
			pipeName,                        // lpFileName: named pipe path
			GENERIC_READ | GENERIC_WRITE,    // dwDesiredAccess: bidirectional read/write access
			0,                               // dwShareMode: prevent shared access
			NULL,                            // lpSecurityAttributes: default security descriptor
			OPEN_EXISTING,                   // dwCreationDisposition: open existing pipe instance
			FILE_FLAG_OVERLAPPED,            // dwFlagsAndAttributes: overlapped mode for async I/O
			NULL                             // hTemplateFile: no template file handle
		);
	}

	return RpcPipe(pipe);
}

bool RpcPipe::callPipeIO(bool isRead, void* buffer, DWORD size, DWORD* rlen, int timeoutMs) {
	if (!pipe_ || pipe_ == INVALID_HANDLE_VALUE) {
		return false;
	}

	if (!ioEvent_ || ioEvent_ == INVALID_HANDLE_VALUE) {
		ioEvent_ = CreateEventW(NULL, TRUE, FALSE, NULL);
	}
	if (!ioEvent_ || ioEvent_ == INVALID_HANDLE_VALUE) {
		return false;
	}

	OVERLAPPED overlapped = { 0 };
	overlapped.hEvent = ioEvent_;
	ResetEvent(ioEvent_);

	BOOL ok = isRead
		? ReadFile(pipe_, buffer, size, rlen, &overlapped)
		: WriteFile(pipe_, buffer, size, rlen, &overlapped);

	if (!ok && GetLastError() != ERROR_IO_PENDING) {
		return false;
	}

	DWORD wait = WaitForSingleObject(ioEvent_, timeoutMs);
	if (wait == WAIT_OBJECT_0) {
		ok = GetOverlappedResult(pipe_, &overlapped, rlen, FALSE);
	}
	else {
		CancelIoEx(pipe_, &overlapped);
		GetOverlappedResult(pipe_, &overlapped, rlen, TRUE);
		ok = FALSE;
	}
	return ok != FALSE;
}

bool RpcPipe::callRpc(const std::string& serializedRequest, std::string& serializedReply, int timeoutMs) {
	std::string request = serializedRequest;
	if (request.empty() || request.back() != '\n') {
		request += '\n';
	}

	DWORD wlen = 0;
	if (!callPipeIO(false, (void*)request.data(), static_cast<DWORD>(request.size()), &wlen, timeoutMs)) {
		return false;
	}

	char buf[8192];
	DWORD rlen = 0;
	while (true) {
		size_t pos = readBuffer_.find('\n');
		if (pos != std::string::npos) {
			serializedReply = readBuffer_.substr(0, pos);
			readBuffer_.erase(0, pos + 1);
			return true;
		}

		if (readBuffer_.size() >= kMaxIpcMessageLength) {
			readBuffer_.clear();
			return false;
		}

		if (!callPipeIO(true, buf, sizeof(buf), &rlen, timeoutMs) || rlen == 0) {
			return false;
		}
		readBuffer_.append(buf, rlen);
	}
}

} // namespace PIME
