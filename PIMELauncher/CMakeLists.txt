project(PIMELauncher)

# generate the resource file containing version info
configure_file("PIMELauncher.rc.in" "PIMELauncher.rc" @ONLY)

set(LIBUV_INCLUDE_DIRS
    ${CMAKE_SOURCE_DIR}/libuv/include
    ${CMAKE_SOURCE_DIR}/libuv/src
)

include_directories(
    ${CMAKE_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${LIBUV_INCLUDE_DIRS}
)

add_executable(PIMELauncher WIN32
    PIMELauncher.cpp
    PipeServer.cpp
    PipeServer.h
    BackendServer.cpp
    BackendServer.h
    Utils.cpp
    Utils.h
    # resources
    ${CMAKE_CURRENT_BINARY_DIR}/PIMELauncher.rc
)

target_link_libraries(PIMELauncher 
    jsoncpp_lib_static
    Wininet  # for http connections
    Crypt32  # for base64 encode
    libuv
)
