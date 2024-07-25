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
pkg_check_modules(gmp REQUIRED IMPORTED_TARGET gmp)
pkg_check_modules(mpfr REQUIRED IMPORTED_TARGET mpfr)

find_path(FLINT_INCLUDE_DIR flint/flint.h)
find_library(FLINT_LIBRARY flint)

add_executable(polybench-flint main.c)

target_include_directories(polybench-flint PRIVATE ${FLINT_INCLUDE_DIR}
                                                   ${CMAKE_BINARY_DIR})
target_link_libraries(polybench-flint PRIVATE m PkgConfig::gmp PkgConfig::mpfr
                                              ${FLINT_LIBRARY})
