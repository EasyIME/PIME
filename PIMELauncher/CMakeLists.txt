project(PIMELauncher)

# http://www.utf8everywhere.org/
add_definitions(/D_UNICODE=1 /DUNICODE=1)

include_directories(
    ${CMAKE_SOURCE_DIR}
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
    # PIMELauncher.rc
)

target_link_libraries(PIMELauncher 
    libpipe
    jsoncpp_lib_static
    Wininet
)
