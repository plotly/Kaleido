cmake_minimum_required(VERSION 3.16)
project(chromium)

set(CMAKE_CXX_STANDARD 14)

include_directories(${CMAKE_CURRENT_SOURCE_DIR}/src)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/src/out/Headless/gen)

add_executable(headless_example src/headless/app/headless_example.cc)
add_executable(headless_shell src/headless/app/headless_shell.cc)
add_executable(orca_next orca_next/orca_next.cc)
