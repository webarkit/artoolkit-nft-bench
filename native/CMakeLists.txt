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

foreach(t test_synth test_bank_io)
    add_executable(${t} tests/${t}.cpp)
    target_link_libraries(${t} PRIVATE nftbench_synth)
    target_compile_definitions(${t} PRIVATE NFTBENCH_SOURCE_DIR="${PROJECT_SOURCE_DIR}")
    add_test(NAME ${t} COMMAND ${t})
endforeach()
add_custom_target(nftbench_tests DEPENDS test_synth test_bank_io)
set_target_properties(nftbench_synth nft_export test_synth test_bank_io PROPERTIES FOLDER "native")
