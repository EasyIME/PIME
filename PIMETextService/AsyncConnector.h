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

#ifndef PIME_ASYNC_CONNECTOR_H
#define PIME_ASYNC_CONNECTOR_H

#include <windows.h>
#include <functional>
#include <memory>
#include <mutex>
#include <string>
#include <nlohmann/json.hpp>

#include "RpcPipe.h"

namespace PIME {

// Callback invoked on the UI thread when connection and init handshake complete.
// - On success: pipe.isValid() is true and initResponse contains the server reply.
// - On connection/handshake failure: pipe.isValid() is false.
// - On cancellation (cancel() or destruction): the callback is NEVER called, and the callback
//   callable is cleared immediately under the lock, ensuring safety when capturing 'this'
//   pointers of objects that may be destroyed concurrently.
using AsyncConnectCallback = std::function<void(RpcPipe pipe, nlohmann::json initResponse)>;

class AsyncConnector : public std::enable_shared_from_this<AsyncConnector> {
public:
	AsyncConnector();
	~AsyncConnector();

	// Starts background connection and handshake on the Windows threadpool.
	// When completed, callback is dispatched to the calling thread's message queue via
	// a private message-only window (HWND_MESSAGE).
	// Must be called from the UI thread.
	bool connect(std::wstring pipeName, nlohmann::json initRequest, AsyncConnectCallback callback);

	// Cancels the connection attempt, closes any opened pipe handle, and destroys the message window.
	// The completion callback is guaranteed NEVER to be invoked after cancel() is called.
	// Can be safely called from any thread (typically called on the UI thread during deactivation/destruction).
	void cancel();

	bool isCancelled() const;

private:
	static void ensureWindowClassRegistered();
	static HWND createMessageOnlyWindow(void* creationParam);
	static LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam);

	void runWorker(PTP_CALLBACK_INSTANCE instance);
	void onWindowMessage();

	mutable std::mutex mutex_;
	std::wstring pipeName_;
	nlohmann::json initRequest_;
	AsyncConnectCallback callback_;
	HWND hwnd_{ NULL };
	bool isCancelled_{ false };

	RpcPipe pipe_;
	nlohmann::json initResponse_;
	bool success_{ false };
};

} // namespace PIME

#endif // PIME_ASYNC_CONNECTOR_H
