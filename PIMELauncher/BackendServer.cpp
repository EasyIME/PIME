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
#include <sstream>

#include <json/json.h>

#include "BackendServer.h"
#include "PipeServer.h"
#include "PipeClient.h"

using namespace std;

namespace PIME {

static wstring_convert<codecvt_utf8<wchar_t>> utf8Codec;
static constexpr auto MAX_RESPONSE_WAITING_TIME = 30;  // if a backend is non-responsive for 30 seconds, it's considered dead

static std::string getUtf8CurrentDir() {
    char dirPath[MAX_PATH];
    size_t len = MAX_PATH;
    uv_cwd(dirPath, &len);
    return dirPath;
}

static std::vector<std::string> getUtf8EnvironmentVariables() {
    // build our own new environments
    auto env_strs = GetEnvironmentStringsW();
    vector<string> utf8Environ;
    for (auto penv = env_strs; *penv; penv += wcslen(penv) + 1) {
        utf8Environ.emplace_back(utf8Codec.to_bytes(penv));
    }
    FreeEnvironmentStringsW(env_strs);
    return utf8Environ;
}

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
    stdinPipe_->write(std::move(msg));
}

uv::Pipe* BackendServer::createStdinPipe() {
    auto stdinPipe = new uv::Pipe();
    stdinPipe->setCloseCallback([stdinPipe]() {delete stdinPipe; });
    return stdinPipe;
}

uv::Pipe* BackendServer::createStdoutPipe() {
    auto stdoutPipe = new uv::Pipe();
    stdoutPipe->setReadCallback(
        [this](const char* buf, size_t len) {
            onStdoutRead(buf, len);
        }
    );
    stdoutPipe->setReadErrorCallback(
        [this](int error) {
            onReadError(error);
        }
    );
    stdoutPipe->setCloseCallback([stdoutPipe]() {delete stdoutPipe; });
    return stdoutPipe;
}

uv::Pipe* BackendServer::createStderrPipe() {
    auto stderrPipe = new uv::Pipe();
    stderrPipe->setReadCallback(
        [this](const char* buf, size_t len) {
            onStderrRead(buf, len);
        }
    );
    stderrPipe->setReadErrorCallback(
        [this](int error) {
            onReadError(error);
        }
    );
    stderrPipe->setCloseCallback([this, stderrPipe]() {delete stderrPipe; });
    return stderrPipe;
}

void BackendServer::startProcess() {
	process_ = new uv_process_t{};
	process_->data = this;
	// create pipes for stdio of the child process
    stdoutPipe_ = createStdoutPipe();
    stdoutReadBuf_.clear();
    stdinPipe_ = createStdinPipe();
    stderrPipe_ = createStderrPipe();

    constexpr auto pipeFlags = uv_stdio_flags(UV_CREATE_PIPE | UV_READABLE_PIPE | UV_WRITABLE_PIPE);
	uv_stdio_container_t stdio_containers[3];
    stdio_containers[0].data.stream = stdinPipe_->streamHandle();
	stdio_containers[0].flags = pipeFlags;
    stdio_containers[1].data.stream = stdoutPipe_->streamHandle();
	stdio_containers[1].flags = pipeFlags;
    stdio_containers[2].data.stream = stderrPipe_->streamHandle();
	stdio_containers[2].flags = pipeFlags;

    auto utf8CurrentDirPath = getUtf8CurrentDir();
    auto executablePath = utf8CurrentDirPath + '\\' + command_;
	const char* argv[] = {
        executablePath.c_str(),
		params_.c_str(),
		nullptr
	};
	uv_process_options_t options = { 0 };
	options.exit_cb = [](uv_process_t* process, int64_t exit_status, int term_signal) {
		reinterpret_cast<BackendServer*>(process->data)->onProcessTerminated(exit_status, term_signal);
	};
	options.flags = UV_PROCESS_WINDOWS_HIDE; //  UV_PROCESS_WINDOWS_VERBATIM_ARGUMENTS;
    options.file = executablePath.c_str();
	options.args = const_cast<char**>(argv);

    auto backendWorkingDirPath = utf8CurrentDirPath + '\\' + workingDir_;
	options.cwd = backendWorkingDirPath.c_str();

	// build our own new environments
    auto utf8EnvVars = getUtf8EnvironmentVariables();
	// add our own environment variables
	// NOTE: Force python to output UTF-8 encoded strings
	// Reference: https://docs.python.org/3/using/cmdline.html#envvar-PYTHONIOENCODING
	// By default, python uses ANSI encoding in Windows and this breaks our unicode support.
	// FIXME: makes this configurable from backend.json.
	utf8EnvVars.emplace_back("PYTHONIOENCODING=utf-8:ignore");

    // convert to a null terminated char* array.
	std::vector<const char*> env;
	for (auto& v : utf8EnvVars) {
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
    stdoutPipe_->startRead();
    stderrPipe_->startRead();
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

void BackendServer::onStdoutRead(const char* buf, size_t len) {
    // print to debug log if there is any
    logger()->debug("RECV: {}", std::string(buf, len));

    // initial ready message from the backend server
    if (!ready_ && buf[0] == '\0') {
        ready_ = true;
        // skip the first byte, and add the received data to our buffer
        // FIXME: this is not very reliable
        stdoutReadBuf_.write(buf + 1, len - 1);
    }
    else {
        // add the received data to our buffer
        stdoutReadBuf_.write(buf, len);
    }

    handleBackendReply();
}

void BackendServer::onReadError(int status) {
    // the backend server is broken, stop it
    terminateProcess();
}

void BackendServer::onStderrRead(const char* buf, size_t len) {
    // FIXME: need to do output buffering since we might not receive a full line
    // log the error message
    logger()->error("[Backend error] {}", std::string(buf, len));
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
        stdinPipe_->close();
		stdinPipe_ = nullptr;
	}

	if (stdoutPipe_ != nullptr) {
        stdoutPipe_->close();
		stdoutPipe_ = nullptr;
        stdoutReadBuf_ = std::stringstream();
    }

	if (stderrPipe_ != nullptr) {
        stderrPipe_->close();
		stderrPipe_ = nullptr;
	}
}

void BackendServer::handleBackendReply() {
	// each output message should be a full line ends with \n or \r\n, so we need to do buffering and
	// handle the messages line by line.
    std::string line;
	for (;;) {
        std::getline(stdoutReadBuf_, line);
        if (stdoutReadBuf_.eof()) {
            // getline() reached end of buffer before finding a '\n'. The current line is incomplete.
            // Put remaining data back to the buffer and wait for the next \n so it becomes a full line.
            stdoutReadBuf_.clear();
            stdoutReadBuf_.str(line);
            break;
        }

		// only handle lines prefixed with "PIME_MSG|" since other lines
		// might be debug messages printed by the backend.
		// Format of each message: "PIMG_MSG|<client_id>|<reply JSON string>\n"
        constexpr char pimeMsgPrefix[] = "PIME_MSG|";
        constexpr size_t pimeMsgPrefixLen = 9;
		if (line.compare(0, pimeMsgPrefixLen, pimeMsgPrefix) == 0) {
            // because Windows uses CRLF "\r\n" for new lines, python and node.js
            // try to convert "\n" to "\r\n" sometimes. Let's remove the additional '\r'
            if (line.back() == '\r') {
                line.pop_back();
            }

            auto sep = line.find('|', pimeMsgPrefixLen);  // Find the next "|".
			if (sep != line.npos) {
				// split the client_id from the remaining json reply
				string clientId = line.substr(pimeMsgPrefixLen, sep - pimeMsgPrefixLen);
                // send the reply message back to the client
                auto msgStart = sep + 1;
                auto msg = line.c_str() + msgStart;
				auto msgLen = line.length() - msgStart;
				if (auto client = pipeServer_->clientFromId(clientId)) {
					client->writePipe(msg, msgLen);
				}
			}
		}
	}
}

} // namespace PIME
