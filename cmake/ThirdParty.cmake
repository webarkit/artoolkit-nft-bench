#
#  ThirdParty.cmake
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

# zlib + libjpeg-turbo providing the imported targets ZLIB::ZLIB and JPEG::JPEG.
if(ARX_FETCH_DEPS)
    include(FetchContent)
    set(FETCHCONTENT_QUIET OFF)

    FetchContent_Declare(zlib
        GIT_REPOSITORY https://github.com/madler/zlib.git
        GIT_TAG        v1.3.1
        GIT_SHALLOW    TRUE)
    set(ZLIB_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(zlib)
    if(TARGET zlibstatic AND NOT TARGET ZLIB::ZLIB)
        target_include_directories(zlibstatic PUBLIC "${zlib_SOURCE_DIR}" "${zlib_BINARY_DIR}")
        add_library(ZLIB::ZLIB ALIAS zlibstatic)
    endif()

    # libjpeg-turbo refuses add_subdirectory(): download its source only (SOURCE_SUBDIR points nowhere),
    # then build + install it at configure time with a nested cmake, once per configuration.
    FetchContent_Declare(libjpeg-turbo
        GIT_REPOSITORY https://github.com/libjpeg-turbo/libjpeg-turbo.git
        GIT_TAG        3.0.4
        GIT_SHALLOW    TRUE
        SOURCE_SUBDIR  _no_cmake_here)
    FetchContent_MakeAvailable(libjpeg-turbo)

    get_property(_multi GLOBAL PROPERTY GENERATOR_IS_MULTI_CONFIG)
    if(_multi)
        set(_jpeg_configs Debug Release)
    else()
        set(_jpeg_configs ${CMAKE_BUILD_TYPE})
        if(NOT _jpeg_configs)
            set(_jpeg_configs Release)
        endif()
    endif()

    add_library(JPEG::JPEG STATIC IMPORTED GLOBAL)
    foreach(_cfg IN LISTS _jpeg_configs)
        set(_bdir   "${CMAKE_BINARY_DIR}/_deps/libjpeg-turbo-build-${_cfg}")
        set(_prefix "${CMAKE_BINARY_DIR}/_deps/libjpeg-turbo-install-${_cfg}")
        if(MSVC)
            set(_lib "${_prefix}/lib/jpeg-static.lib")
        else()
            set(_lib "${_prefix}/lib/libjpeg.a")
            if(NOT EXISTS "${_lib}")
                set(_lib "${_prefix}/lib64/libjpeg.a")
            endif()
        endif()
        if(NOT EXISTS "${_lib}" AND NOT EXISTS "${_prefix}/lib64/libjpeg.a")
            message(STATUS "Building libjpeg-turbo (${_cfg}) ...")
            set(_extra "")
            if(MSVC)
                list(APPEND _extra -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded$<$<CONFIG:Debug>:Debug>DLL)
            endif()
            execute_process(COMMAND ${CMAKE_COMMAND}
                    -S "${libjpeg-turbo_SOURCE_DIR}" -B "${_bdir}"
                    -G "${CMAKE_GENERATOR}" -A "${CMAKE_GENERATOR_PLATFORM}"
                    -DCMAKE_BUILD_TYPE=${_cfg} -DCMAKE_INSTALL_PREFIX=${_prefix}
                    -DENABLE_SHARED=OFF -DENABLE_STATIC=ON -DWITH_SIMD=OFF
                    -DWITH_TURBOJPEG=OFF -DWITH_JAVA=OFF -DWITH_TOOLS=OFF -DWITH_TESTS=OFF
                    -DCMAKE_POSITION_INDEPENDENT_CODE=ON ${_extra}
                RESULT_VARIABLE _r)
            if(_r)
                message(FATAL_ERROR "libjpeg-turbo configure failed (${_cfg})")
            endif()
            execute_process(COMMAND ${CMAKE_COMMAND} --build "${_bdir}" --config ${_cfg} --target install
                RESULT_VARIABLE _r)
            if(_r)
                message(FATAL_ERROR "libjpeg-turbo build failed (${_cfg})")
            endif()
            if(NOT MSVC AND NOT EXISTS "${_lib}")
                set(_lib "${_prefix}/lib64/libjpeg.a")
            endif()
        endif()
        string(TOUPPER ${_cfg} _CFG)
        set_property(TARGET JPEG::JPEG APPEND PROPERTY IMPORTED_CONFIGURATIONS ${_CFG})
        set_target_properties(JPEG::JPEG PROPERTIES IMPORTED_LOCATION_${_CFG} "${_lib}")
        set(_jpeg_inc "${_prefix}/include")
    endforeach()
    # Map unlisted configs (RelWithDebInfo / MinSizeRel) to Release.
    set_target_properties(JPEG::JPEG PROPERTIES
        INTERFACE_INCLUDE_DIRECTORIES "${_jpeg_inc}"
        MAP_IMPORTED_CONFIG_RELWITHDEBINFO Release
        MAP_IMPORTED_CONFIG_MINSIZEREL Release)
else()
    find_package(ZLIB REQUIRED)
    find_package(JPEG REQUIRED)
endif()

# nlohmann/json (MIT) and stb_image / stb_image_write (public domain / MIT), used by the native bench tools.
include(FetchContent)
FetchContent_Declare(nlohmann_json
    URL https://github.com/nlohmann/json/releases/download/v3.11.3/json.tar.xz)
set(JSON_BuildTests OFF CACHE INTERNAL "")
FetchContent_MakeAvailable(nlohmann_json)

FetchContent_Declare(stb
    GIT_REPOSITORY https://github.com/nothings/stb.git
    GIT_TAG        2c980bb59875b0d32144a71867fbdebb2f77cd20)
FetchContent_GetProperties(stb)
if(NOT stb_POPULATED)
    FetchContent_Populate(stb)
endif()
add_library(stb_headers INTERFACE)
target_include_directories(stb_headers SYSTEM INTERFACE "${stb_SOURCE_DIR}")
