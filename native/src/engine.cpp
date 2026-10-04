/*
 *  engine.cpp
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

#include "engine.hpp"

#include <chrono>
#include <cstdio>
#include <cstring>

namespace nftbench {

double nowMs() {
    using namespace std::chrono;
    return duration<double, std::milli>(steady_clock::now().time_since_epoch()).count();
}

Engine::~Engine() {
    if (ar2_) ar2DeleteHandle(&ar2_);
    if (surf_) ar2FreeSurfaceSet(&surf_);
    if (kpm_) kpmDeleteHandle(&kpm_);
    if (lt_) arParamLTFree(&lt_);
}

bool Engine::init(const EngineConfig &cfg) {
    const Camera &c = cfg.cam;
    arParamClear(&cparam_, c.w, c.h, AR_DIST_FUNCTION_VERSION_DEFAULT);
    std::memset(cparam_.mat, 0, sizeof(cparam_.mat));
    cparam_.mat[0][0] = c.fx; cparam_.mat[0][2] = c.cx;
    cparam_.mat[1][1] = c.fy; cparam_.mat[1][2] = c.cy;
    cparam_.mat[2][2] = 1.0;
    lt_ = arParamLTCreate(&cparam_, AR_PARAM_LT_DEFAULT_OFFSET);
    if (!lt_) return false;
    kpm_ = kpmCreateHandle(lt_);
    if (!kpm_) return false;
    kpmSetProcMode(kpm_, (KPM_PROC_MODE)cfg.kpmProc);
    KpmRefDataSet *ref = nullptr;
    if (kpmLoadRefDataSet(cfg.dataset.c_str(), "fset3", &ref) < 0) { std::fprintf(stderr, "cannot load %s.fset3\n", cfg.dataset.c_str()); return false; }
    if (kpmChangePageNoOfRefDataSet(ref, KpmChangePageNoAllPages, 0) < 0) return false;
    if (kpmSetRefDataSet(kpm_, ref) < 0) return false;
    kpmDeleteRefDataSet(&ref);
    ar2_ = ar2CreateHandle(lt_, AR_PIXEL_FORMAT_MONO, cfg.threads);
    if (!ar2_) return false;
    // nftSimple's settings for a 640x480-class camera.
    ar2SetTrackingThresh(ar2_, 5.0); ar2SetSimThresh(ar2_, 0.50); ar2SetSearchFeatureNum(ar2_, 16);
    ar2SetSearchSize(ar2_, 12); ar2SetTemplateSize1(ar2_, 6); ar2SetTemplateSize2(ar2_, 6);
    surf_ = ar2ReadSurfaceSet(cfg.dataset.c_str(), "fset", nullptr);
    if (!surf_) { std::fprintf(stderr, "cannot load %s.fset\n", cfg.dataset.c_str()); return false; }
    return true;
}

bool Engine::detect(const uint8_t *grey, float pose[3][4], int *inliers, double *ms) {
    double t0 = nowMs();
    kpmMatching(kpm_, const_cast<ARUint8 *>(grey));
    *ms = nowMs() - t0;
    KpmResult *res = nullptr; int n = 0;
    kpmGetResult(kpm_, &res, &n);
    bool found = false; float best = 1e30f;
    for (int i = 0; i < n; i++) {
        if (res[i].camPoseF != 0) continue;
        if (!found || res[i].error < best) {
            found = true; best = res[i].error; *inliers = res[i].inlierNum;
            for (int r = 0; r < 3; r++) for (int q = 0; q < 4; q++) pose[r][q] = res[i].camPose[r][q];
        }
    }
    return found;
}

void Engine::setInitPose(const float pose[3][4]) {
    std::memcpy(trans_, pose, sizeof(trans_));
    ar2SetInitTrans(surf_, trans_);
}

int Engine::track(const uint8_t *grey, float pose[3][4], double *ms) {
    float err = 0;
    double t0 = nowMs();
    int rc = ar2Tracking(ar2_, surf_, const_cast<ARUint8 *>(grey), trans_, &err);
    *ms = nowMs() - t0;
    if (rc < 0) return rc;
    std::memcpy(pose, trans_, sizeof(trans_));
    return 0;
}

}  // namespace nftbench
