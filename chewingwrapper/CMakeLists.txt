cmake_minimum_required(VERSION 2.8.8)
project(chewingwrapper)

if(NOT DEFINED PROJECT_LIBCHEWING)
    message(FATAL_ERROR "PROJECT_LIBCHEWING must be provided")
endif()

include_directories(
    ${PROJECT_SOURCE_DIR}/include
    ${PROJECT_LIBCHEWING}/include
)

add_library(chewingwrapper_static STATIC
    ${PROJECT_SOURCE_DIR}/include/chewingwrapper.hpp
    ${PROJECT_SOURCE_DIR}/src/chewingwrapper.cpp
)
target_link_libraries(chewingwrapper_static chewing_static)
