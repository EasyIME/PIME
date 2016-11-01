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

#include "PipeServer.h"
#include <Windows.h>
#include <ShlObj.h>
#include <Shellapi.h>
#include <Lmcons.h> // for UNLEN
#include <cstring>
#include <cassert>
#include <string>
#include <vector>
#include <map>
#include <fstream>
#include <algorithm>
#include <json/json.h>

using namespace std;

namespace PIME {

PipeServer* PipeServer::singleton_ = nullptr;

PipeServer::PipeServer() :
	pendingPipeConnection_(false),
	quitExistingLauncher_(false) {
	// this can only be assigned once
	assert(singleton_ == nullptr);
	singleton_ = this;

	// get the PIME directory
	wchar_t topDirPathBuf[MAX_PATH];
	DWORD len = GetModuleFileNameW(NULL, topDirPathBuf, MAX_PATH);
	topDirPathBuf[len] = '\0';
	wchar_t* p = wcsrchr(topDirPathBuf, '\\');
	if (p)
		*p = '\0';

	topDirPath_ = topDirPathBuf;

	// must set CWD to our dir. otherwise the backends won't launch.
	::SetCurrentDirectoryW(topDirPath_.c_str());
}

PipeServer::~PipeServer() {
	if (connectPipeOverlapped_.hEvent != INVALID_HANDLE_VALUE)
		CloseHandle(connectPipeOverlapped_.hEvent);

	if (everyoneSID_ != nullptr)
		FreeSid(everyoneSID_);
	if (allAppsSID_ != nullptr)
		FreeSid(allAppsSID_);
	if (securittyDescriptor_ != nullptr)
		LocalFree(securittyDescriptor_);
	if (acl_ != nullptr)
		LocalFree(acl_);
}

string PipeServer::getPipeName(const char* base_name) {
	string pipe_name;
	char username[UNLEN + 1];
	DWORD unlen = UNLEN + 1;
	if (GetUserNameA(username, &unlen)) {
		// add username to the pipe path so it will not clash with other users' pipes.
		pipe_name = "\\\\.\\pipe\\";
		pipe_name += username;
		pipe_name += "\\PIME\\";
		pipe_name += base_name;
	}
	return pipe_name;
}

void PipeServer::parseCommandLine(LPSTR cmd) {
	int argc;
	wchar_t** argv = CommandLineToArgvW(GetCommandLine(), &argc);
	// parse command line options
	for (int i = 1; i < argc; ++i) {
		const wchar_t* arg = argv[i];
		if (wcscmp(arg, L"/quit") == 0)
			quitExistingLauncher_ = true;
	}
	LocalFree(argv);
}

// send IPC message "quit" to the existing PIME Launcher process.
void PipeServer::terminateExistingLauncher() {
	string pipe_name = getPipeName("Launcher");
	char buf[16];
	DWORD rlen;
	::CallNamedPipeA(pipe_name.c_str(), "quit", 4, buf, sizeof(buf) - 1, &rlen, 1000); // wait for 1 sec.
}

void PipeServer::quit() {
	BackendServer::finalize();
	ExitProcess(0); // quit PipeServer
}


void PipeServer::initSecurityAttributes() {
	// create security attributes for the pipe
	// http://msdn.microsoft.com/en-us/library/windows/desktop/hh448449(v=vs.85).aspx
	// define new Win 8 app related constants
	memset(&explicitAccesses_, 0, sizeof(explicitAccesses_));
	// Create a well-known SID for the Everyone group.
	// FIXME: we should limit the access to current user only
	// See this article for details: https://msdn.microsoft.com/en-us/library/windows/desktop/hh448493(v=vs.85).aspx

	SID_IDENTIFIER_AUTHORITY worldSidAuthority = SECURITY_WORLD_SID_AUTHORITY;
	AllocateAndInitializeSid(&worldSidAuthority, 1,
		SECURITY_WORLD_RID, 0, 0, 0, 0, 0, 0, 0, &everyoneSID_);

	// https://services.land.vic.gov.au/ArcGIS10.1/edESRIArcGIS10_01_01_3143/Python/pywin32/PLATLIB/win32/Demos/security/explicit_entries.py

	explicitAccesses_[0].grfAccessPermissions = GENERIC_ALL;
	explicitAccesses_[0].grfAccessMode = SET_ACCESS;
	explicitAccesses_[0].grfInheritance = SUB_CONTAINERS_AND_OBJECTS_INHERIT;
	explicitAccesses_[0].Trustee.pMultipleTrustee = NULL;
	explicitAccesses_[0].Trustee.MultipleTrusteeOperation = NO_MULTIPLE_TRUSTEE;
	explicitAccesses_[0].Trustee.TrusteeForm = TRUSTEE_IS_SID;
	explicitAccesses_[0].Trustee.TrusteeType = TRUSTEE_IS_WELL_KNOWN_GROUP;
	explicitAccesses_[0].Trustee.ptstrName = (LPTSTR)everyoneSID_;

	// FIXME: will this work under Windows 7 and Vista?
	// create SID for app containers
	SID_IDENTIFIER_AUTHORITY appPackageAuthority = SECURITY_APP_PACKAGE_AUTHORITY;
	AllocateAndInitializeSid(&appPackageAuthority,
		SECURITY_BUILTIN_APP_PACKAGE_RID_COUNT,
		SECURITY_APP_PACKAGE_BASE_RID,
		SECURITY_BUILTIN_PACKAGE_ANY_PACKAGE,
		0, 0, 0, 0, 0, 0, &allAppsSID_);

	explicitAccesses_[1].grfAccessPermissions = GENERIC_ALL;
	explicitAccesses_[1].grfAccessMode = SET_ACCESS;
	explicitAccesses_[1].grfInheritance = SUB_CONTAINERS_AND_OBJECTS_INHERIT;
	explicitAccesses_[1].Trustee.pMultipleTrustee = NULL;
	explicitAccesses_[1].Trustee.MultipleTrusteeOperation = NO_MULTIPLE_TRUSTEE;
	explicitAccesses_[1].Trustee.TrusteeForm = TRUSTEE_IS_SID;
	explicitAccesses_[1].Trustee.TrusteeType = TRUSTEE_IS_GROUP;
	explicitAccesses_[1].Trustee.ptstrName = (LPTSTR)allAppsSID_;

	// create DACL
	DWORD err = SetEntriesInAcl(2, explicitAccesses_, NULL, &acl_);
	if (0 == err) {
		// security descriptor
		securittyDescriptor_ = (PSECURITY_DESCRIPTOR)LocalAlloc(LPTR, SECURITY_DESCRIPTOR_MIN_LENGTH);
		InitializeSecurityDescriptor(securittyDescriptor_, SECURITY_DESCRIPTOR_REVISION);

		// Add the ACL to the security descriptor. 
		SetSecurityDescriptorDacl(securittyDescriptor_, TRUE, acl_, FALSE);
	}

	securityAttributes_.nLength = sizeof(SECURITY_ATTRIBUTES);
	securityAttributes_.lpSecurityDescriptor = securittyDescriptor_;
	securityAttributes_.bInheritHandle = TRUE;
}


// References:
// https://msdn.microsoft.com/en-us/library/windows/desktop/aa365588(v=vs.85).aspx
HANDLE PipeServer::createPipe(const wchar_t* app_name) {
	HANDLE pipe = INVALID_HANDLE_VALUE;
	wchar_t username[UNLEN + 1];
	DWORD unlen = UNLEN + 1;
	if (GetUserNameW(username, &unlen)) {
		// add username to the pipe path so it will not clash with other users' pipes.
		wchar_t pipe_name[MAX_PATH];
		wsprintf(pipe_name, L"\\\\.\\pipe\\%s\\PIME\\%s", username, app_name);
		const size_t buffer_size = 1024;
		// create the pipe
		pipe = CreateNamedPipeW(pipe_name,
			PIPE_ACCESS_DUPLEX | FILE_FLAG_OVERLAPPED,
			PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE | PIPE_WAIT,
			PIPE_UNLIMITED_INSTANCES,
			buffer_size,
			buffer_size,
			NMPWAIT_USE_DEFAULT_WAIT,
			&securityAttributes_);
	}
	return pipe;
}

void PipeServer::closePipe(HANDLE pipe) {
	FlushFileBuffers(pipe);
	DisconnectNamedPipe(pipe);
	CloseHandle(pipe);
}


HANDLE PipeServer::acceptClientPipe() {
	HANDLE client_pipe = createPipe(L"Launcher");
	if (client_pipe != INVALID_HANDLE_VALUE) {
		if (ConnectNamedPipe(client_pipe, &connectPipeOverlapped_)) {
			// connection to client succeded without blocking (the event is signaled)
			pendingPipeConnection_ = false;
		}
		else { // connection fails
			switch (GetLastError()) {
			case ERROR_IO_PENDING:
				// The overlapped connection in progress and we need to wait
				pendingPipeConnection_ = true;
				break;
			case ERROR_PIPE_CONNECTED:
				// the client is already connected before we call ConnectNamedPipe()
				SetEvent(connectPipeOverlapped_.hEvent); // signal the event manually
				pendingPipeConnection_ = false;
				break;
			default: // unknown errors
				pendingPipeConnection_ = false;
				CloseHandle(client_pipe);
				client_pipe = INVALID_HANDLE_VALUE;
			}
		}
	}
	return client_pipe;
}


int PipeServer::exec(LPSTR cmd) {
	parseCommandLine(cmd);
	if (quitExistingLauncher_) { // terminate existing launcher process
		terminateExistingLauncher();
		return 0;
	}

	// this is the first instance
	BackendServer::init(topDirPath_);

	// preparing for the server pipe
	initSecurityAttributes();
	// notification for new incoming connections
	memset(&connectPipeOverlapped_, 0, sizeof(connectPipeOverlapped_));
	// event used to notify new incoming pipe connections
	connectPipeOverlapped_.hEvent = CreateEvent(NULL, TRUE, TRUE, NULL);
	if (connectPipeOverlapped_.hEvent == NULL)
		return -1;

	// main server loop, accepting new incoming clients
	HANDLE client_pipe = acceptClientPipe();
	for (;;) {
		// wait for incoming pipe connection to complete
		DWORD waitResult = WaitForSingleObjectEx(connectPipeOverlapped_.hEvent, INFINITE, TRUE);
		switch (waitResult) {
		case WAIT_OBJECT_0:  // new incoming connection (ConnectNamedPipe() is finished)
			if (pendingPipeConnection_) {
				DWORD rlen;
				bool success = GetOverlappedResult(client_pipe, &connectPipeOverlapped_, &rlen, FALSE);
				if (!success) { // connection failed
					closePipe(client_pipe);
					client_pipe = INVALID_HANDLE_VALUE;
				}
			}

			// handle the newly connected client
			if (client_pipe != INVALID_HANDLE_VALUE) {
				ClientInfo* client = new ClientInfo(client_pipe);
				clients_[client_pipe] = client;
				readClient(client);  // read data from the client asynchronously
			}

			// try to accept the next client connection
			client_pipe = acceptClientPipe();
			break;
		case WAIT_IO_COMPLETION:  // some overlapped I/O is finished (handled in completion routines)
			while (!finishedRequests_.empty()) {
				AsyncRequest* req = finishedRequests_.front();
				finishedRequests_.pop();
				switch (req->type_) {
				case AsyncRequest::ASYNC_READ:
					onReadFinished(req);
					break;
				case AsyncRequest::ASYNC_WRITE:
					onWriteFinished(req);
					break;
				}
				delete req;
			}
			break;
		default:
			return -1;  // some unknown errors hapened
		}
	}
	return 0;
}

void PipeServer::readClient(ClientInfo* client) {
	AsyncRequest* req = new AsyncRequest(this, client, AsyncRequest::ASYNC_READ, 1024, nullptr);
	ReadFileEx(client->pipe_, req->buf_, req->bufSize_, (OVERLAPPED*)req, &_onFinishedCallback);
}

void PipeServer::writeClient(ClientInfo* client, const char* data, int len) {
	AsyncRequest* req = new AsyncRequest(this, client, AsyncRequest::ASYNC_WRITE, len, data);
	WriteFileEx(client->pipe_, req->buf_, req->bufSize_, (OVERLAPPED*)req, &_onFinishedCallback);
}

// static
void CALLBACK PipeServer::_onFinishedCallback(DWORD err, DWORD numBytes, OVERLAPPED* overlapped) {
	AsyncRequest* req = reinterpret_cast<AsyncRequest*>(overlapped);
	req->errCode_ = err;
	req->numBytes_ = numBytes;
	req->server_->finishedRequests_.push(req);
}

void PipeServer::onReadFinished(AsyncRequest* req) {
	if (req->numBytes_ > 0) {
		req->client_->readBuf_.append(req->buf_, req->numBytes_);
	}

	switch (req->errCode_) {
	case 0: // finish of this message
		// TODO: call the backend to handle the message
		handleClientMessage(req->client_);
		break;
	case ERROR_MORE_DATA: // need further reads to get the whole message
		readClient(req->client_);
		break;
	case ERROR_IO_PENDING:
		break;
	default: // the pipe is broken, disconnect!
		closeClient(req->client_);
	}
}


void PipeServer::onWriteFinished(AsyncRequest* req) {
	readClient(req->client_);  // read more data from this client
}

void PipeServer::handleClientMessage(ClientInfo* client) {
	// special handling, asked for quitting PIMELauncher.
	if (client->readBuf_ == "quit") {
		quit();
		return;
	}

	// call the backend to handle this message
	if (client->backend_ == nullptr) {
		// backend is unknown, parse the json
		Json::Value msg;
		Json::Reader reader;
		if (reader.parse(client->readBuf_, msg)) {
			const char* method = msg["method"].asCString();
			if (method != nullptr) {
				if (strcmp(method, "init") == 0) {  // the client connects to us the first time
					const char* guid = msg["id"].asCString();
					client->backend_ = BackendServer::fromLangProfileGuid(guid);
					if (client->backend_ == nullptr) {
						// FIXME: write some response to indicate the failure
						return;
					}
					client->clientId_ = client->backend_->addNewClient();
				}
			}
		}
		if (client->backend_ == nullptr) {
			// fail to find a usable backend
			client->readBuf_.clear();
			// FIXME: write some response to indicate the failure
			return;
		}
	}
	// pass the incoming message to the backend and get the response
	std::string response = client->backend_->handleClientMessage(client->clientId_, client->readBuf_);
	client->readBuf_.clear();

	// pass the response back to the client
	writeClient(client, response.c_str(), response.length());
}

void PipeServer::closeClient(ClientInfo* client) {
	if (client->backend_ != nullptr) {
		if (!client->clientId_.empty())
			client->backend_->removeClient(client->clientId_);
	}

	clients_.erase(client->pipe_);
	if (client->pipe_ != INVALID_HANDLE_VALUE)
		::CloseHandle(client->pipe_);
	// FIXME: if the client has some pending requests, how to cancel them?
	delete client;
}

} // namespace PIME