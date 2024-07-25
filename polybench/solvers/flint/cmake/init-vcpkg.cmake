if(NOT DEFINED CMAKE_TOOLCHAIN_FILE)
  if(DEFINED ENV{VCPKG_ROOT})
    set(CMAKE_TOOLCHAIN_FILE
        "$ENV{VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake"
        CACHE STRING "Vcpkg toolchain file")
  else()
    set(CMAKE_TOOLCHAIN_FILE
        "${CMAKE_CURRENT_SOURCE_DIR}/vcpkg/scripts/buildsystems/vcpkg.cmake"
        CACHE STRING "Vcpkg toolchain file")
    if(NOT EXISTS
       "${CMAKE_CURRENT_SOURCE_DIR}/vcpkg/scripts/buildsystems/vcpkg.cmake")
      find_package(Git QUIET)
      if(GIT_FOUND)
        execute_process(
          COMMAND ${GIT_EXECUTABLE} submodule status vcpkg
          WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
          RESULT_VARIABLE TMP_SUBMODULE_RESULT
          OUTPUT_QUIET ERROR_QUIET OUTPUT_STRIP_TRAILING_WHITESPACE)
        if(NOT TMP_SUBMODULE_RESULT)
          execute_process(
            COMMAND ${GIT_EXECUTABLE} submodule update --init vcpkg
            WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})
        elseif(NOT EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/vcpkg)
          execute_process(
            COMMAND ${GIT_EXECUTABLE} clone
                    https://github.com/microsoft/vcpkg.git
            WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})
        endif()
      endif()
    endif()
  endif()
endif()
