cmake_minimum_required(VERSION 3.15)

# Policy CMP0091 enables CMAKE_MSVC_RUNTIME_LIBRARY
cmake_policy(SET CMP0091 NEW)

# Statically link MSVC CRT (/MT in Release, /MTd in Debug) across all targets
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

project(PIME)

# load current number from file
file(READ "version.txt" PIME_VERSION)
# we use semantic versioning: <major>.<minor>.<patch>[-<some suffix>]
# convert the version string into a list (separated by ;)
string(REGEX MATCHALL "[0-9]+" PIME_VERSION_PARTS "${PIME_VERSION}")
list(GET PIME_VERSION_PARTS 0 PIME_VERSION_MAJOR)
list(GET PIME_VERSION_PARTS 1 PIME_VERSION_MINOR)
list(GET PIME_VERSION_PARTS 2 PIME_VERSION_PATCH)

# http://www.utf8everywhere.org/
add_definitions(
	/D_UNICODE=1 /DUNICODE=1 # do Unicode build
	/D_CRT_SECURE_NO_WARNINGS # disable warnings about old libc functions
	/GR- # turn off C++ RTTI
    -DWIN32_LEAN_AND_MEAN
    -D_WIN32_WINNT=0x0600
)

add_subdirectory(${PROJECT_SOURCE_DIR}/libIME2)

add_subdirectory(${PROJECT_SOURCE_DIR}/PIMETextService)

# only build the following components for 32-bit x86 platform
if("${CMAKE_SIZEOF_VOID_P}" EQUAL "4")
    include(FetchContent)

    FetchContent_Declare(
        Corrosion
        GIT_REPOSITORY https://github.com/corrosion-rs/corrosion.git
        GIT_TAG v0.6 # Optionally specify a commit hash, version tag or branch here
    )
    FetchContent_MakeAvailable(Corrosion)

    add_subdirectory(${PROJECT_SOURCE_DIR}/PIMELauncher)
endif("${CMAKE_SIZEOF_VOID_P}" EQUAL "4")

include(CTest)

if(BUILD_TESTING)
    add_executable(PIMETextServiceCursorTest tests/composition_cursor_test.cpp)
    target_include_directories(PIMETextServiceCursorTest PRIVATE ${PROJECT_SOURCE_DIR}/PIMETextService)
    target_compile_features(PIMETextServiceCursorTest PRIVATE cxx_std_14)
    add_test(NAME PIMETextServiceCursorTest COMMAND PIMETextServiceCursorTest)
endif()
