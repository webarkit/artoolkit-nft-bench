/*
 *  rng.hpp
 *  artoolkit-nft-bench
 *
 *  This file is part of artoolkit-nft-bench.
 *
 *  SPDX-License-Identifier: LGPL-3.0-or-later
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU Lesser General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU Lesser General Public License for more details.
 *
 *  You should have received a copy of the GNU Lesser General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 *  Copyright 2026 WebARKit.
 *
 *  Author(s): Walter Perdan @kalwalt https://github.com/kalwalt
 *
 */

#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>

namespace nftbench {

const double kPi = 3.14159265358979323846;
inline double deg2rad(double d) { return d * kPi / 180.0; }

// xorshift64*: identical sequence on every platform.
struct Rng {
    uint64_t s;
    explicit Rng(uint64_t seed) : s(seed * 0x9E3779B97F4A7C15ull + 0x1234567ull) { for (int i = 0; i < 4; i++) next(); }
    uint64_t next() { s ^= s >> 12; s ^= s << 25; s ^= s >> 27; return s * 0x2545F4914F6CDD1Dull; }
    double u01() { return (double)(next() >> 11) / 9007199254740992.0; }
    double uni(double a, double b) { return a + (b - a) * u01(); }
    double gauss() { double u1 = std::max(u01(), 1e-12), u2 = u01(); return std::sqrt(-2.0 * std::log(u1)) * std::cos(2.0 * kPi * u2); }
};

}  // namespace nftbench
