cmake_minimum_required(VERSION 2.8.11)

# override default c/c++ flags, add /MT to link VC++ runtime statically.
set(CMAKE_USER_MAKE_RULES_OVERRIDE	${CMAKE_CURRENT_SOURCE_DIR}/cmake/c_flag_overrides.cmake)
set(CMAKE_USER_MAKE_RULES_OVERRIDE_CXX	${CMAKE_CURRENT_SOURCE_DIR}/cmake/cxx_flag_overrides.cmake)

project(PIME)

# http://www.utf8everywhere.org/
add_definitions(
	/D_UNICODE=1 /DUNICODE=1 # do Unicode build
	/D_CRT_SECURE_NO_WARNINGS # disable warnings about old libc functions
	/GR- # turn off C++ RTTI
)

add_subdirectory(${PROJECT_SOURCE_DIR}/libIME)
add_subdirectory(${PROJECT_SOURCE_DIR}/jsoncpp)
add_subdirectory(${PROJECT_SOURCE_DIR}/PIME)

# only build the following components for 32-bit x86 platform
if("${CMAKE_SIZEOF_VOID_P}" EQUAL "4")
    add_subdirectory(${PROJECT_SOURCE_DIR}/PIMELauncher)
    add_subdirectory(${PROJECT_SOURCE_DIR}/libpipe)
endif("${CMAKE_SIZEOF_VOID_P}" EQUAL "4")
