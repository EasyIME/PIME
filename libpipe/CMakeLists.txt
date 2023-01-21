cmake_minimum_required(VERSION 2.8.8)

project(libpipe)

# http://www.utf8everywhere.org/
add_definitions(/D_UNICODE=1 /DUNICODE=1)

include_directories(
    ${CMAKE_SOURCE_DIR}
)

add_library(libpipe SHARED
	libpipe.cpp
	libpipe.h
	libpipe.def
)
