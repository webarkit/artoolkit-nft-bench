/*
 *  bank_io.hpp
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
// Frame bank on disk: frames/NNNNNN.png (8-bit grey) + bank.json (schema in python/nftbench/schema.py).
#include <string>
#include <vector>
#include "scenarios.hpp"
#include "synth.hpp"

namespace nftbench {

struct BankEntry {
    int seq = 0, i = 0;
    double t = 0.0;
    std::string group, file;
    bool hasPose = false, hasCorners = false;
    Pose gt{};
    double corners[8] = {0};   // TL, TR, BR, BL of the marker image, frame pixels
};

struct BankData {
    std::string dir, kind, name, markerImage, markerDataset;
    int width = 0, height = 0;
    double markerDpi = 0, markerWmm = 0, markerHmm = 0;
    Camera camera{};
    std::vector<BankEntry> frames;
};

void writeBank(const std::string &dir, const Marker &m, const std::string &markerImage, const std::string &markerDataset,
               const Camera &c, const std::vector<BankFrame> &frames, const std::string &name);
BankData readBank(const std::string &dir);
std::vector<uint8_t> loadGrey(const BankData &b, size_t index);   // throws std::runtime_error on size mismatch

}  // namespace nftbench
