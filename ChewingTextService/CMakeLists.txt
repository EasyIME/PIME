cmake_minimum_required(VERSION 2.8.8)

project(ChewingTextService)

if(NOT DEFINED PROJECT_LIBCHEWING)
    message(FATAL_ERROR "PROJECT_LIBCHEWING must be provided")
endif()

# http://www.utf8everywhere.org/
add_definitions(/D_UNICODE=1 /DUNICODE=1)

include_directories(
    ${PROJECT_LIBCHEWING}/include
    ${CMAKE_SOURCE_DIR}
)

add_library(ChewingService SHARED
    ${PROJECT_SOURCE_DIR}/ChewingImeModule.cpp
    ${PROJECT_SOURCE_DIR}/ChewingImeModule.h
    ${PROJECT_SOURCE_DIR}/ChewingTextService.cpp
    ${PROJECT_SOURCE_DIR}/ChewingTextService.def
    ${PROJECT_SOURCE_DIR}/ChewingTextService.h
    ${PROJECT_SOURCE_DIR}/DllEntry.cpp
    ${PROJECT_SOURCE_DIR}/mainicon.ico
)
target_link_libraries(ChewingService chewing_static libime_static)
