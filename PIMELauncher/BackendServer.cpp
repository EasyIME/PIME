//
//	Copyright (C) 2015 - 2016 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
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

#include <Windows.h>
#include <ShlObj.h>
#include <Shellapi.h>
#include <Lmcons.h> // for UNLEN
#include <Wincrypt.h>  // for CryptBinaryToString (used for base64 encoding)
#include <cstring>
#include <cassert>
#include <chrono>  // C++ 11 clock functions
#include <string>
#include <vector>
#include <map>
#include <fstream>
#include <algorithm>
#include <codecvt>  // for utf8 conversion
#include <locale>  // for wstring_convert

#include <json/json.h>

#include "BackendServer.h"
#include "PipeServer.h"

using namespace std;

static wstring_convert<codecvt_utf8<wchar_t>> utf8Codec;

namespace PIME {

BackendServer::BackendServer(PipeServer* pipeServer, const Json::Value& info) :
	pipeServer_{pipeServer},
	process_{ nullptr },
	stdinPipe_{nullptr},
	stdoutPipe_{nullptr},
	ready_{false},
	name_(info["name"].asString()),
	command_(info["command"].asString()),
	workingDir_(info["workingDir"].asString()),
	params_(info["params"].asString()) {
}

BackendServer::~BackendServer() {
	terminateProcess();
}

void BackendServer::handleClientMessage(ClientInfo * client, const char * readBuf, size_t len) {
	if (!isProcessRunning()) {
		startProcess();
	}

	// message format: <client_id>|<json string>\n
	string msg = string{ client->clientId_ };
	msg += "|";
	msg.append(readBuf, len);
	msg += "\n";

	// write the message to the backend server
	uv_buf_t buf = {msg.length(), (char*)msg.c_str()};
	uv_write_t* req = new uv_write_t{};
	uv_write(req, stdinStream(), &buf, 1, [](uv_write_t* req, int status) {
		delete req;
	});
}

void BackendServer::startProcess() {
	process_ = new uv_process_t{};
	process_->data = this;
	// create pipes for stdio of the child process
	stdinPipe_ = new uv_pipe_t{};
	stdinPipe_->data = this;
	uv_pipe_init(uv_default_loop(), stdinPipe_, 0);

	stdoutPipe_ = new uv_pipe_t{};
	stdoutPipe_->data = this;
	uv_pipe_init(uv_default_loop(), stdoutPipe_, 0);

	uv_stdio_container_t stdio_containers[3];
	stdio_containers[0].data.stream = stdinStream();
	stdio_containers[0].flags = uv_stdio_flags(UV_CREATE_PIPE | UV_READABLE_PIPE | UV_WRITABLE_PIPE);
	stdio_containers[1].data.stream = stdoutStream();
	stdio_containers[1].flags = uv_stdio_flags(UV_CREATE_PIPE | UV_READABLE_PIPE | UV_WRITABLE_PIPE);
	stdio_containers[2].data.stream = nullptr;
	stdio_containers[2].flags = UV_IGNORE;

	char full_exe_path[MAX_PATH];
	size_t cwd_len = MAX_PATH;
	uv_cwd(full_exe_path, &cwd_len);
	full_exe_path[cwd_len] = '\\';
	strcpy(full_exe_path + cwd_len + 1, command_.c_str());
	const char* argv[] = {
		full_exe_path,
		params_.c_str(),
		nullptr
	};
	uv_process_options_t options = { 0 };
	options.exit_cb = [](uv_process_t* process, int64_t exit_status, int term_signal) {
		reinterpret_cast<BackendServer*>(process->data)->onProcessTerminated(exit_status, term_signal);
	};
	options.flags = UV_PROCESS_WINDOWS_HIDE; //  UV_PROCESS_WINDOWS_VERBATIM_ARGUMENTS;
	options.file = argv[0];
	options.args = const_cast<char**>(argv);
	char full_working_dir[MAX_PATH];
	::GetFullPathNameA(workingDir_.c_str(), MAX_PATH, full_working_dir, nullptr);
	options.cwd = full_working_dir;

	// build our own new environments
	auto env_strs = GetEnvironmentStringsW();
	vector<string> utf8_environ;
	for (auto penv = env_strs; *penv; penv += wcslen(penv) + 1) {
		utf8_environ.emplace_back(utf8Codec.to_bytes(penv));
	}
	FreeEnvironmentStringsW(env_strs);
	// add our own environment variables
	// NOTE: Force python to output UTF-8 encoded strings
	// Reference: https://docs.python.org/3/using/cmdline.html#envvar-PYTHONIOENCODING
	// By default, python uses ANSI encoding in Windows and this breaks our unicode support.
	// FIXME: makes this configurable from backend.json.
	utf8_environ.emplace_back("PYTHONIOENCODING=utf-8:ignore");
	vector<const char*> env;
	for (auto& v : utf8_environ) {
		env.emplace_back(v.c_str());
	}
	env.emplace_back(nullptr);
	options.env = const_cast<char**>(env.data());

	options.stdio_count = 3;
	options.stdio = stdio_containers;
	int ret = uv_spawn(uv_default_loop(), process_, &options);
	if (ret < 0) {
		delete process_;
		process_ = nullptr;
		uv_close(reinterpret_cast<uv_handle_t*>(stdinPipe_), [](uv_handle_t* handle) {
			delete reinterpret_cast<uv_pipe_t*>(handle);
		});
		stdinPipe_ = nullptr;
		uv_close(reinterpret_cast<uv_handle_t*>(stdoutPipe_), [](uv_handle_t* handle) {
			delete reinterpret_cast<uv_pipe_t*>(handle);
		});
		stdoutPipe_ = nullptr;
		return;
	}

	// start receiving data from the backend server
	uv_read_start(stdoutStream(), allocReadBuf,
		[](uv_stream_t* stream, ssize_t nread, const uv_buf_t* buf) {
			reinterpret_cast<BackendServer*>(stream->data)->onProcessDataReceived(stream, nread, buf);
		}
	);
}

void BackendServer::terminateProcess() {
	if (process_) {
		closeStdioPipes();
		uv_process_kill(process_, SIGTERM);
	}
}

// check if the backend server process is running
bool BackendServer::isProcessRunning() {
	return process_ != nullptr;
}

void BackendServer::allocReadBuf(uv_handle_t *, size_t suggested_size, uv_buf_t * buf) {
	buf->base = new char[suggested_size];
	buf->len = suggested_size;
}

void BackendServer::onProcessDataReceived(uv_stream_t * stream, ssize_t nread, const uv_buf_t * buf) {
	if (nread < 0 || nread == UV_EOF) {
		if (buf->base) {
			delete[]buf->base;
		}
		// the backend server is broken, stop it
		terminateProcess();
		return;
	}
	if (buf->base) {
		// initial ready message from the backend server
		if (buf->base[0] == '\0') {
			ready_ = true;
		}
		else {
			// pass the reply to the main server for further handling and sending back to the client
			pipeServer_->handleBackendReply(buf->base, nread);
		}
		delete[]buf->base;
	}
}

void BackendServer::onProcessTerminated(int64_t exit_status, int term_signal) {
	delete process_;
	process_ = nullptr;

	closeStdioPipes();

	pipeServer_->onBackendClosed(this);
}

void BackendServer::closeStdioPipes() {
	ready_ = false;
	if (stdinPipe_ != nullptr) {
		uv_close(reinterpret_cast<uv_handle_t*>(stdinPipe_), [](uv_handle_t* handle) {
			delete reinterpret_cast<uv_pipe_t*>(handle);
		});
		stdinPipe_ = nullptr;
	}

	if (stdoutPipe_ != nullptr) {
		uv_close(reinterpret_cast<uv_handle_t*>(stdoutPipe_), [](uv_handle_t* handle) {
			delete reinterpret_cast<uv_pipe_t*>(handle);
		});
		stdoutPipe_ = nullptr;
	}
}

} // namespace PIME
