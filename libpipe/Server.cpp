#include "Server.h"

#include <istream>

#include <boost/asio/read_until.hpp>

namespace pime {

namespace asio = ::boost::asio;

namespace {

HANDLE createPipeHandle(wchar_t* pipeName) {
    // PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE  ??
    auto pipeHandle = ::CreateNamedPipeW(pipeName,
        PIPE_ACCESS_DUPLEX | FILE_FLAG_OVERLAPPED,
        /*PIPE_TYPE_BYTE*/ (PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE) | PIPE_WAIT | PIPE_REJECT_REMOTE_CLIENTS,
        PIPE_UNLIMITED_INSTANCES, 65535, 65535, 1000, nullptr);
    return pipeHandle;
}

}  // namespace

Server::Server(): workGuard_(ioContext_.get_executor()), nextPipe_(ioContext_) {
}

asio::windows::stream_handle Server::createPipe() {
    HANDLE pipeHandle = createPipeHandle(L"");
    // TODO: Implement pipe creation.
    // boost asio doesn't take ownership and it doesn't close the handle in dtor.
    // we have to close it manually.
    return asio::windows::stream_handle( ioContext_, pipeHandle );
}

void Server::closeClient(ClientData* client) {
    client->stream.close();
    // event_callback_("closed");
}

void Server::handleRequest(ClientData* client_data, std::string& line) {
    // event_callback_("request", line);
}

void Server::waitForNextClient() {
    nextPipe_ = createPipe();
    asio::windows::overlapped_ptr overlapped{
        ioContext_,
        [this](boost::system::error_code ec, size_t size) {
            auto client_data = std::make_unique<ClientData>(std::move(nextPipe_));
            // event_callback_("connected");

            readClient(client_data.get());

            clients_.push_back(std::move(client_data));

            ioContext_.post([this]() {
                waitForNextClient();
            });
        }
    };
    if (!::ConnectNamedPipe(nextPipe_.native_handle(), overlapped.get())) {
        int error = GetLastError();
        if (error == ERROR_PIPE_CONNECTED) {
            // TODO: handle this case.
        }
        if (error == ERROR_IO_PENDING) {
            // Normal condition since this is async I/O.
            overlapped.release();
        }
        else {
            boost::system::error_code ec{ error, asio::error::get_system_category() };
            overlapped.complete(ec, 0);
        }
    }
}

void Server::readClient(ClientData* client_data) {
    // one clinet per buffer.
    // Reference:https://www.boost.org/doc/libs/1_43_0/doc/html/boost_asio/reference/async_read_until/overload1.html
    asio::async_read_until(client_data->stream, client_data->buffer, '\n',
        [client_data, this](boost::system::error_code ec, std::size_t size) {
            if (!ec) {
                std::istream is(&client_data->buffer);
                std::string line;
                std::getline(is, line);

                handleRequest(client_data, line);

                // read the next request.
                readClient(client_data);
            }
            else if (ec.value() != ERROR_MORE_DATA) {
                closeClient(client_data);
                return;
            }
        }
    );
}

void Server::writeClient(ClientData& client_data, const char* data, size_t len) {
    char* dup = new char[len];
    std::memcpy(dup, data, len);
    asio::async_write(client_data.stream, asio::buffer(dup, len),
        [this, dup](boost::system::error_code ec, std::size_t size) {
            delete[]dup;
        });
}

void Server::run() {
    // keeps the executor running forever.
    waitForNextClient();
    ioContext_.run();
}

}  // namespace pime
