cmake_minimum_required(VERSION 3.16)
project(genshin_decoder)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_C_STANDARD 11)

add_library(genshin-aes SHARED src/aes.c)

add_executable(genshin-unpack src/main.cpp src/util.cpp)
if(APPLE)
  include_directories(/opt/homebrew/Cellar/lz4/1.9.3/include)
  target_link_directories(genshin-unpack PUBLIC /opt/homebrew/Cellar/lz4/1.9.3/lib)
endif()
target_link_libraries(genshin-unpack genshin-aes lz4 c)

add_executable(bc7_to_rgb bc7/main.cc bc7/bcn.cc)
