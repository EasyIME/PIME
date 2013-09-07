cmake_minimum_required(VERSION 2.8.8)
project(windows-TSF-chewing)

enable_testing()

set(PROJECT_LIBCHEWING ${PROJECT_SOURCE_DIR}/libchewing)
set(CHEWING_DATA_PREFIX ${PROJECT_BINARY_DIR}/libchewing/data)
add_subdirectory(${PROJECT_LIBCHEWING})

add_subdirectory(chewingwrapper)
