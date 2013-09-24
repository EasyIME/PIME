cmake_minimum_required(VERSION 2.8.11)

# override default c/c++ flags, add /MT to link VC++ runtime statically.
set(CMAKE_USER_MAKE_RULES_OVERRIDE	${CMAKE_CURRENT_SOURCE_DIR}/cmake/c_flag_overrides.cmake)
set(CMAKE_USER_MAKE_RULES_OVERRIDE_CXX	${CMAKE_CURRENT_SOURCE_DIR}/cmake/cxx_flag_overrides.cmake)

project(windows-chewing-tsf)

# http://www.utf8everywhere.org/
add_definitions(
	/D_UNICODE=1 /DUNICODE=1 # do Unicode build
	/D_CRT_SECURE_NO_WARNINGS # disable warnings about old libc functions
	/GR- # turn off C++ RTTI
)

enable_testing()

set(PROJECT_LIBCHEWING ${PROJECT_SOURCE_DIR}/libchewing)
set(CHEWING_DATA_PREFIX ${PROJECT_BINARY_DIR}/libchewing/data)

add_subdirectory(${PROJECT_LIBCHEWING})

add_subdirectory(${PROJECT_SOURCE_DIR}/libIME)

add_subdirectory(chewingwrapper)

add_subdirectory(${PROJECT_SOURCE_DIR}/ChewingTextService)

add_subdirectory(${PROJECT_SOURCE_DIR}/ChewingPreferences)
