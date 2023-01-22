#include <boost/asio/read.hpp>
#include <boost/asio/write.hpp>
#include <boost/asio/error.hpp>
#include <boost/asio/execution_context.hpp>
#include <boost/system/error_code.hpp>
#include <boost/date_time/posix_time/posix_time.hpp>

#include <boost/asio/io_context.hpp>
#include <boost/asio/executor_work_guard.hpp>
#include <boost/asio/windows/stream_handle.hpp>

#include <boost/asio/windows/overlapped_ptr.hpp>

typedef int (*EventHandler)(int event, int client_id, const char* payload);

struct ClientData {
    boost::asio::windows::stream_handle stream;
    boost::asio::streambuf buffer;
};

HANDLE createPipe() {
        // PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE  ??
    auto pipeHandle = ::CreateNamedPipeW(pipeName.c_str(),
        PIPE_ACCESS_DUPLEX | FILE_FLAG_OVERLAPPED,
        /*PIPE_TYPE_BYTE*/ (PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE) | PIPE_WAIT | PIPE_REJECT_REMOTE_CLIENTS,
        PIPE_UNLIMITED_INSTANCES, 65535, 65535, 1000, nullptr);
    return pipeHandle;
}

class Server {

public:

    boost::asio::windows::stream_handle create() {
        pipeHandle = INVALID_HANDLE_VALUE;
        // TODO: Implement pipe creation.
        // boost asio doesn't take ownership and it doesn't close the handle in dtor.
        // we have to close it manually.
        return boost::asio::windows::stream_handle{ server->ioContext(), pipeHandle };
    }

    void closPipe() {
        pipeStream_.close();
        event_callback_("closed");
    }

    void handleRequest(ClientData* client_data, std::string& line) {
        event_callback_("request", line);
    }

    void readClient(ClientData* client_data) {
        // one clinet per buffer.
        boost::asio::streambuf buffer;
        // Reference:https://www.boost.org/doc/libs/1_43_0/doc/html/boost_asio/reference/async_read_until/overload1.html
        pipeStream_.async_read_until(buffer, '\n',
            [client_data, this](boost::system::error_code ec, std::size_t size) {
                if (!ec) {
                    std::istream is(&b);
                    std::string line;
                    std::getline(is, line);

                    handleRequest(line);

                    // read the next request.
                    readClient(client_data);
                }
                else if (ec.value() != ERROR_MORE_DATA) {
                    closePipe();
                    return;
                }
            }
        );
    }

    void write(pipeStream, data) {
        writeBuf_.assign(data, len);
        boost::asio::async_write(pipeStream_, boost::asio::buffer(writeBuf_),
            [this](boost::system::error_code ec, std::size_t size) {
                writeBuf_.clear();
                startRead();  // Start reading the next request from client.
            });
    }

    void listen() {
        pipeStream_ = createPipe();
        boost::asio::windows::overlapped_ptr overlapped{
            ioContext_,
            [&pipeStream_, this](boost::system::error_code ec, size_t size) mutable {
                auto client_data = std::make_unique<ClientData>();
                client_data.stream = pipeStream_;
                event_callback_("connected");

                readClient(client_data);
                listen();
            }
        };
        if (!::ConnectNamedPipe(nextClient_->pipeHandle(), overlapped.get())) {
            int error = GetLastError();
            if (error == ERROR_IO_PENDING) {
                // Normal condition since this is async I/O.
                overlapped.release();
            }
            else {
                boost::system::error_code ec{ error, boost::asio::error::get_system_category() };
                overlapped.complete(ec, 0);
            }
        }
    }

    void run() {
        boost::asio::io_context ioContext_;
        // keeps the executor running forever.
        boost::asio::executor_work_guard<boost::asio::io_context::executor_type> workGuard_(ioContext_.get_executor());

        listen();

        ioContext_.run();
    }

private:
    std::vector<std::unique_ptr<ClientData>> clients_;
    EventHandler event_handler_;

    boost::asio::io_context ioContext_;
    // keeps the executor running forever.
    boost::asio::executor_work_guard<boost::asio::io_context::executor_type> workGuard_;
};

extern "C" {

std::unique_ptr<Server> g_server;

void run_pime_server(const char* pipe_path, EventHandler event_handler) {
    g_server = std::make_unique<Server>();
    g_server->run();
}

int write_reply(int pipe_id, const char* buffer, int size) {
    return g_server->write(pipe_id, buffer, size);
}

}
