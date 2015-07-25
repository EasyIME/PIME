cmake_minimum_required(VERSION 2.8.8)

project(NodeTextService)

# http://www.utf8everywhere.org/
add_definitions(/D_UNICODE=1 /DUNICODE=1)

include_directories(
    ${CMAKE_SOURCE_DIR}
    ${CMAKE_SOURCE_DIR}/rapidjson/include
)

add_library(NodeTextService SHARED
    # core IME implementation
    NodeImeModule.cpp
    NodeImeModule.h
    NodeTextService.cpp
    NodeTextService.def
    NodeTextService.h
    NodeClient.cpp
    NodeClient.h
    DllEntry.cpp
    # resources
    NodeTextService.rc
)

target_link_libraries(NodeTextService
    libIME_static
)
