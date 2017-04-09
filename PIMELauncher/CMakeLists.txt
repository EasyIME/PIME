project(PIMELauncher)

# generate the resource file containing version info
configure_file("version.rc.in" "version.rc" @ONLY)

set(LIBUV_INCLUDE_DIRS
    ${CMAKE_SOURCE_DIR}/libuv/include
    ${CMAKE_SOURCE_DIR}/libuv/src
)

include_directories(
    ${CMAKE_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_BINARY_DIR}
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
    PIMELauncher.rc
)

target_link_libraries(PIMELauncher 
    jsoncpp_lib_static
    Rpcrt4 # for uuid stuff
    libuv
)

add_executable(PIMEDebugConsole
    PIMEDebugConsole.cpp
)

target_link_libraries(PIMEDebugConsole
    jsoncpp_lib_static
    libuv
)
