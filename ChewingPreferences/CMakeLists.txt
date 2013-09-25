cmake_minimum_required(VERSION 2.8.8)

project(ChewingPreferences)

# http://www.utf8everywhere.org/
add_definitions(/D_UNICODE=1 /DUNICODE=1)

include_directories(
    ${CMAKE_SOURCE_DIR}
)

add_executable(ChewingPreferences WIN32
    # Entry point
    ${PROJECT_SOURCE_DIR}/ChewingPreferences.cpp
    # Configurations
    ${CMAKE_SOURCE_DIR}/ChewingTextService/ChewingConfig.cpp
    ${CMAKE_SOURCE_DIR}/ChewingTextService/ChewingConfig.h
    # libIME UI code
    ${CMAKE_SOURCE_DIR}/libIME/Utils.cpp
    ${CMAKE_SOURCE_DIR}/libIME/Utils.h
    ${CMAKE_SOURCE_DIR}/libIME/Window.cpp
    ${CMAKE_SOURCE_DIR}/libIME/Window.h
    ${CMAKE_SOURCE_DIR}/libIME/Dialog.cpp
    ${CMAKE_SOURCE_DIR}/libIME/Dialog.h
    ${CMAKE_SOURCE_DIR}/libIME/PropertyDialog.cpp
    ${CMAKE_SOURCE_DIR}/libIME/PropertyDialog.h
    ${CMAKE_SOURCE_DIR}/libIME/PropertyPage.cpp
    ${CMAKE_SOURCE_DIR}/libIME/PropertyPage.h
    # Configuration dialog
    ${PROJECT_SOURCE_DIR}/TypingPropertyPage.cpp
    ${PROJECT_SOURCE_DIR}/TypingPropertyPage.h
    ${PROJECT_SOURCE_DIR}/UiPropertyPage.cpp
    ${PROJECT_SOURCE_DIR}/UiPropertyPage.h
    ${PROJECT_SOURCE_DIR}/KeyboardPropertyPage.cpp
    ${PROJECT_SOURCE_DIR}/KeyboardPropertyPage.h
    ${PROJECT_SOURCE_DIR}/SymbolsPropertyPage.cpp
    ${PROJECT_SOURCE_DIR}/SymbolsPropertyPage.h
    # About dialog
    ${PROJECT_SOURCE_DIR}/AboutDialog.cpp
    ${PROJECT_SOURCE_DIR}/AboutDialog.h
    # resources
    ${PROJECT_SOURCE_DIR}/ChewingPreferences.rc
	${PROJECT_SOURCE_DIR}/ChewingPreferences.exe.manifest
    ${CMAKE_SOURCE_DIR}/ChewingTextService/mainicon.ico
    ${CMAKE_SOURCE_DIR}/ChewingTextService/logo.bmp
)
target_link_libraries(ChewingPreferences
	comctl32.lib
)
