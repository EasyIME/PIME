cmake_minimum_required(VERSION 2.8.8)

project(windows-chewing-tsf)

# http://www.utf8everywhere.org/
add_definitions(/D_UNICODE=1 /DUNICODE=1)

enable_testing()

set(PROJECT_LIBCHEWING ${PROJECT_SOURCE_DIR}/external/libchewing)
add_subdirectory(${PROJECT_LIBCHEWING})

add_subdirectory(${PROJECT_SOURCE_DIR}/libIME)

add_subdirectory(${PROJECT_SOURCE_DIR}/ChewingTextService)
