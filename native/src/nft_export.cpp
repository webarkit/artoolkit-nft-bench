/*
 *  nft_export.cpp
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

// nft_export: write a synthetic frame bank (grey PNG frames + bank.json with the true pose of every frame).
//
//   nft_export out=<dir> image=<marker.jpg> dpi=<f> dataset=<marker dataset name>
//              [width=640 height=480 fovy=45 seed=1 trials=10 scenarios=a,b seqs=3 seqlen=90 speeds=0,2,5 fps=30
//               mode=detect|track|all legacy_hash=0]
#include <cstdio>
#include <cstdlib>
#include <map>
#include <string>
#include <vector>

#include <AR/ar.h>

#include "bank_io.hpp"
#include "scenarios.hpp"

using namespace nftbench;

static std::vector<std::string> splitList(const std::string &s) {
    std::vector<std::string> out; size_t p = 0;
    while (p < s.size()) { size_t e = s.find(',', p); if (e == std::string::npos) e = s.size(); out.push_back(s.substr(p, e - p)); p = e + 1; }
    return out;
}

int main(int argc, char **argv) {
    std::map<std::string, std::string> a;
    for (int i = 1; i < argc; i++) { std::string s = argv[i]; size_t e = s.find('='); if (e != std::string::npos) a[s.substr(0, e)] = s.substr(e + 1); }
    auto get = [&](const char *k, const char *def) { auto it = a.find(k); return it == a.end() ? std::string(def) : it->second; };
    if (!a.count("out") || !a.count("image") || !a.count("dpi") || !a.count("dataset")) {
        std::fprintf(stderr, "usage: nft_export out=<dir> image=<marker.jpg> dpi=<f> dataset=<name> [options, see source]\n");
        return 2;
    }
    arLogLevel = AR_LOG_LEVEL_ERROR;
    Marker m;
    if (!loadMarker(a["image"], std::atof(a["dpi"].c_str()), m)) return 1;
    Camera c = makeCamera(std::atoi(get("width", "640").c_str()), std::atoi(get("height", "480").c_str()), std::atof(get("fovy", "45").c_str()));
    const uint64_t seed = (uint64_t)std::atoll(get("seed", "1").c_str());
    const std::string mode = get("mode", "all");
    std::vector<BankFrame> frames;
    if (mode == "detect" || mode == "all")
        frames = buildDetectionFrames(m, c, seed, std::atoi(get("trials", "10").c_str()), splitList(get("scenarios", "")),
                                      get("legacy_hash", "0") == "1");
    if (mode == "track" || mode == "all") {
        std::vector<double> speeds;
        for (auto &s : splitList(get("speeds", "0,2,5,10,20,35"))) speeds.push_back(std::atof(s.c_str()));
        auto tr = buildTrackingFrames(m, c, seed, std::atoi(get("seqs", "3").c_str()), std::atoi(get("seqlen", "90").c_str()),
                                      speeds, std::atof(get("fps", "30").c_str()));
        frames.insert(frames.end(), std::make_move_iterator(tr.begin()), std::make_move_iterator(tr.end()));
    }
    std::string image = a["image"];
    size_t slash = image.find_last_of("/\\");
    writeBank(a["out"], m, slash == std::string::npos ? image : image.substr(slash + 1), a["dataset"], c, frames, get("name", "synthetic"));
    std::printf("wrote %zu frames to %s\n", frames.size(), a["out"].c_str());
    return 0;
}
