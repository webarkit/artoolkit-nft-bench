/*
 *  scenarios.hpp
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
// Scenario sets for synthetic frame banks. Seeds, pose specs and RNG consumption order are those of the exploratory
// nft_eval harness, so a bank reproduces the frames that harness evaluated.
#include <string>
#include <vector>
#include "synth.hpp"

namespace nftbench {

struct BankFrame {
    int seq = 0, i = 0;
    double t = 0.0;              // seconds since the start of the sequence
    std::string group;           // "detect/<scenario>=<level>" or "track/speed=<v>"
    Pose gt;
    std::vector<uint8_t> grey;   // cam.w * cam.h, 8-bit
};

struct ScenarioDef { std::string name; std::vector<double> values; };
std::vector<ScenarioDef> allScenarios();

// legacyStdHash=true seeds groups with std::hash<std::string>, as nft_eval did. That hash differs between standard
// libraries, so it is only for reproducing nft_eval's frames on the same compiler; the default is a stable FNV-1a hash.
std::vector<BankFrame> buildDetectionFrames(const Marker &m, const Camera &c, uint64_t seed, int trials,
                                            const std::vector<std::string> &scenarioNames, bool legacyStdHash = false);
std::vector<BankFrame> buildTrackingFrames(const Marker &m, const Camera &c, uint64_t seed, int sequences, int seqlen,
                                           const std::vector<double> &speeds, double fps = 30.0);

}  // namespace nftbench
