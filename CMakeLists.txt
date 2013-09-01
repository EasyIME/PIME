cmake_minimum_required(VERSION 2.8.8)
project(windows-TSF-chewing)

enable_testing()

set(PROJECT_LIBCHEWING ${PROJECT_SOURCE_DIR}/external/libchewing)
add_subdirectory(${PROJECT_LIBCHEWING})

add_subdirectory(chewingwrapper)
