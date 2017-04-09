project(PIMELauncher)

# http://www.utf8everywhere.org/
add_definitions(/D_UNICODE=1 /DUNICODE=1)

# generate the resource file containing version info
configure_file("version.rc.in" "version.rc" @ONLY)

include_directories(
    ${CMAKE_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_BINARY_DIR}
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
    Wininet  # for http connections
    Crypt32  # for base64 encode
)
