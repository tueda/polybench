cmake_minimum_required(VERSION 3.15)
include(cmake/init-vcpkg.cmake)
project(
  polybench-flint
  VERSION 0.1.0
  LANGUAGES C)

get_filename_component(COMPILER_NAME ${CMAKE_C_COMPILER} NAME_WE)
set(COMPILER_VERSION
    "${COMPILER_NAME} (${CMAKE_C_COMPILER_ID}) ${CMAKE_C_COMPILER_VERSION}")
configure_file(${CMAKE_SOURCE_DIR}/version.h.in ${CMAKE_BINARY_DIR}/version.h
               @ONLY)

find_package(PkgConfig REQUIRED)
pkg_check_modules(flint REQUIRED IMPORTED_TARGET flint)

find_library(MATH_LIBRARY m)
add_library(Math::Math INTERFACE IMPORTED)
target_link_libraries(Math::Math INTERFACE ${MATH_LIBRARY})

add_executable(polybench-flint main.c)
target_include_directories(polybench-flint PRIVATE ${CMAKE_BINARY_DIR})
target_link_libraries(polybench-flint PRIVATE PkgConfig::flint Math::Math)
