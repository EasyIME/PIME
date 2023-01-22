#include <string>
#include <vector>
#include <memory>

#include <boost/asio/read.hpp>
#include <boost/asio/write.hpp>
#include <boost/asio/error.hpp>
#include <boost/asio/execution_context.hpp>
#include <boost/system/error_code.hpp>

#include <boost/asio/io_context.hpp>
#include <boost/asio/executor_work_guard.hpp>
#include <boost/asio/windows/stream_handle.hpp>

#include <boost/asio/streambuf.hpp>
#include <boost/asio/windows/overlapped_ptr.hpp>

namespace pime {

typedef int (*EventHandler)(int event, int client_id, const char* payload);

struct ClientData {
    explicit ClientData(boost::asio::windows::stream_handle&& pipe) : stream(std::move(pipe)) {}
    boost::asio::windows::stream_handle stream;
    boost::asio::streambuf buffer;
};

class Server {

public:
    Server();

    boost::asio::windows::stream_handle createPipe();

    void closeClient(ClientData* client);

    void handleRequest(ClientData* client_data, std::string& line);

    void readClient(ClientData* client_data);

    void writeClient(ClientData& client_data, const char* data, size_t len);

    void waitForNextClient();

    void run();

private:
    std::vector<std::unique_ptr<ClientData>> clients_;
    EventHandler event_handler_;

    boost::asio::io_context ioContext_;
    // keeps the executor running forever.
    boost::asio::executor_work_guard<boost::asio::io_context::executor_type> workGuard_;
    boost::asio::windows::stream_handle nextPipe_;
};
}  // namespace pime
