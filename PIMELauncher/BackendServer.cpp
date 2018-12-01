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
#include "PipeClient.h"

using namespace std;

namespace PIME {

static wstring_convert<codecvt_utf8<wchar_t>> utf8Codec;
static constexpr auto MAX_RESPONSE_WAITING_TIME = 30;  // if a backend is non-responsive for 30 seconds, it's considered dead


BackendServer::BackendServer(PipeServer* pipeServer, const Json::Value& info) :
	pipeServer_{pipeServer},
	process_{ nullptr },
	stdinPipe_{nullptr},
	stdoutPipe_{nullptr},
	stderrPipe_{nullptr},
	ready_{false},
	name_(info["name"].asString()),
	needRestart_{false},
	command_(info["command"].asString()),
	workingDir_(info["workingDir"].asString()),
	params_(info["params"].asString()) {
}

BackendServer::~BackendServer() {
	terminateProcess();
}

std::shared_ptr<spdlog::logger>& BackendServer::logger() {
	return pipeServer_->logger();
}

void BackendServer::handleClientMessage(PipeClient * client, const char * readBuf, size_t len) {
	if (!isProcessRunning()) {
		startProcess();
	}

	// message format: <client_id>|<json string>\n
	string msg = string{ client->clientId_ };
	msg += "|";
	msg.append(readBuf, len);
	msg += "\n";

	logger()->debug("SEND: {}", msg);

	// write the message to the backend server
	writeInputPipe(msg.c_str(), msg.length());
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
	stdoutReadBuf_.clear();

	stderrPipe_ = new uv_pipe_t{};
	stderrPipe_->data = this;
	uv_pipe_init(uv_default_loop(), stderrPipe_, 0);

	uv_stdio_container_t stdio_containers[3];
	stdio_containers[0].data.stream = stdinStream();
	stdio_containers[0].flags = uv_stdio_flags(UV_CREATE_PIPE | UV_READABLE_PIPE | UV_WRITABLE_PIPE);
	stdio_containers[1].data.stream = stdoutStream();
	stdio_containers[1].flags = uv_stdio_flags(UV_CREATE_PIPE | UV_READABLE_PIPE | UV_WRITABLE_PIPE);
	stdio_containers[2].data.stream = stderrStream();
	stdio_containers[2].flags = uv_stdio_flags(UV_CREATE_PIPE | UV_READABLE_PIPE | UV_WRITABLE_PIPE);

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
		closeStdioPipes();
		return;
	}

	// start receiving data from the backend server
	startReadOutputPipe();
	startReadErrorPipe();
}

void BackendServer::restartProcess() {
	if (!needRestart_) {
		needRestart_ = true;
		terminateProcess();
	}
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
	// FIXME: need to do output buffering since we might not receive a full line
	if (nread < 0 || nread == UV_EOF) {
		if (buf->base) {
			delete[]buf->base;
		}
		// the backend server is broken, stop it
		terminateProcess();
		return;
	}
	if (buf->base) {
		// print to debug log if there is any
		logger()->debug("RECV: {}", std::string(buf->base, buf->len));

		// initial ready message from the backend server
		if (!ready_ && buf->base[0] == '\0') {
			ready_ = true;
			// skip the first byte, and add the received data to our buffer
			// FIXME: this is not very reliable
			stdoutReadBuf_.append(buf->base + 1, buf->len - 1);
		}
		else {
			// add the received data to our buffer
			stdoutReadBuf_.append(buf->base, buf->len);
		}

		handleBackendReply();

		delete[]buf->base;
	}
}

void BackendServer::onProcessErrorReceived(uv_stream_t * stream, ssize_t nread, const uv_buf_t * buf) {
	// FIXME: need to do output buffering since we might not receive a full line
	if (nread < 0 || nread == UV_EOF) {
		if (buf->base) {
			delete[]buf->base;
		}
		// the backend server is broken, stop it
		terminateProcess();
		return;
	}
	if (buf->base) {
		// log the error message
		logger()->error("[Backend error] {}", std::string(buf->base, buf->len));
		delete[]buf->base;
	}
}

void BackendServer::onProcessTerminated(int64_t exit_status, int term_signal) {
	delete process_;
	process_ = nullptr;

	closeStdioPipes();

	pipeServer_->onBackendClosed(this);

	if (needRestart_) {
		startProcess();
		needRestart_ = false;
	}
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
		stdoutReadBuf_.clear();
	}

	if (stderrPipe_ != nullptr) {
		uv_close(reinterpret_cast<uv_handle_t*>(stderrPipe_), [](uv_handle_t* handle) {
			delete reinterpret_cast<uv_pipe_t*>(handle);
		});
		stderrPipe_ = nullptr;
	}
}

void BackendServer::handleBackendReply() {
	// each output message should be a full line ends with \n or \r\n, so we need to do buffering and
	// handle the messages line by line.
	auto lineStartPos = 0;
	for (;;) {
		auto lineEndPos = stdoutReadBuf_.find('\n', lineStartPos);
		if (lineEndPos != stdoutReadBuf_.npos) {
			auto lineLen = lineEndPos - lineStartPos;
			auto line = stdoutReadBuf_.c_str() + lineStartPos;
			auto lineEnd = line + lineLen;

			// only handle lines prefixed with "PIME_MSG|" since other lines
			// might be debug messages printed by the backend.
			// Format of each message: "PIMG_MSG|<client_id>|<reply JSON string>\n"
			if (strncmp(line, "PIME_MSG|", 9) == 0) {
				line += 9; // Skip the "PIME_MSG|" prefix
				if (auto sep = strchr(line, '|')) {
					// split the client_id from the remaining json reply
					string clientId(line, sep - line);
					auto msg = sep + 1;
					auto msgLen = lineEnd - msg;
					// because Windows uses CRLF "\r\n" for new lines, python and node.js
					// try to convert "\n" to "\r\n" sometimes. Let's remove the additional '\r'
					if (msgLen > 0 && msg[msgLen - 1] == '\r') {
						--msgLen;
					}

					// send the reply message back to the client
					if (auto client = pipeServer_->clientFromId(clientId)) {
						client->writePipe(msg, msgLen);
					}
				}
			}

			// skip empty lines or additional CRLF, and go to the next non-empty line
			lineStartPos = lineEndPos + 1;
		}
		else {
			break;
		}
	}
	// Leave remaining data not processed in the buffer, waiting for the next \n so it becomes a full line.
	stdoutReadBuf_ = stdoutReadBuf_.substr(lineStartPos);
}

void BackendServer::startReadOutputPipe() {
	uv_read_start(stdoutStream(), allocReadBuf,
		[](uv_stream_t* stream, ssize_t nread, const uv_buf_t* buf) {
			reinterpret_cast<BackendServer*>(stream->data)->onProcessDataReceived(stream, nread, buf);
		}
	);
}

void BackendServer::startReadErrorPipe() {
	uv_read_start(stderrStream(), allocReadBuf,
		[](uv_stream_t* stream, ssize_t nread, const uv_buf_t* buf) {
		reinterpret_cast<BackendServer*>(stream->data)->onProcessErrorReceived(stream, nread, buf);
	}
	);
}

void BackendServer::writeInputPipe(const char* data, size_t len) {
	// The memory pointed to by the buffers must remain valid until the callback gets called. 
	// http://docs.libuv.org/en/v1.x/stream.html
	// So we need to copy the buffer
	char* copiedData = new char[len];
	memcpy(copiedData, data, len);
	uv_buf_t buf = { len, copiedData };
	uv_write_t* req = new uv_write_t{};
	req->data = copiedData;
	uv_write(req, stdinStream(), &buf, 1, [](uv_write_t* req, int status) {
		char* copiedData = reinterpret_cast<char*>(req->data);
		delete[]copiedData;
		delete req;
	});
}

} // namespace PIME
