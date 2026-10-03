/*
 *  test_bank_io.cpp
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
#include "bank_io.hpp"
#include "synth.hpp"
#include <filesystem>
using namespace nftbench;

static std::string MARKER = std::string(NFTBENCH_SOURCE_DIR) + "/data/markers/pinball.jpg";

int main() {
    Marker m; CHECK(loadMarker(MARKER, 150.0, m));
    Camera c = makeCamera(64, 48, 45.0);
    std::vector<BankFrame> frames(2);
    for (int k = 0; k < 2; k++) {
        PoseSpec s; s.rollDeg = 10.0 * k;
        frames[k].seq = k; frames[k].i = 0; frames[k].t = 0.0; frames[k].group = "detect/test=1";
        frames[k].gt = makePose(s, m, c);
        frames[k].grey.assign((size_t)c.w * c.h, (uint8_t)(40 + k));
    }
    std::string dir = (std::filesystem::temp_directory_path() / "nftbench_test_bank").string();
    std::filesystem::remove_all(dir);
    writeBank(dir, m, "pinball.jpg", "pinball-d150-l2-i3", c, frames, "unit");
    BankData b = readBank(dir);
    CHECK(b.frames.size() == 2 && b.width == 64 && b.height == 48);
    CHECK_NEAR(b.camera.fx, c.fx, 1e-9);
    CHECK_NEAR(b.markerDpi, 150.0, 1e-12);
    for (int k = 0; k < 2; k++) {
        for (int r = 0; r < 3; r++) for (int q = 0; q < 3; q++) CHECK_NEAR(b.frames[k].gt.R[r][q], frames[k].gt.R[r][q], 1e-9);
        CHECK(loadGrey(b, k) == frames[k].grey);
    }
    // Corner convention shared with python/nftbench/geometry.py: TL is the projection of marker point (0, H).
    double x, y; projectMarkerPoint(frames[0].gt, c, 0.0, m.heightMM(), x, y);
    CHECK_NEAR(b.frames[0].corners[0], x, 1e-6);
    CHECK_NEAR(b.frames[0].corners[1], y, 1e-6);
    std::filesystem::remove_all(dir);
    std::printf("test_bank_io: ok\n");
    return 0;
}
