/*
 *  engine.hpp
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
// KPM detection + AR2 tracking on grey frames: the same loop nftSimple runs, without GL or video.
#include <string>
#include <AR/ar.h>
#include <AR2/tracking.h>
#include <KPM/kpm.h>
#include "synth.hpp"

namespace nftbench {

struct EngineConfig {
    std::string dataset;   // path without extension; .fset3 (KPM) and .fset (AR2) are loaded
    Camera cam{};          // pinhole, no distortion
    int kpmProc = 1;       // KPM_PROC_MODE
    int threads = 1;       // AR2 tracking threads; -1 = AR2_TRACKING_DEFAULT_THREAD_NUM. KPM (FREAK) is single-threaded.
};

class Engine {
public:
    Engine() = default;
    Engine(const Engine &) = delete;
    Engine &operator=(const Engine &) = delete;
    ~Engine();
    bool init(const EngineConfig &cfg);
    // KPM: true and pose/inliers filled if the marker was found. ms = wall time of kpmMatching.
    bool detect(const uint8_t *grey, float pose[3][4], int *inliers, double *ms);
    // AR2: 0 and pose filled on success, negative if tracking was lost. Requires setInitPose() first.
    int track(const uint8_t *grey, float pose[3][4], double *ms);
    void setInitPose(const float pose[3][4]);

private:
    ARParam cparam_{};
    ARParamLT *lt_ = nullptr;
    KpmHandle *kpm_ = nullptr;
    AR2HandleT *ar2_ = nullptr;
    AR2SurfaceSetT *surf_ = nullptr;
    float trans_[3][4] = {};
};

double nowMs();

}  // namespace nftbench
