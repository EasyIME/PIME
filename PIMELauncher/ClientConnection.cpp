#include "ClientConnection.h"
#include "BackendServer.h"
#include "PIMELauncher.h"
#include <json/json.h>

using namespace std;

ClientConnection::ClientConnection(HANDLE pipe, PIMELauncher* server):
	server_(server),
	pipe_(pipe),
	backendServer_(nullptr),
	readClientOverlapped_{0} {
}

ClientConnection::~ClientConnection() {
	close();
}

void ClientConnection::close() {
	if (pipe_ != INVALID_HANDLE_VALUE) {
		FlushFileBuffers(pipe_);
		DisconnectNamedPipe(pipe_);
		CloseHandle(pipe_);
		pipe_ = INVALID_HANDLE_VALUE;
	}

	// FIXME: remove from server?
}

void ClientConnection::asyncReadClient() {
	ReadFileEx(pipe_, readClientBuf_, sizeof(readClientBuf_) - 1, &readClientOverlapped_, &_onAsyncReadClientFinished);
}

void ClientConnection::asyncReadBackend() {
	ReadFileEx(backendServer_->stdout_, readBackendBuf_, sizeof(readBackendBuf_) - 1, &readBackendOverlapped_, &_onAsyncReadBackendFinished);
}

void ClientConnection::onAsyncReadClientFinished(DWORD err, DWORD numBytes) {
	if (numBytes > 0) {
		readClientBuf_[numBytes] = '\0';
		currentMsg_ += readClientBuf_;
	}

	switch (err) {
	case 0: // finish of this message
		handleClientRequest();
		break;
	case ERROR_MORE_DATA: // need further reads
		asyncReadClient();
		break;
	case ERROR_IO_PENDING:
		break;
	default: // the pipe is broken, disconnect!
		close();
	}
}

void ClientConnection::onAsyncWriteClientFinished(DWORD err, DWORD numBytes) {
}

void ClientConnection::onAsyncReadBackendFinished(DWORD err, DWORD numBytes) {
	if (numBytes > 0) {
		readBackendBuf_[numBytes] = '\0';
		currentReply_ += readBackendBuf_;
	}

	switch (err) {
	case 0: // finish of this message
		handleBackendReply();
		break;
	case ERROR_MORE_DATA: // need further reads
		asyncReadBackend();
		break;
	case ERROR_IO_PENDING:
		break;
	default: // the pipe is broken, disconnect!
		close();
	}
}

void ClientConnection::onAsyncWriteBackendFinished(DWORD err, DWORD numBytes) {
}

void ClientConnection::handleClientRequest() {
	if (backendServer_ == nullptr) {  // the client does not have an associated backend yet
		string reply;
		Json::Value msg;
		Json::Reader reader;
		if (reader.parse(currentMsg_, msg)) {
			const char* method = msg["method"].asCString();
			if (method != nullptr) {
				BackendServer* backend = nullptr;
				if (strcmp(method, "init") == 0) {
					// the client connects to us the first time
					const char* guid = msg["id"].asCString();
					// find the backend required by the text service
					backendServer_ = server_->findBackendForClient(guid);
				}
			}
		}
		if (backendServer_ == nullptr)  // no valid backend is found
			return;
	}

	// ensure that the backend is running
	
	if (!backendServer_->isRunning())
		backendServer_->start();

	// read the result from the backend
	asyncReadBackend();

	// redirect the message got from the client to the backend
	// WriteFileEx(backendServer_->stdin_, currentMsg_.c_str(), currentMsg_.length(), &writeBackendOverlapped_, &_onAsyncWriteBackendFinished);

	// currentMsg_.clear();
}

void ClientConnection::handleBackendReply() {
	WriteFileEx(pipe_, currentReply_.c_str(), currentReply_.length(), &writeClientOverlapped_, &_onAsyncWriteClientFinished);
	// currentReply_.clear();
}
