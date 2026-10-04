/*
 *  scenarios.cpp
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

#include "scenarios.hpp"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <functional>

namespace nftbench {

static PoseSpec nominalSpec(Rng &rng) {
    PoseSpec s; s.distFactor = rng.uni(1.2, 1.8); s.tiltDeg = rng.uni(0, 20); s.tiltAzimuthDeg = rng.uni(0, 360);
    s.rollDeg = rng.uni(-30, 30); s.dxFrac = rng.uni(-0.12, 0.12); s.dyFrac = rng.uni(-0.12, 0.12);
    return s;
}

static void applyScenario(const std::string &name, double v, PoseSpec &s, Degrade &d) {
    if (name == "scale") s.distFactor = v;
    else if (name == "tilt") s.tiltDeg = v;
    else if (name == "roll") s.rollDeg = v;
    else if (name == "blur") d.blurSigma = v;
    else if (name == "noise") d.noiseSigma = v;
    else if (name == "light") { d.gain = v; d.offset = (v < 1.0 ? -10.0 * (1.0 - v) / 0.3 : 0.0); d.ramp = (v < 1.0 ? 0.3 : 0.0); }
    else if (name == "occlusion") d.occlusion = v;
}

std::vector<ScenarioDef> allScenarios() {
    return {
        {"scale", {1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0}},
        {"tilt", {0, 15, 30, 45, 55, 65, 72, 78}},
        {"roll", {0, 45, 90, 135, 180}},
        {"blur", {0, 1, 2, 3, 4}},
        {"noise", {0, 5, 10, 20, 30}},
        {"light", {1.0, 0.7, 0.4, 0.25}},
        {"occlusion", {0, 0.2, 0.4, 0.6}},
    };
}

static uint64_t fnv1a(const std::string &s) {
    uint64_t h = 1469598103934665603ull;
    for (unsigned char ch : s) { h ^= ch; h *= 1099511628211ull; }
    return h;
}

static std::string fmtLevel(double v) { char b[32]; std::snprintf(b, sizeof(b), "%g", v); return b; }

std::vector<BankFrame> buildDetectionFrames(const Marker &m, const Camera &c, uint64_t seed, int trials,
                                            const std::vector<std::string> &names, bool legacyStdHash) {
    std::vector<BankFrame> out;
    int seq = 0;
    for (auto &sc : allScenarios()) {
        if (!names.empty() && std::find(names.begin(), names.end(), sc.name) == names.end()) continue;
        const uint64_t h = legacyStdHash ? (uint64_t)std::hash<std::string>()(sc.name) : fnv1a(sc.name);
        for (double lv : sc.values) for (int t = 0; t < trials; t++) {
            Rng rng(seed * 1000003ull + (h % 9973) * 7919ull + (uint64_t)(lv * 1000) * 31ull + t);
            PoseSpec ps = nominalSpec(rng); Degrade d; applyScenario(sc.name, lv, ps, d);
            BankFrame f;
            f.seq = seq++; f.i = 0; f.t = 0.0; f.group = "detect/" + sc.name + "=" + fmtLevel(lv);
            f.gt = makePose(ps, m, c);
            std::vector<float> bg = makeBackground(c, rng, d.bgContrast);
            renderFrame(m, c, {f.gt}, bg, d, rng, f.grey);
            out.push_back(std::move(f));
        }
    }
    return out;
}

std::vector<BankFrame> buildTrackingFrames(const Marker &m, const Camera &c, uint64_t seed, int sequences, int seqlen,
                                           const std::vector<double> &speeds, double fps) {
    std::vector<BankFrame> out;
    int seq = 100000;  // tracking sequence ids never collide with detection ids
    const int W = c.w, H = c.h;
    for (double v : speeds) for (int q = 0; q < sequences; q++, seq++) {
        Rng rng(seed * 7777777ull + (uint64_t)(v * 100) * 131ull + q);
        PoseSpec base = nominalSpec(rng); base.distFactor = rng.uni(1.3, 1.7); base.tiltDeg = rng.uni(5, 25);
        double dirx = std::cos(rng.uni(0, 2 * kPi)), diry = std::sin(rng.uni(0, 2 * kPi));
        double omega = v * 0.15;  // deg/frame, roll
        Degrade d; d.noiseSigma = 3.0; d.blurSigma = 0.6;
        std::vector<float> bg = makeBackground(c, rng, 1.0);
        auto specAt = [&](double fr) {
            PoseSpec s = base;
            // Triangle-wave motion keeps the marker inside the frame at any speed.
            auto tri = [](double x) { double mm = std::fmod(x, 4.0); if (mm < 0) mm += 4.0; return mm < 1 ? mm : (mm < 3 ? 2 - mm : mm - 4); };
            double dpx = v * fr;
            s.dxFrac = base.dxFrac + 0.28 * tri(dirx * dpx / (0.28 * W) * 1.0 + 0.0);
            s.dyFrac = base.dyFrac + 0.28 * tri(diry * dpx / (0.28 * H) * 1.0);
            s.rollDeg = base.rollDeg + omega * fr;
            s.tiltDeg = base.tiltDeg + 8.0 * std::sin(fr * 0.05 * (1.0 + v * 0.05));
            return s;
        };
        for (int f = 0; f < seqlen; f++) {
            int sub = 1 + std::min(6, (int)(v / 3.0));   // motion blur: average over half a frame interval
            std::vector<Pose> poses;
            for (int k = 0; k < sub; k++) poses.push_back(makePose(specAt(f + (sub == 1 ? 0.0 : (k / (double)(sub - 1) - 0.5) * 0.5)), m, c));
            BankFrame bf;
            bf.seq = seq; bf.i = f; bf.t = f / fps; bf.group = "track/speed=" + fmtLevel(v);
            bf.gt = makePose(specAt(f), m, c);
            renderFrame(m, c, poses, bg, d, rng, bf.grey);
            out.push_back(std::move(bf));
        }
    }
    return out;
}

}  // namespace nftbench
