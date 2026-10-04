/*
 *  test_synth.cpp
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

#include "check.hpp"
#include "rng.hpp"
#include "synth.hpp"
#include <string>
using namespace nftbench;

static std::string MARKER = std::string(NFTBENCH_SOURCE_DIR) + "/data/markers/pinball.jpg";

static void test_rng_first_values() {
    Rng r(1);
    CHECK_NEAR(r.u01(), 0.7718103805524489, 1e-15);
    CHECK_NEAR(r.u01(), 0.10988071017396017, 1e-15);
    CHECK_NEAR(r.u01(), 0.4002747432996099, 1e-15);
}

static void test_pixel_to_plane_roundtrip(const Marker &m, const Camera &c) {
    PoseSpec s; s.tiltDeg = 30; s.rollDeg = 20; s.tiltAzimuthDeg = 45;
    Pose P = makePose(s, m, c);
    double x, y, X, Y;
    projectMarkerPoint(P, c, 50.0, 70.0, x, y);
    CHECK(pixelToPlane(P, c, x, y, X, Y));
    CHECK_NEAR(X, 50.0, 1e-6);
    CHECK_NEAR(Y, 70.0, 1e-6);
}

static void test_make_pose_frontal_distance(const Marker &m, const Camera &c) {
    PoseSpec s; s.distFactor = 1.0;
    Pose P = makePose(s, m, c);
    double x0, y0, x1, y1;
    projectMarkerPoint(P, c, 0.0, 0.0, x0, y0);
    projectMarkerPoint(P, c, 0.0, m.heightMM(), x1, y1);
    CHECK_NEAR(std::fabs(y1 - y0), 0.8 * c.h, 1e-6);
}

static void test_render_is_deterministic(const Marker &m, const Camera &c) {
    std::vector<uint8_t> a, b;
    for (auto *out : {&a, &b}) {
        Rng rng(7);
        PoseSpec s; Pose P = makePose(s, m, c);
        Degrade d; d.noiseSigma = 5;
        std::vector<float> bg = makeBackground(c, rng, 1.0);
        renderFrame(m, c, {P}, bg, d, rng, *out);
    }
    CHECK(a == b);
    CHECK(a.size() == (size_t)c.w * c.h);
}

int main() {
    test_rng_first_values();
    Marker m;
    CHECK(loadMarker(MARKER, 150.0, m));
    Camera c = makeCamera(640, 480, 45.0);
    CHECK_NEAR(c.fx, 240.0 / std::tan(22.5 * 3.14159265358979323846 / 180.0), 1e-9);
    test_pixel_to_plane_roundtrip(m, c);
    test_make_pose_frontal_distance(m, c);
    test_render_is_deterministic(m, c);
    std::printf("test_synth: ok\n");
    return 0;
}
