# A subset of boost libraries 1.72.0 extracted using bcp.
# Command line:
# bcp.exe --boost="C:\Program Files\boost\boost_1_72_0" --scan "<dir path>\PIME\PIMEServer\PIMEServer.h" "<dir path>\PIME\boost-1.72.0"

project(boost_subset)
set(PROJECT_NAME, boost_subset)

include_directories(${PROJECT_SOURCE_DIR})

file(GLOB_RECURSE LIBSRCS
    libs/*/src/*.c
    libs/*/src/*.cpp
    libs/*/src/*.cc
    libs/*/src/*.h
    libs/*/src/*.hpp)

# add_library(${PROJECT_NAME} STATIC ${LIBSRCS})
add_library(${PROJECT_NAME} ${LIBSRCS})
