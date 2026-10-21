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

#ifndef PIME_RPC_PIPE_H
#define PIME_RPC_PIPE_H

#include <windows.h>
#include <string>

namespace PIME {

constexpr size_t kMaxIpcMessageLength = 4 * 1024 * 1024; // 4 MB

// RAII move-only wrapper managing an RPC channel over a Windows Named Pipe.
// Encapsulates pipe handle lifecycle, line-delimited message framing, and overlapped I/O.
class RpcPipe {
public:
	RpcPipe();
	explicit RpcPipe(HANDLE pipe);
	~RpcPipe();

	// Move-only
	RpcPipe(RpcPipe&& other) noexcept;
	RpcPipe& operator=(RpcPipe&& other) noexcept;
	RpcPipe(const RpcPipe&) = delete;
	RpcPipe& operator=(const RpcPipe&) = delete;

	// Factory: connects to the named pipe synchronously with a timeout (blocking).
	static RpcPipe connect(const wchar_t* pipeName, int timeoutMs = 3000);

	// Checks if the underlying pipe handle is currently open and valid.
	bool isValid() const noexcept { return pipe_ != INVALID_HANDLE_VALUE; }
	explicit operator bool() const noexcept { return isValid(); }

	HANDLE pipeHandle() const noexcept { return pipe_; }

	// Closes the pipe handle, overlapped event, and clears the read buffer.
	void close() noexcept;

	// Sends a newline-delimited request and reads a newline-delimited reply (blocking).
	bool callRpc(const std::string& request, std::string& reply, int timeoutMs);

private:
	bool callPipeIO(bool isRead, void* buffer, DWORD size, DWORD* rlen, int timeoutMs);

	HANDLE pipe_ = INVALID_HANDLE_VALUE;
	HANDLE ioEvent_ = NULL;
	std::string readBuffer_;
};

} // namespace PIME

#endif // PIME_RPC_PIPE_H
