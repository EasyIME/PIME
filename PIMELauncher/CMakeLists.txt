project(PIMELauncher)

# generate the resource file containing version info
configure_file("version.rc.in" "version.rc" @ONLY)

set(LIBUV_INCLUDE_DIRS
    ${CMAKE_SOURCE_DIR}/libuv/include
    ${CMAKE_SOURCE_DIR}/libuv/src
)

set(SPDLOG_INCLUDE_DIRS
    ${CMAKE_SOURCE_DIR}/spdlog-1.2.1/include
)
add_definitions(
    # Enable using wchar_t & wstring for filenames
    -DSPDLOG_WCHAR_FILENAMES=1
    # Prevent the fd of log files from being inherited by child processes
    # This is required. Otherwise the file rotation will fail since the file is kept open by the child process.
    -DSPDLOG_PREVENT_CHILD_FD=1
)

include_directories(
    ${CMAKE_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_BINARY_DIR}
    ${LIBUV_INCLUDE_DIRS}
    ${SPDLOG_INCLUDE_DIRS}
)

add_executable(PIMELauncher WIN32
    PIMELauncher.cpp
    PipeServer.cpp
    PipeServer.h
    PipeClient.cpp
    PipeClient.h
    BackendServer.cpp
    BackendServer.h
    Utils.cpp
    Utils.h
    # resources
    PIMELauncher.rc
)

target_link_libraries(PIMELauncher 
    jsoncpp_lib_static
    Rpcrt4 # for uuid stuff
    libuv
)
