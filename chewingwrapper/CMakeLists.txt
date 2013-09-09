cmake_minimum_required(VERSION 2.8.8)
project(chewingwrapper)

if(NOT DEFINED PROJECT_LIBCHEWING OR NOT DEFINED CHEWING_DATA_PREFIX)
	message(FATAL_ERROR "PROJECT_LIBCHEWING and CHEWING_DATA_PREFIX must be provided")
endif()

# /wd4819
# Without BOM, Visual Studio does not treat source file as UTF-8 encoding, thus
# it will complain about invalid character. Use /wd4819 can suppress this
# warning.
set(CMAKE_C_FLAGS "/wd4819 ${CMAKE_C_FLAGS}")

include_directories(
	${PROJECT_SOURCE_DIR}/include
	${PROJECT_LIBCHEWING}/include
)

add_library(chewingwrapper_static STATIC
	${PROJECT_SOURCE_DIR}/include/chewingwrapper.hpp
	${PROJECT_SOURCE_DIR}/src/chewingwrapper.cpp
)
target_link_libraries(chewingwrapper_static chewing_static)

enable_testing()
set(CHEWINGWRAPPER_TEST
	test-chewingwrapper
)

set(CHEWINGWRAPPER_TEST_BIN ${PROJECT_BINARY_DIR}/test)

foreach(target ${CHEWINGWRAPPER_TEST})
	add_executable(${target}
		${PROJECT_SOURCE_DIR}/test/${target}.cpp
	)
	target_link_libraries(${target} chewingwrapper_static)
	set_target_properties(${target} PROPERTIES
		RUNTIME_OUTPUT_DIRECTORY ${CHEWINGWRAPPER_TEST_BIN}
		RUNTIME_OUTPUT_DIRECTORY_DEBUG ${CHEWINGWRAPPER_TEST_BIN}
		RUNTIME_OUTPUT_DIRECTORY_RELEASE ${CHEWINGWRAPPER_TEST_BIN}
		COMPILE_DEFINITIONS
			"CHEWING_PATH=\"${CHEWING_DATA_PREFIX}\";CHEWING_USER_PATH=\"${CHEWINGWRAPPER_TEST_BIN}\""
	)

	add_test(${target} ${CHEWINGWRAPPER_TEST_BIN}/${target})
endforeach()
