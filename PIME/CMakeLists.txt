cmake_minimum_required(VERSION 2.8.8)

project(PIMETextService)

# http://www.utf8everywhere.org/
add_definitions(/D_UNICODE=1 /DUNICODE=1)

include_directories(
    ${CMAKE_SOURCE_DIR}
    ${CMAKE_SOURCE_DIR}/jsoncpp/include
)

add_library(PIMETextService SHARED
    # core IME implementation
    PIMEImeModule.cpp
    PIMEImeModule.h
    PIMETextService.cpp
    PIMETextService.def
    PIMETextService.h
    PIMEClient.cpp
    PIMEClient.h
    PIMELangBarButton.cpp
    PIMELangBarButton.h
    DllEntry.cpp
    # resources
    PIMETextService.rc
)

target_link_libraries(PIMETextService
    libIME_static
    jsoncpp_lib_static
)
