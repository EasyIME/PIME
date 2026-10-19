cmake_minimum_required(VERSION 3.0)

project(PIMETextService)

# http://www.utf8everywhere.org/
add_definitions(/D_UNICODE=1 /DUNICODE=1)
set(CMAKE_CXX_STANDARD 17)

# generate the resource file containing version info
configure_file("PIMETextService.rc.in" "PIMETextService.rc" @ONLY)

include_directories(
    ${CMAKE_SOURCE_DIR}
    ${CMAKE_SOURCE_DIR}/json/single_include
    ${CMAKE_CURRENT_SOURCE_DIR}
)

add_library(PIMETextService SHARED
    # core IME implementation
    PIMEImeModule.cpp
    PIMEImeModule.h
    IconCache.h
    IconCache.cpp
    PIMETextService.cpp
    PIMETextService.def
    PIMETextService.h
    PIMEClient.cpp
    PIMEClient.h
    PIMELangBarButton.cpp
    PIMELangBarButton.h
    DllEntry.cpp
    # resources
    ${CMAKE_CURRENT_BINARY_DIR}/PIMETextService.rc
)

target_link_libraries(PIMETextService
    libIME2_static
)

if(CMAKE_CXX_COMPILER_ARCHITECTURE_ID MATCHES "ARM64")
    # Directly build the native ARM64 implementation as PIMETextService_arm64.dll
    set_target_properties(PIMETextService PROPERTIES OUTPUT_NAME "PIMETextService_arm64")

    # Link the ARM64X forwarder DLL directly as PIMETextService.dll
    add_custom_command(
        TARGET PIMETextService POST_BUILD
        COMMAND "${CMAKE_LINKER}" /nologo /dll /noentry /nodefaultlib /machine:arm64x
                /defArm64Native:${CMAKE_CURRENT_SOURCE_DIR}/PIMETextService_arm64x_arm64.def
                /def:${CMAKE_CURRENT_SOURCE_DIR}/PIMETextService_arm64x_x64.def
                /out:$<TARGET_FILE_DIR:PIMETextService>/PIMETextService.dll
        COMMENT "Linking ARM64X forwarder DLL"
    )
endif()

