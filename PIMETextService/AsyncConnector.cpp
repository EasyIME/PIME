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

#include "AsyncConnector.h"
#include "JsonUtils.h"
#include <mutex>
#include <cassert>

namespace PIME {

namespace {

constexpr UINT WM_PIME_ASYNC_DONE = WM_USER + 0x4101;
constexpr wchar_t kWindowClassName[] = L"PIME_AsyncConnector_MsgWnd";
constexpr int kDefaultRpcTimeoutMs = 15000;
constexpr size_t kMaxIpcMessageLength = 4 * 1024 * 1024; // 4 MB

HMODULE getSelfModuleHandle(bool addRef = false) {
	HMODULE hModule = NULL;
	DWORD flags = GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS;
	if (!addRef) {
		flags |= GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT;
	}
	GetModuleHandleExW(
		flags,
		reinterpret_cast<LPCWSTR>(&getSelfModuleHandle),
		&hModule
	);
	return hModule;
}

} // namespace

void AsyncConnector::ensureWindowClassRegistered() {
	static std::once_flag once;
	std::call_once(once, []() {
		WNDCLASSEXW wc = { sizeof(wc) };
		wc.lpfnWndProc = AsyncConnector::WndProc;
		wc.hInstance = getSelfModuleHandle();
		wc.lpszClassName = kWindowClassName;
		RegisterClassExW(&wc);
	});
}

// Creates an invisible, message-only Win32 window (HWND_MESSAGE).
// Message-only windows do not render, have no visual elements or Z-order,
// and are used purely to marshal messages and callbacks to the creating thread's queue.
HWND AsyncConnector::createMessageOnlyWindow(void* creationParam) {
	ensureWindowClassRegistered();
	return CreateWindowExW(
		0,                         // dwExStyle: No extended window styles needed
		kWindowClassName,          // lpClassName: Registered window class name for message dispatching
		NULL,                      // lpWindowName: No title bar or caption text for a message-only window
		0,                         // dwStyle: Standard 0 (no WS_VISIBLE, WS_CHILD, or border styles)
		0,                         // X: Ignored for message-only windows
		0,                         // Y: Ignored for message-only windows
		0,                         // nWidth: Ignored for message-only windows
		0,                         // nHeight: Ignored for message-only windows
		HWND_MESSAGE,              // hWndParent: HWND_MESSAGE designates this window as message-only
		NULL,                      // hMenu: No menu handle
		getSelfModuleHandle(),     // hInstance: Handle to the module instance of this DLL
		creationParam              // lpParam: Passed to WM_NCCREATE/WM_CREATE for GWLP_USERDATA association
	);
}

AsyncConnector::AsyncConnector() {
}

AsyncConnector::~AsyncConnector() {
	cancel();
}

LRESULT CALLBACK AsyncConnector::WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
	if (msg == WM_NCCREATE) {
		auto cs = reinterpret_cast<CREATESTRUCTW*>(lParam);
		SetWindowLongPtrW(hwnd, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(cs->lpCreateParams));
		return TRUE;
	}

	if (msg == WM_NCDESTROY) {
		SetWindowLongPtrW(hwnd, GWLP_USERDATA, 0);
		return DefWindowProcW(hwnd, msg, wParam, lParam);
	}

	auto connector = reinterpret_cast<AsyncConnector*>(GetWindowLongPtrW(hwnd, GWLP_USERDATA));
	if (connector && msg == WM_PIME_ASYNC_DONE) {
		connector->onWindowMessage();
		return 0;
	}

	return DefWindowProcW(hwnd, msg, wParam, lParam);
}

bool AsyncConnector::connect(std::wstring pipeName, nlohmann::json initRequest, AsyncConnectCallback callback) {
	std::lock_guard<std::mutex> lock(mutex_);
	if (isCancelled_ || hwnd_ != NULL) {
		return false;
	}

	pipeName_ = std::move(pipeName);
	initRequest_ = std::move(initRequest);
	callback_ = std::move(callback);

	hwnd_ = createMessageOnlyWindow(this);
	if (!hwnd_) {
		return false;
	}

	auto self = shared_from_this();
	auto context = new std::shared_ptr<AsyncConnector>(self);

	BOOL submitted = TrySubmitThreadpoolCallback(
		[](PTP_CALLBACK_INSTANCE instance, PVOID param) {
			// Inform the Windows threadpool that this task may block on pipe I/O.
			// This allows the threadpool scheduler to allocate a replacement worker thread,
			// preventing thread starvation in the pool.
			CallbackMayRunLong(instance);

			// Prevent DLL unloading race conditions:
			// If the host application unloads PIMETextService.dll while this worker is running,
			// the thread would crash when returning into unmapped memory.
			// 1. getSelfModuleHandle(addRef=true) increments the DLL reference count via GetModuleHandleEx.
			// 2. FreeLibraryWhenCallbackReturns instructs the OS threadpool to call FreeLibrary()
			//    only AFTER this callback completes and its stack frames have popped.
			//    This keeps the DLL loaded for the entire callback duration and cleanly balances the count.
			HMODULE hModule = getSelfModuleHandle(/*addRef=*/true);
			if (hModule) {
				FreeLibraryWhenCallbackReturns(instance, hModule);
			}

			// Reclaim heap-allocated context and hold shared_ptr on the stack during execution.
			auto context = static_cast<std::shared_ptr<AsyncConnector>*>(param);
			auto conn = std::move(*context);
			delete context;

			conn->runWorker(instance);
		},
		context,
		nullptr
	);

	if (!submitted) {
		delete context;
		DestroyWindow(hwnd_);
		hwnd_ = NULL;
		return false;
	}

	return true;
}

void AsyncConnector::cancel() {
	HWND hwndToDestroy = NULL;
	{
		std::lock_guard<std::mutex> lock(mutex_);
		if (isCancelled_) {
			return;
		}
		isCancelled_ = true;
		callback_ = nullptr;

		hwndToDestroy = hwnd_;
		hwnd_ = NULL;

		pipe_.close();
	}

	if (hwndToDestroy) {
		DestroyWindow(hwndToDestroy);
	}
}

bool AsyncConnector::isCancelled() const {
	std::lock_guard<std::mutex> lock(mutex_);
	return isCancelled_;
}

void AsyncConnector::onWindowMessage() {
	auto self = shared_from_this();

	AsyncConnectCallback cb;
	RpcPipe pipe;
	nlohmann::json initResp;
	HWND hwndToDestroy = NULL;

	{
		std::lock_guard<std::mutex> lock(mutex_);
		hwndToDestroy = hwnd_;
		hwnd_ = NULL;

		if (!isCancelled_) {
			cb = std::move(callback_);
			pipe = std::move(pipe_);
			initResp = std::move(initResponse_);
		}
		else {
			pipe_.close();
		}
	}

	if (hwndToDestroy) {
		DestroyWindow(hwndToDestroy);
	}

	if (cb) {
		cb(std::move(pipe), std::move(initResp));
	}
}

void AsyncConnector::runWorker(PTP_CALLBACK_INSTANCE /*instance*/) {
	if (isCancelled()) {
		return;
	}

	// 1. Connect to named pipe with retries
	RpcPipe pipe;
	for (int attempt = 0; attempt < 3 && !isCancelled(); ++attempt) {
		pipe = RpcPipe::connect(pipeName_.c_str(), 1000);
		if (pipe.isValid()) {
			break;
		}
		if (attempt < 2 && !isCancelled()) {
			for (int i = 0; i < 10 && !isCancelled(); ++i) {
				Sleep(50);
			}
		}
	}

	if (isCancelled() || !pipe.isValid()) {
		std::lock_guard<std::mutex> lock(mutex_);
		if (!isCancelled_ && hwnd_) {
			PostMessageW(hwnd_, WM_PIME_ASYNC_DONE, 0, 0);
		}
		return;
	}

	// 2. Perform init RPC handshake in the background.
	// Initializing the backend (launching Python/Node.js runtimes and loading language
	// dictionaries) can take several seconds. Doing this off the UI thread prevents host UI freezes.
	nlohmann::json initReq = initRequest_;
	initReq["seqNum"] = 1;

	std::string initReply;
	bool ok = pipe.callRpc(initReq.dump(), initReply, kDefaultRpcTimeoutMs);
	nlohmann::json initRespJson;
	if (ok) {
		initRespJson = parseJsonNoThrow(initReply);
		// Validate that the reply is valid JSON, an object, and matches our sequence number.
		if (initRespJson.is_discarded() || !initRespJson.is_object() ||
		    jsonValueOr<int>(initRespJson, "seqNum", 0) != 1) {
			ok = false;
		}
	}

	HWND targetHwnd = NULL;
	{
		std::lock_guard<std::mutex> lock(mutex_);
		// If cancel() was called while the init RPC was in flight, discard the pipe immediately.
		if (isCancelled_ || !ok) {
			pipe.close();
		}
		else {
			// Handshake succeeded: store pipe and response for UI thread dispatching.
			pipe_ = std::move(pipe);
			initResponse_ = std::move(initRespJson);
			success_ = true;
		}
		// Capture hwnd_ under lock; posting is performed outside the lock to avoid lock contention.
		targetHwnd = hwnd_;
	}

	// Dispatch completion back to the UI thread via message queue.
	// PostMessageW is non-blocking and safe to call from any worker thread.
	if (targetHwnd) {
		PostMessageW(targetHwnd, WM_PIME_ASYNC_DONE, 0, 0);
	}
}

} // namespace PIME
