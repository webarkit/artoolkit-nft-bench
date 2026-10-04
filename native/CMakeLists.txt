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

# Native side of the bench: synthetic frame library, bank I/O, exporter, runner and their unit tests.

add_library(nftbench_synth STATIC src/synth.cpp src/scenarios.cpp src/bank_io.cpp)
target_include_directories(nftbench_synth PUBLIC src)
target_link_libraries(nftbench_synth PUBLIC AR2 AR ARUtil JPEG::JPEG nlohmann_json::nlohmann_json stb_headers)
target_compile_features(nftbench_synth PUBLIC cxx_std_17)
if(MSVC)
    target_compile_definitions(nftbench_synth PUBLIC _CRT_SECURE_NO_WARNINGS _USE_MATH_DEFINES NOMINMAX)
endif()

add_executable(nft_export src/nft_export.cpp)
target_link_libraries(nft_export PRIVATE nftbench_synth)

add_library(nftbench_engine STATIC src/engine.cpp)
target_link_libraries(nftbench_engine PUBLIC nftbench_synth KPM AR2 ARICP AR ARUtil)

foreach(t test_synth test_bank_io test_engine)
    add_executable(${t} tests/${t}.cpp)
    target_link_libraries(${t} PRIVATE nftbench_engine)
    target_compile_definitions(${t} PRIVATE NFTBENCH_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
    add_test(NAME ${t} COMMAND ${t})
endforeach()
add_custom_target(nftbench_tests DEPENDS test_synth test_bank_io test_engine)
set_target_properties(nftbench_synth nft_export test_synth test_bank_io PROPERTIES FOLDER "native")

# The native runner. The artoolkit5 commit and the build flags go into every result header.
execute_process(COMMAND git -C "${ARTK5_ROOT}" rev-parse --short HEAD OUTPUT_VARIABLE ARTK5_COMMIT
                OUTPUT_STRIP_TRAILING_WHITESPACE ERROR_QUIET)
add_executable(nft_run src/nft_run.cpp)
target_link_libraries(nft_run PRIVATE nftbench_engine)
target_compile_definitions(nft_run PRIVATE
    NFTBENCH_ARTK5_COMMIT="${ARTK5_COMMIT}"
    NFTBENCH_BUILD_FLAGS="${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION} $<CONFIG> ${CMAKE_CXX_FLAGS_RELEASE}")
set_target_properties(nft_run nftbench_engine PROPERTIES FOLDER "native")
