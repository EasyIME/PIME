#include <iostream>
#include <sstream>
#include <uv.h>
#include <Windows.h>
#include <Lmcons.h> // for UNLEN

using namespace std;

class DebugConsole {
public:
	DebugConsole() :
		pipe_{ nullptr },
		isConnected_{ false } {
	}

	int exec();

private:
	void connectPipe();
	void onConnected(int status);
	void onDataReceived(uv_stream_t* stream, ssize_t nread, const uv_buf_t* buf);

private:
	uv_pipe_t* pipe_;
	bool isConnected_;
};

void DebugConsole::connectPipe() {
	pipe_ = new uv_pipe_t{};
	uv_pipe_init(uv_default_loop(), pipe_, 0);
	pipe_->data = this;

	char pipe_name[MAX_PATH];
	char username[UNLEN + 1];
	DWORD unlen = UNLEN + 1;
	if (GetUserNameA(username, &unlen)) {
		// add username to the pipe path so it will not clash with other users' pipes.
		sprintf(pipe_name, "\\\\.\\pipe\\%s\\PIME\\%s", username, "Debug");
	}

	uv_connect_t* req = new uv_connect_t{};
	req->data = this;
	uv_pipe_connect(req, pipe_, pipe_name, [](uv_connect_t* req, int status) {
		auto _this = reinterpret_cast<DebugConsole*>(req->data);
		_this->onConnected(status);
		delete req;
	});

}

void DebugConsole::onConnected(int status) {
	if (status == 0) {
		cout << "Debug console connected\n";
		isConnected_ = true;
		auto stream = reinterpret_cast<uv_stream_t*>(pipe_);
		uv_read_start(stream,
			[](uv_handle_t *, size_t suggested_size, uv_buf_t * buf) {
				buf->base = new char[suggested_size];
				buf->len = suggested_size;
			},
			[](uv_stream_t* stream, ssize_t nread, const uv_buf_t* buf) {
				reinterpret_cast<DebugConsole*>(stream->data)->onDataReceived(stream, nread, buf);
			}
		);
	}
	else {
		cout << "Fail to connect to the debug console\n";
		delete pipe_;
		pipe_ = nullptr;
	}
}

void DebugConsole::onDataReceived(uv_stream_t * stream, ssize_t nread, const uv_buf_t * buf) {
	if (nread < 0 || nread == UV_EOF) {
		cerr << "Error\n";
		if (buf->base) {
			delete[]buf->base;
		}
		return;
	}
	// handle the message
	if (buf->base) {
		stringstream lines(string(buf->base, nread));
		string line;
		while (getline(lines, line)) {
			if (line.compare(0, 6, "INPUT:") == 0) {
				SetConsoleTextAttribute(GetStdHandle(STD_OUTPUT_HANDLE), FOREGROUND_INTENSITY | FOREGROUND_BLUE | FOREGROUND_GREEN);
			}
			else if (line.compare(0, 7, "OUTPUT:") == 0) {
				SetConsoleTextAttribute(GetStdHandle(STD_OUTPUT_HANDLE), FOREGROUND_INTENSITY | FOREGROUND_GREEN);
			}
			cout << line << endl;
		}
		delete[]buf->base;
	}
	// reset color
	SetConsoleTextAttribute(GetStdHandle(STD_OUTPUT_HANDLE), FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE);
}

int DebugConsole::exec() {
	// connect to PIMELauncher
	connectPipe();
	uv_run(uv_default_loop(), UV_RUN_DEFAULT);
	return 0;
}

int main(int argc, char** argv) {
	SetConsoleTitle(L"PIME Debug Console");
	SetConsoleOutputCP(CP_UTF8); // set the console encoding to UTF-8
	COORD size = {80, 1024};
	SetConsoleScreenBufferSize(GetStdHandle(STD_OUTPUT_HANDLE), size);
	DebugConsole console;
	return console.exec();
}
