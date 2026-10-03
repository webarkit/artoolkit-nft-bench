#
#  CMakeLists.txt
#  artoolkit-nft-bench
#
#  This file is part of artoolkit-nft-bench.
#
#  SPDX-License-Identifier: LGPL-3.0-or-later
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  Copyright 2026 WebARKit.
#
#  Author(s): Walter Perdan @kalwalt https://github.com/kalwalt
#

cmake_minimum_required(VERSION 3.20)
project(artoolkit5_nft LANGUAGES C CXX)

# Out-of-tree CMake build of the NFT-relevant subset of ARToolKit5 (webarkit fork).
# The upstream sources live in the extern/artoolkit5 submodule and are never modified.
# GL / GLUT / video / OSG / examples are intentionally NOT built: this is for headless
# detection (KPM) and tracking (AR2) quality testing.

set(CMAKE_C_STANDARD 99)
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
if(MSVC)
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL")
endif()
set_property(GLOBAL PROPERTY USE_FOLDERS ON)

set(ARTK5_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/extern/artoolkit5" CACHE PATH "ARToolKit5 sources")
if(NOT EXISTS "${ARTK5_ROOT}/include/AR/ar.h")
    message(FATAL_ERROR "ARToolKit5 sources not found in ${ARTK5_ROOT}. Run: git submodule update --init")
endif()

option(ARX_FETCH_DEPS "Download and build zlib + libjpeg-turbo instead of using system packages" ON)
option(ARX_BUILD_TESTS "Build the NFT quality-test harness" ON)

include(cmake/ThirdParty.cmake)
include(cmake/ARToolKitSources.cmake)

# config.h is generated into the build tree (upstream Configure scripts would write into the source tree).
# Headless build: select the "dummy" video input as default (config.h.in otherwise #errors out).
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${ARTK5_ROOT}/include/AR/config.h.in")
file(READ "${ARTK5_ROOT}/include/AR/config.h.in" _config_h)
string(REGEX REPLACE "#undef[ 	]+ARVIDEO_INPUT_DEFAULT_DUMMY" "#define ARVIDEO_INPUT_DEFAULT_DUMMY" _config_h "${_config_h}")
file(WRITE "${CMAKE_BINARY_DIR}/generated/AR/config.h" "${_config_h}")

# Public include dirs. Deliberately NOT include/win64-x64 etc.: those hold stale bundled jpeg/zlib/pthread headers.
set(ARTK5_INCLUDE_DIRS "${CMAKE_BINARY_DIR}/generated" "${ARTK5_ROOT}/include")

function(artk5_library name)
    add_library(${name} STATIC ${ARGN})
    target_include_directories(${name} PUBLIC ${ARTK5_INCLUDE_DIRS})
    if(WIN32)
        # thread_sub.c falls back to native Win32 critical sections / condition variables / _beginthread,
        # so no pthreads-win32 is needed (the bundled pthreadVC2 is for old MSVC only).
        target_compile_definitions(${name} PRIVATE ARUTIL_DISABLE_PTHREADS)
    endif()
    if(MSVC)
        target_compile_definitions(${name} PRIVATE _CRT_SECURE_NO_DEPRECATE _CRT_NONSTDC_NO_DEPRECATE _USE_MATH_DEFINES)
        target_compile_options(${name} PRIVATE /W3 /wd4244 /wd4267 /wd4305 /wd4996)
    elseif(UNIX)
        target_link_libraries(${name} PUBLIC m)
        # ioapi.c uses fopen64/ftello64/fseeko64, which are hidden with a strict -std on glibc;
        # without this they are implicitly declared and 64-bit pointers get truncated.
        target_compile_definitions(${name} PRIVATE _LARGEFILE64_SOURCE _FILE_OFFSET_BITS=64)
    endif()
    set_target_properties(${name} PROPERTIES FOLDER "artoolkit5")
endfunction()

artk5_library(ARUtil ${ARTK5_ARUTIL_SOURCES})
target_link_libraries(ARUtil PUBLIC ZLIB::ZLIB)
if(NOT WIN32)
    find_package(Threads REQUIRED)
    target_link_libraries(ARUtil PUBLIC Threads::Threads)
endif()

artk5_library(AR ${ARTK5_AR_SOURCES})
target_link_libraries(AR PUBLIC ARUtil)

artk5_library(ARICP ${ARTK5_ARICP_SOURCES})
target_link_libraries(ARICP PUBLIC AR)

artk5_library(AR2 ${ARTK5_AR2_SOURCES})
target_link_libraries(AR2 PUBLIC AR ARUtil JPEG::JPEG)

artk5_library(KPM ${ARTK5_KPM_SOURCES})
target_include_directories(KPM PRIVATE "${ARTK5_ROOT}/lib/SRC/KPM/FreakMatcher")
if(NOT MSVC)
    # Upstream FreakMatcher headers use std::numeric_limits without including <limits>.
    target_compile_options(KPM PRIVATE "$<$<COMPILE_LANGUAGE:CXX>:SHELL:-include limits>" "$<$<COMPILE_LANGUAGE:CXX>:SHELL:-include cstdint>")
endif()
target_link_libraries(KPM PUBLIC AR ARUtil AR2)

# NFT dataset generator (upstream tool, built unmodified from the submodule).
add_executable(genTexData "${ARTK5_ROOT}/util/genTexData/genTexData.c")
target_link_libraries(genTexData PRIVATE AR2 KPM ARICP AR ARUtil JPEG::JPEG)
if(MSVC)
    target_compile_definitions(genTexData PRIVATE _CRT_SECURE_NO_DEPRECATE)
endif()
set_target_properties(genTexData PROPERTIES FOLDER "tools")

if(ARX_BUILD_TESTS AND EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/tests/CMakeLists.txt")
    enable_testing()
    add_subdirectory(tests)
endif()
