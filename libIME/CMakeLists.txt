cmake_minimum_required(VERSION 2.8.8)

project(libIME)

# http://www.utf8everywhere.org/
add_definitions(
	/D_UNICODE=1
	/DUNICODE=1
)

add_library(libIME_static STATIC
	# Core TSF part
    ${PROJECT_SOURCE_DIR}/EditSession.cpp
    ${PROJECT_SOURCE_DIR}/EditSession.h
    ${PROJECT_SOURCE_DIR}/ImeModule.cpp
    ${PROJECT_SOURCE_DIR}/ImeModule.h
    ${PROJECT_SOURCE_DIR}/libIME.cpp
    ${PROJECT_SOURCE_DIR}/libIME.h
    ${PROJECT_SOURCE_DIR}/TextService.cpp
    ${PROJECT_SOURCE_DIR}/TextService.h
    ${PROJECT_SOURCE_DIR}/Utils.cpp
    ${PROJECT_SOURCE_DIR}/Utils.h
	# UI-related code
	${PROJECT_SOURCE_DIR}/DrawUtils.h
	${PROJECT_SOURCE_DIR}/DrawUtils.cpp
	${PROJECT_SOURCE_DIR}/Window.cpp
	${PROJECT_SOURCE_DIR}/Window.h
	${PROJECT_SOURCE_DIR}/ImeWindow.cpp
	${PROJECT_SOURCE_DIR}/ImeWindow.h
	${PROJECT_SOURCE_DIR}/CandidateWindow.h
	${PROJECT_SOURCE_DIR}/CandidateWindow.cpp
)
