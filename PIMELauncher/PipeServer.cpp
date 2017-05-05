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
#include <iostream>
#include <cstring>
#include <cassert>
#include <string>
#include <vector>
#include <map>
#include <fstream>
#include <algorithm>
#include <codecvt>  // for utf8 conversion
#include <locale>  // for wstring_convert

#include <json/json.h>

#include "BackendServer.h"
#include "Utils.h"
#include "../libIME/WindowsVersion.h"

using namespace std;

static wstring_convert<codecvt_utf8<wchar_t>> utf8Codec;

namespace PIME {

PipeServer* PipeServer::singleton_ = nullptr;


ClientInfo::ClientInfo(PipeServer* server) :
	backend_(nullptr), server_{ server } {
}

bool ClientInfo::isInitialized() const {
	return (!clientId_.empty() && backend_ != nullptr);
}

bool ClientInfo::init(const Json::Value & params) {
	const char* method = params["method"].asCString();
	if (method != nullptr) {
		if (strcmp(method, "init") == 0) {  // the client connects to us the first time
			// generate a new uuid for client ID
			UUID uuid;
			UuidCreate(&uuid);
			RPC_CSTR uuid_str = nullptr;
			UuidToStringA(&uuid, &uuid_str);
			clientId_ = (char*)uuid_str;
			RpcStringFreeA(&uuid_str);

			// find a backend for the client text service
			const char* guid = params["id"].asCString();
			backend_ = server_->backendFromLangProfileGuid(guid);
			if (backend_ != nullptr) {
				// FIXME: write some response to indicate the failure
				return true;
			}
		}
	}
	return false;
}


PipeServer::PipeServer() :
	securittyDescriptor_(nullptr),
	acl_(nullptr),
	everyoneSID_(nullptr),
	allAppsSID_(nullptr),
	quitExistingLauncher_(false),
	debugClientPipe_{ nullptr } {
	// this can only be assigned once
	assert(singleton_ == nullptr);
	singleton_ = this;
}

PipeServer::~PipeServer() {
	closeDebugClient();

	if (everyoneSID_ != nullptr)
		FreeSid(everyoneSID_);
	if (allAppsSID_ != nullptr)
		FreeSid(allAppsSID_);
	if (securittyDescriptor_ != nullptr)
		LocalFree(securittyDescriptor_);
	if (acl_ != nullptr)
		LocalFree(acl_);
}

void PipeServer::initBackendServers(const std::wstring & topDirPath) {
	// load known backend implementations
	Json::Value backends;
	if (loadJsonFile(topDirPath + L"\\backends.json", backends)) {
		if (backends.isArray()) {
			for (auto it = backends.begin(); it != backends.end(); ++it) {
				auto& backendInfo = *it;
				BackendServer* backend = new BackendServer(this, backendInfo);
				backends_.push_back(backend);
			}
		}
	}

	// maps language profiles to backend names
	initInputMethods(topDirPath);
}

void PipeServer::initInputMethods(const std::wstring& topDirPath) {
	// maps language profiles to backend names
	for (BackendServer* backend : backends_) {
		std::wstring dirPath = topDirPath + L"\\" + utf8Codec.from_bytes(backend->name_) + L"\\input_methods";
		// scan the dir for lang profile definition files (ime.json)
		WIN32_FIND_DATA findData = { 0 };
		HANDLE hFind = ::FindFirstFile((dirPath + L"\\*").c_str(), &findData);
		if (hFind != INVALID_HANDLE_VALUE) {
			do {
				if (findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) { // this is a subdir
					if (findData.cFileName[0] != '.') {
						std::wstring imejson = dirPath;
						imejson += '\\';
						imejson += findData.cFileName;
						imejson += L"\\ime.json";
						// Make sure the file exists
						DWORD fileAttrib = GetFileAttributesW(imejson.c_str());
						if (fileAttrib != INVALID_FILE_ATTRIBUTES) {
							// load the json file to get the info of input method
							Json::Value json;
							if (loadJsonFile(imejson, json)) {
								std::string guid = json["guid"].asString();
								transform(guid.begin(), guid.end(), guid.begin(), tolower);  // convert GUID to lwoer case
																							 // map text service GUID to its backend server
								backendMap_.insert(std::make_pair(guid, backendFromName(backend->name_.c_str())));
							}
						}
					}
				}
			} while (::FindNextFile(hFind, &findData));
			::FindClose(hFind);
		}
	}
}

void PipeServer::finalizeBackendServers() {
	// try to terminate launched backend server processes
	for (BackendServer* backend : backends_) {
		backend->terminateProcess();
		delete backend;
	}
}

BackendServer* PipeServer::backendFromName(const char* name) {
	// for such a small list, linear search is often faster than hash table or map
	for (BackendServer* backend : backends_) {
		if (backend->name_ == name)
			return backend;
	}
	return nullptr;
}

void PipeServer::onBackendClosed(BackendServer * backend) {
	// the backend server is terminated, disconnect all clients using this backend
	auto removed_it = std::remove_if(clients_.begin(), clients_.end(),
		[backend](ClientInfo* client) {
		if (client->backend_ == backend) {
			// if the client is using this broken backend, disconnect it
			uv_close((uv_handle_t*)&client->pipe_, [](uv_handle_t* handle) {
				auto client = (ClientInfo*)handle->data;
				delete client;
			});
			return true;
		}
		return false;
	});
	clients_.erase(removed_it, clients_.cend());
}

BackendServer* PipeServer::backendFromLangProfileGuid(const char* guid) {
	auto it = backendMap_.find(guid);
	if (it != backendMap_.end())  // found the backend for the text service
		return it->second;
	return nullptr;
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
	finalizeBackendServers();
	ExitProcess(0); // quit PipeServer
}

void PipeServer::handleBackendReply(const char * readBuf, size_t len) {
	recentDebugMessages_.emplace_back(readBuf, len);
	// only keep recent 100 messages
	if (recentDebugMessages_.size() >= 100) {
		recentDebugMessages_.pop_front();
	}
	// print to debug console if there is any
	outputDebugMessage(readBuf, len);

	// pass the response back to the clients
	auto line = readBuf;
	auto buf_end = readBuf + len;
	while (line < buf_end) {
		// Format of each line:
		// PIMG_MSG|<client_id>|<json reply>\n
		if (auto line_end = strchr(line, '\n')) {
			// only handle lines prefixed with "PIME_MSG|" since other lines
			// might be debug messages printed by the backend.
			if (strncmp(line, "PIME_MSG|", 9) == 0) {
				line += 9; // Skip the prefix
				if (auto sep = strchr(line, '|')) {
					// split the client_id from the remaining json reply
					string clientId(line, sep - line);
					auto msg = sep + 1;
					auto msg_len = line_end - msg;
					// because Windows uses CRLF "\r\n" for new lines, python and node.js
					// try to convert "\n" to "\r\n" sometimes. Let's remove the additional '\r'
					if (msg_len > 0 && msg[msg_len - 1] == '\r') {
						--msg_len;
					}
					// send the reply message back to the client
					sendReplyToClient(clientId, msg, msg_len);
				}
			}
			line = line_end + 1;
		}
		else {
			break;
		}
	}
}

void PipeServer::sendReplyToClient(const std::string clientId, const char* msg, size_t len) {
	// find the client with this ID
	auto it = std::find_if(clients_.cbegin(), clients_.cend(), [clientId](const ClientInfo* client) {
		return client->clientId_ == clientId;
	});
	if (it != clients_.cend()) {
		auto client = *it;
		uv_buf_t buf = {len, (char*)msg};
		uv_write_t* req = new uv_write_t{};
		uv_write(req, client->stream(), &buf, 1, [](uv_write_t* req, int status) {
			delete req;
		});
	}
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
void PipeServer::initPipe(uv_pipe_t* pipe, const char* app_name, SECURITY_ATTRIBUTES* sa) {
	wchar_t username[UNLEN + 1];
	DWORD unlen = UNLEN + 1;
	if (GetUserNameW(username, &unlen)) {
		// add username to the pipe path so it will not clash with other users' pipes.
		char pipe_name[MAX_PATH];
		std::string utf8_username = utf8Codec.to_bytes(username, username + unlen);
		sprintf(pipe_name, "\\\\.\\pipe\\%s\\PIME\\%s", utf8_username.c_str(), app_name);
		// create the pipe
		uv_pipe_init_windows_named_pipe(uv_default_loop(), pipe, 0, PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE, sa);
		pipe->data = this;
		uv_pipe_bind(pipe, pipe_name);
	}
}


void PipeServer::onNewClientConnected(uv_stream_t* server, int status) {
	auto server_pipe = reinterpret_cast<uv_pipe_t*>(server);
	auto client = new ClientInfo{this};
	uv_pipe_init_windows_named_pipe(uv_default_loop(), &client->pipe_, 0, server_pipe->pipe_mode, server_pipe->security_attributes);
	client->pipe_.data = client;
	uv_stream_set_blocking((uv_stream_t*)&client->pipe_, 0);
	uv_accept(server, (uv_stream_t*)&client->pipe_);
	clients_.push_back(client);

	uv_read_start((uv_stream_t*)&client->pipe_,
		[](uv_handle_t* handle, size_t suggested_size, uv_buf_t* buf) {
			buf->base = new char[suggested_size];
			buf->len = suggested_size;
		},
		[](uv_stream_t* stream, ssize_t nread, const uv_buf_t* buf) {
			auto client = (ClientInfo*)stream->data;
			client->server_->onClientDataReceived(stream, nread, buf);
		}
	);
}

void PipeServer::onClientDataReceived(uv_stream_t* stream, ssize_t nread, const uv_buf_t* buf) {
	auto client = (ClientInfo*)stream->data;
	if (nread <= 0 || nread == UV_EOF || buf->base == nullptr) {
		if (buf->base) {
			delete []buf->base;
		}
		// the client connection seems to be broken. close it.
		closeClient(client);
		return;
	}
	if (buf->base) {
		handleClientMessage(client, buf->base, buf->len);
		delete[]buf->base;
	}
}

int PipeServer::exec(LPSTR cmd) {
	parseCommandLine(cmd);
	if (quitExistingLauncher_) { // terminate existing launcher process
		terminateExistingLauncher();
		return 0;
	}

	// get the PIME directory
	wchar_t exeFilePathBuf[MAX_PATH];
	DWORD len = GetModuleFileNameW(NULL, exeFilePathBuf, MAX_PATH);
	exeFilePathBuf[len] = '\0';

	// Ask Windows to restart our process when crashes happen.
	RegisterApplicationRestart(exeFilePathBuf, 0);

	// strip the filename part to get dir path
	wchar_t* p = wcsrchr(exeFilePathBuf, '\\');
	if (p)
		*p = '\0';
	topDirPath_ = exeFilePathBuf;

	// must set CWD to our dir. otherwise the backends won't launch.
	::SetCurrentDirectoryW(topDirPath_.c_str());

	// this is the first instance
	initBackendServers(topDirPath_);

	// preparing for the server pipe
	SECURITY_ATTRIBUTES* sa = nullptr;
	if (Ime::WindowsVersion().isWindows8Above()) {
		// Setting special security attributes to the named pipe is only needed 
		// for Windows >= 8 since older versions do not have app containers (metro apps) 
		// in which connecting to pipes are blocked by default permission settings.
		initSecurityAttributes();
		sa = &securityAttributes_;
	}
	// initialize the server pipe
	initPipe(&serverPipe_, "Launcher", sa);

	// listen to events from clients
	uv_listen(reinterpret_cast<uv_stream_t*>(&serverPipe_), 32, [](uv_stream_t* server, int status) {
		PipeServer* _this = (PipeServer*)server->data;
		_this->onNewClientConnected(server, status);
	});

	// initialize the debug pipe connected by debug console
	initPipe(&debugServerPipe_, "Debug", nullptr);

	// listen to events from the debug console
	uv_listen(reinterpret_cast<uv_stream_t*>(&debugServerPipe_), 1, [](uv_stream_t* server, int status) {
		PipeServer* _this = (PipeServer*)server->data;
		_this->onNewDebugClientConnected(server, status);
	});

	// run the main loop
	uv_run(uv_default_loop(), UV_RUN_DEFAULT);
	return 0;
}

void PipeServer::handleClientMessage(ClientInfo* client, const char* readBuf, size_t len) {
	// special handling, asked for quitting PIMELauncher.
	if (len >= 4 && strncmp("quit", readBuf, 4) == 0) {
		quit();
		return;
	}
	if (!client->isInitialized()) {
		Json::Value msg;
		Json::Reader reader;
		if (reader.parse(readBuf, msg)) {
			client->init(msg);
		}
	}
	// pass the incoming message to the backend
	auto backend = client->backend_;
	if (backend) {
		backend->handleClientMessage(client, readBuf, len);
	}
}

void PipeServer::closeClient(ClientInfo* client) {
	if (client->backend_ != nullptr) {
		// FIXME: client->backend_->removeClient(client->clientId_);
		// notify the backend server to remove the client
		const char msg[] = "{\"method\":\"close\"}";
		client->backend_->handleClientMessage(client, msg, strlen(msg));
	}

	clients_.erase(find(clients_.begin(), clients_.end(), client));
	uv_close((uv_handle_t*)&client->pipe_, [](uv_handle_t* handle) {
		auto client = (ClientInfo*)handle->data;
		delete client;
	});
}

void PipeServer::onNewDebugClientConnected(uv_stream_t* server, int status) {
	auto server_pipe = reinterpret_cast<uv_pipe_t*>(server);
	uv_pipe_t* client_pipe = new uv_pipe_t{};
	uv_pipe_init_windows_named_pipe(uv_default_loop(), client_pipe, 0, server_pipe->pipe_mode, server_pipe->security_attributes);
	client_pipe->data = this;
	uv_stream_set_blocking((uv_stream_t*)client_pipe, 0);
	uv_accept(server, (uv_stream_t*)client_pipe);

	// kill existing debug console client since we only allow one connection
	if (debugClientPipe_) {
		closeDebugClient();
	}
	debugClientPipe_ = client_pipe;

	// if there are recent debug messages, output them to the debug console
	for (auto& msg : recentDebugMessages_) {
		outputDebugMessage(msg.c_str(), msg.length());
	}
}

void PipeServer::closeDebugClient() {
	uv_close((uv_handle_t*)debugClientPipe_, [](uv_handle_t* handle) {
		delete (uv_pipe_t*)handle;
	});
	debugClientPipe_ = nullptr;
}

struct DebugMessageReq {
	uv_write_t req;
	string msg;
	PipeServer* pipeServer;
};

void PipeServer::outputDebugMessage(const char * msg, size_t len) {
	if (debugClientPipe_ != nullptr) {
		auto req_data = new DebugMessageReq{ {}, string{msg, len }, this};
		req_data->req.data = req_data;
		uv_buf_t buf = {req_data->msg.length(), (char*)req_data->msg.c_str()};

		uv_write(&req_data->req, reinterpret_cast<uv_stream_t*>(debugClientPipe_), &buf, 1, [](uv_write_t* req, int status) {
			DebugMessageReq* req_data = reinterpret_cast<DebugMessageReq*>(req->data);
			if (status < 0 || status == UV_EOF) {
				req_data->pipeServer->closeDebugClient();
			}
			delete req_data;
		});
	}
}

} // namespace PIME
