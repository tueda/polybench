cmake_minimum_required(VERSION 3.29)
include(cmake/init-vcpkg.cmake)
project(
  polybench-flint
  VERSION 0.1.0
  LANGUAGES C)
add_executable(polybench-flint main.c)
