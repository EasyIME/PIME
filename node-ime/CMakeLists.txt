cmake_minimum_required(VERSION 2.8.8)

project(NodeTextService)

# http://www.utf8everywhere.org/
add_definitions(/D_UNICODE=1 /DUNICODE=1)

include_directories(
    ${CMAKE_SOURCE_DIR}
    ${CMAKE_SOURCE_DIR}/casablanca/Release/include
)

add_library(NodeTextService SHARED
    # core IME implementation
    NodeImeModule.cpp
    NodeImeModule.h
    NodeTextService.cpp
    NodeTextService.def
    NodeTextService.h
    DllEntry.cpp
    # resources
    NodeTextService.rc
)

if(CMAKE_CL_64)
    set(REST_CPP_LIBRARY_DIR ${CMAKE_SOURCE_DIR}/casablanca/Binaries/x64/Release)
else()
    set(REST_CPP_LIBRARY_DIR ${CMAKE_SOURCE_DIR}/casablanca/Binaries/Win32/Release)
endif()

# FIXME: Why this is useless?
#link_directories(${REST_CPP_LIBRARY_DIR})

target_link_libraries(NodeTextService
    libIME_static
    ${REST_CPP_LIBRARY_DIR}/cpprest110_2_2.lib
)
