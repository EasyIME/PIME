cmake_minimum_required(VERSION 2.8.8)
project(windows-TSF-chewing)

add_subdirectory(external/libchewing)

include_directories(
    chewingwrapper/include
    external/libchewing/include
)

add_library(chewingwrapper STATIC
    chewingwrapper/include/chewingwrapper.hpp
    chewingwrapper/src/chewingwrapper.cpp
)
target_link_libraries(chewingwrapper chewing_static)
