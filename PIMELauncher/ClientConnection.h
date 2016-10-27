#ifndef _CLIENT_CONNECTION_H_
#define _CLIENT_CONNECTION_H_

#include <windows.h>
#include <cstddef> // for offsetof
#include <string>

class PIMELauncher;
class BackendServer;

class ClientConnection
{
public:
	ClientConnection(HANDLE pipe, PIMELauncher* server);
	~ClientConnection();
	void close();

	void asyncReadClient();

private:
	void asyncReadBackend();

	void onAsyncReadClientFinished(DWORD err, DWORD numBytes);
	static void CALLBACK _onAsyncReadClientFinished(DWORD err, DWORD numBytes, OVERLAPPED* overlapped) {
		// get the this pointer
		char* objAddr = reinterpret_cast<char*>(overlapped) - offsetof(ClientConnection, readClientOverlapped_);
		ClientConnection* _this = reinterpret_cast<ClientConnection*>(objAddr);
		_this->onAsyncReadClientFinished(err, numBytes);
	}

	void onAsyncWriteClientFinished(DWORD err, DWORD numBytes);
	static void CALLBACK _onAsyncWriteClientFinished(DWORD err, DWORD numBytes, OVERLAPPED* overlapped) {
		// get the this pointer
		char* objAddr = reinterpret_cast<char*>(overlapped) - offsetof(ClientConnection, writeClientOverlapped_);
		ClientConnection* _this = reinterpret_cast<ClientConnection*>(objAddr);
		_this->onAsyncWriteClientFinished(err, numBytes);
	}

	void onAsyncReadBackendFinished(DWORD err, DWORD numBytes);
	static void CALLBACK _onAsyncReadBackendFinished(DWORD err, DWORD numBytes, OVERLAPPED* overlapped) {
		// get the this pointer
		char* objAddr = reinterpret_cast<char*>(overlapped) - offsetof(ClientConnection, readBackendOverlapped_);
		ClientConnection* _this = reinterpret_cast<ClientConnection*>(objAddr);
		_this->onAsyncReadBackendFinished(err, numBytes);
	}

	void onAsyncWriteBackendFinished(DWORD err, DWORD numBytes);
	static void CALLBACK _onAsyncWriteBackendFinished(DWORD err, DWORD numBytes, OVERLAPPED* overlapped) {
		// get the this pointer
		char* objAddr = reinterpret_cast<char*>(overlapped) - offsetof(ClientConnection, writeBackendOverlapped_);
		ClientConnection* _this = reinterpret_cast<ClientConnection*>(objAddr);
		_this->onAsyncWriteBackendFinished(err, numBytes);
	}

	void handleClientRequest();
	void handleBackendReply();

private:
	PIMELauncher* server_;
	HANDLE pipe_;
	BackendServer* backendServer_;

	std::string currentMsg_;
	OVERLAPPED readClientOverlapped_;
	char readClientBuf_[1024];

	std::string currentReply_;
	OVERLAPPED readBackendOverlapped_;
	char readBackendBuf_[1024];

	OVERLAPPED writeClientOverlapped_;
	OVERLAPPED writeBackendOverlapped_;
};

#endif // _CLIENT_CONNECTION_H_
