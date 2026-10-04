/*
 *  synth.hpp
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
// Synthetic NFT frame rendering with a known pose (moved unchanged from the exploratory nft_eval harness).
#include <cstdint>
#include <string>
#include <vector>
#include "rng.hpp"

namespace nftbench {

typedef double Mat3[3][3];
struct Pose { double R[3][3]; double t[3]; };  // marker -> camera (ARToolKit convention, millimetres)
struct Camera { int w, h; double fx, fy, cx, cy; };

struct Level { int w, h; std::vector<float> px; };

struct Marker {
    std::vector<Level> pyr;  // pyr[0] = full resolution luma
    double dpi = 150.0;
    double widthMM() const { return pyr[0].w / dpi * 25.4; }
    double heightMM() const { return pyr[0].h / dpi * 25.4; }
};

struct Degrade {
    double blurSigma = 0;     // optical blur, px
    double noiseSigma = 0;    // additive gaussian, grey levels
    double gain = 1.0;        // contrast about mid-grey
    double offset = 0;        // brightness
    double ramp = 0;          // horizontal illumination gradient, +-fraction
    double occlusion = 0;     // fraction of the marker's projected bbox covered by a flat patch
    double bgContrast = 1.0;  // background texture amplitude multiplier
};

struct PoseSpec {
    double distFactor = 1.5;   // multiples of the "marker fills 80% of frame height" distance
    double tiltDeg = 0;        // out-of-plane tilt
    double tiltAzimuthDeg = 0; // direction of tilt axis in the marker plane
    double rollDeg = 0;        // in-plane rotation
    double dxFrac = 0, dyFrac = 0;  // marker-centre offset from frame centre, fraction of frame size
};

void matMul(const Mat3 a, const Mat3 b, Mat3 out);
void rotAxis(double ax, double ay, double az, double ang, Mat3 R);
// Pinhole camera matching arParamClearWithFOVy(): f = (h/2)/tan(fovy/2), principal point at (w/2, h/2).
Camera makeCamera(int w, int h, double fovyDeg);
bool loadMarker(const std::string &jpg, double dpi, Marker &m);
bool pixelToPlane(const Pose &P, const Camera &c, double x, double y, double &X, double &Y);
void projectMarkerPoint(const Pose &P, const Camera &c, double X, double Y, double &x, double &y);
void gaussianBlur(std::vector<float> &img, int w, int h, double sigma);
std::vector<float> makeBackground(const Camera &c, Rng &rng, double amp);
void renderFrame(const Marker &m, const Camera &cam, const std::vector<Pose> &poses, const std::vector<float> &bg,
                 const Degrade &dg, Rng &rng, std::vector<uint8_t> &out);
Pose makePose(const PoseSpec &s, const Marker &m, const Camera &cam);

}  // namespace nftbench
