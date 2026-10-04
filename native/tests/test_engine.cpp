/*
 *  test_engine.cpp
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
#include "engine.hpp"
#include "synth.hpp"
#include <AR/ar.h>
using namespace nftbench;

static const std::string ROOT = NFTBENCH_SOURCE_DIR;

int main() {
    arLogLevel = AR_LOG_LEVEL_ERROR;
    Marker m; CHECK(loadMarker(ROOT + "/data/markers/pinball.jpg", 150.0, m));
    Camera c = makeCamera(640, 480, 45.0);
    PoseSpec s; s.distFactor = 1.5;
    Pose gt = makePose(s, m, c);
    Rng rng(3);
    std::vector<float> bg = makeBackground(c, rng, 1.0);
    std::vector<uint8_t> frame; Degrade d; renderFrame(m, c, {gt}, bg, d, rng, frame);

    EngineConfig cfg; cfg.dataset = ROOT + "/data/markers/pinball-d150-l2-i3/pinball"; cfg.cam = c; cfg.kpmProc = 1; cfg.threads = 1;
    Engine e;
    CHECK(e.init(cfg));
    // test_detect_finds_marker_in_clean_synthetic_frame
    float pose[3][4]; int inl = 0; double ms = 0;
    CHECK(e.detect(frame.data(), pose, &inl, &ms));
    CHECK(inl > 10 && ms > 0);
    double centreZ = pose[2][0] * m.widthMM() / 2 + pose[2][1] * m.heightMM() / 2 + pose[2][3];
    double gtZ = gt.R[2][0] * m.widthMM() / 2 + gt.R[2][1] * m.heightMM() / 2 + gt.t[2];
    CHECK(std::fabs(centreZ - gtZ) / gtZ < 0.02);
    // test_track_after_detect_returns_ok_on_same_frame
    e.setInitPose(pose);
    float tp[3][4];
    CHECK(e.track(frame.data(), tp, &ms) == 0);
    CHECK(std::fabs(tp[2][3] - pose[2][3]) / std::fabs(pose[2][3]) < 0.02);
    std::printf("test_engine: ok\n");
    return 0;
}
