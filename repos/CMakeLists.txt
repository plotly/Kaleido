cmake_minimum_required(VERSION 3.16)
project(chromium)

set(CMAKE_CXX_STANDARD 14)

include_directories(${CMAKE_CURRENT_SOURCE_DIR}/src)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/src/out/Kaleido_linux_x64/gen)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/kaleido/cc)

add_executable(kaleido kaleido/cc/kaleido.cc kaleido/cc/kaleido.h kaleido/cc/scopes/Plotly.h kaleido/cc/scopes/Base.h)
