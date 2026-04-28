if(NOT DEFINED CMAKE_TOOLCHAIN_FILE)
  if(DEFINED ENV{VCPKG_ROOT})
    set(CMAKE_TOOLCHAIN_FILE
        "$ENV{VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake"
        CACHE STRING "Vcpkg toolchain file")
  else()
    set(CMAKE_TOOLCHAIN_FILE
        "${CMAKE_CURRENT_SOURCE_DIR}/vcpkg/scripts/buildsystems/vcpkg.cmake"
        CACHE STRING "Vcpkg toolchain file")
  endif()
endif()
if(CMAKE_TOOLCHAIN_FILE STREQUAL
   "${CMAKE_CURRENT_SOURCE_DIR}/vcpkg/scripts/buildsystems/vcpkg.cmake")
  find_package(Git QUIET)
  if(GIT_FOUND)
    execute_process(
      COMMAND "${GIT_EXECUTABLE}" submodule status vcpkg
      WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
      RESULT_VARIABLE TMP_SUBMODULE_RESULT
      OUTPUT_QUIET ERROR_QUIET OUTPUT_STRIP_TRAILING_WHITESPACE)
    if(NOT TMP_SUBMODULE_RESULT)
      execute_process(COMMAND "${GIT_EXECUTABLE}" submodule update --init vcpkg
                      WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}")
    elseif(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/vcpkg/.git")
      execute_process(COMMAND "${GIT_EXECUTABLE}" pull --ff-only
                      WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/vcpkg")
    else()
      execute_process(
        COMMAND "${GIT_EXECUTABLE}" clone https://github.com/microsoft/vcpkg.git
        WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}")
    endif()
  endif()
  if(NOT EXISTS "${CMAKE_TOOLCHAIN_FILE}")
    message(
      FATAL_ERROR
        "Failed to initialize vcpkg: ${CMAKE_TOOLCHAIN_FILE} not found")
  endif()
endif()
