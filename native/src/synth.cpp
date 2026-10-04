/*
 *  synth.cpp
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

#include "synth.hpp"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>

#include <AR/ar.h>
#include <AR2/imageFormat.h>
#include <AR2/util.h>

namespace nftbench {

Camera makeCamera(int w, int h, double fovyDeg) {
    Camera c; c.w = w; c.h = h;
    c.fx = c.fy = h / 2.0 / std::tan(deg2rad(fovyDeg) / 2.0);
    c.cx = w / 2.0; c.cy = h / 2.0;
    return c;
}

void matMul(const Mat3 a, const Mat3 b, Mat3 out) {
    Mat3 r;
    for (int i = 0; i < 3; i++) for (int j = 0; j < 3; j++) { r[i][j] = 0; for (int k = 0; k < 3; k++) r[i][j] += a[i][k] * b[k][j]; }
    memcpy(out, r, sizeof(r));
}
void rotAxis(double ax, double ay, double az, double ang, Mat3 R) {
    double n = std::sqrt(ax * ax + ay * ay + az * az); ax /= n; ay /= n; az /= n;
    double c = std::cos(ang), s = std::sin(ang), C = 1 - c;
    R[0][0] = c + ax * ax * C;      R[0][1] = ax * ay * C - az * s; R[0][2] = ax * az * C + ay * s;
    R[1][0] = ay * ax * C + az * s; R[1][1] = c + ay * ay * C;      R[1][2] = ay * az * C - ax * s;
    R[2][0] = az * ax * C - ay * s; R[2][1] = az * ay * C + ax * s; R[2][2] = c + az * az * C;
}


bool loadMarker(const std::string &jpgPath, double dpi, Marker &m) {
    const char *jpg = jpgPath.c_str();
    char base[1024], ext[64];
    ar2UtilDivideExt(jpg, base, ext);
    AR2JpegImageT *img = ar2ReadJpegImage(base, ext);
    if (!img) { fprintf(stderr, "Cannot read %s\n", jpg); return false; }
    Level l0; l0.w = img->xsize; l0.h = img->ysize; l0.px.resize((size_t)l0.w * l0.h);
    for (int i = 0; i < l0.w * l0.h; i++) {
        if (img->nc == 1) l0.px[i] = img->image[i];
        else { const ARUint8 *p = img->image + i * img->nc; l0.px[i] = 0.299f * p[0] + 0.587f * p[1] + 0.114f * p[2]; }
    }
    ar2FreeJpegImage(&img);
    m.dpi = dpi;
    m.pyr.push_back(std::move(l0));
    while (m.pyr.back().w >= 32 && m.pyr.back().h >= 32) {
        const Level &p = m.pyr.back();
        Level n; n.w = p.w / 2; n.h = p.h / 2; n.px.resize((size_t)n.w * n.h);
        for (int y = 0; y < n.h; y++) for (int x = 0; x < n.w; x++)
            n.px[(size_t)y * n.w + x] = 0.25f * (p.px[(size_t)(2 * y) * p.w + 2 * x] + p.px[(size_t)(2 * y) * p.w + 2 * x + 1] +
                                                 p.px[(size_t)(2 * y + 1) * p.w + 2 * x] + p.px[(size_t)(2 * y + 1) * p.w + 2 * x + 1]);
        m.pyr.push_back(std::move(n));
    }
    return true;
}

static inline float sampleBilinear(const Level &L, double x, double y) {  // x,y in pixel-centre coords of the level
    x = std::min(std::max(x, 0.0), L.w - 1.001); y = std::min(std::max(y, 0.0), L.h - 1.001);
    int x0 = (int)x, y0 = (int)y; float fx = (float)(x - x0), fy = (float)(y - y0);
    const float *p = &L.px[(size_t)y0 * L.w + x0];
    return (p[0] * (1 - fx) + p[1] * fx) * (1 - fy) + (p[L.w] * (1 - fx) + p[L.w + 1] * fx) * fy;
}

// Frame pixel -> marker plane millimetres. Returns false if the ray points away from the plane.
bool pixelToPlane(const Pose &P, const Camera &c, double x, double y, double &X, double &Y) {
    double d[3] = {(x - c.cx) / c.fx, (y - c.cy) / c.fy, 1.0};
    double C[3], D[3];
    for (int i = 0; i < 3; i++) {
        C[i] = -(P.R[0][i] * P.t[0] + P.R[1][i] * P.t[1] + P.R[2][i] * P.t[2]);   // camera centre in marker frame
        D[i] = P.R[0][i] * d[0] + P.R[1][i] * d[1] + P.R[2][i] * d[2];             // ray direction in marker frame
    }
    if (std::fabs(D[2]) < 1e-9) return false;
    double s = -C[2] / D[2];
    if (s <= 0) return false;
    X = C[0] + s * D[0]; Y = C[1] + s * D[1];
    return true;
}

void projectMarkerPoint(const Pose &P, const Camera &c, double X, double Y, double &x, double &y) {
    double pc[3];
    for (int i = 0; i < 3; i++) pc[i] = P.R[i][0] * X + P.R[i][1] * Y + P.t[i];
    x = c.fx * pc[0] / pc[2] + c.cx; y = c.fy * pc[1] / pc[2] + c.cy;
}

void gaussianBlur(std::vector<float> &img, int w, int h, double sigma) {
    if (sigma < 0.05) return;
    int r = std::max(1, (int)std::ceil(3 * sigma));
    std::vector<float> k(2 * r + 1); float sum = 0;
    for (int i = -r; i <= r; i++) { k[i + r] = (float)std::exp(-0.5 * i * i / (sigma * sigma)); sum += k[i + r]; }
    for (float &v : k) v /= sum;
    std::vector<float> tmp(img.size());
    for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) {
        float a = 0; for (int i = -r; i <= r; i++) a += k[i + r] * img[(size_t)y * w + std::min(std::max(x + i, 0), w - 1)];
        tmp[(size_t)y * w + x] = a; }
    for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) {
        float a = 0; for (int i = -r; i <= r; i++) a += k[i + r] * tmp[(size_t)std::min(std::max(y + i, 0), h - 1) * w + x];
        img[(size_t)y * w + x] = a; }
}



// Smooth random background so that the marker is not floating on a flat field.
std::vector<float> makeBackground(const Camera &c, Rng &rng, double amp) {
    std::vector<float> bg((size_t)c.w * c.h);
    for (float &v : bg) v = (float)rng.gauss();
    gaussianBlur(bg, c.w, c.h, 6.0);
    float mx = 1e-6f; for (float v : bg) mx = std::max(mx, std::fabs(v));
    for (float &v : bg) v = 115.0f + (float)(amp * 45.0) * v / mx;
    return bg;
}

// Renders one grey-level frame. 'poses' > 1 gives motion blur by averaging sub-frame renders.
void renderFrame(const Marker &m, const Camera &cam, const std::vector<Pose> &poses, const std::vector<float> &bg,
                 const Degrade &dg, Rng &rng, std::vector<uint8_t> &out) {
    std::vector<float> acc((size_t)cam.w * cam.h, 0.0f);
    for (const Pose &P : poses) {
        // Choose a mip level from the source-pixels-per-frame-pixel scale at the marker centre.
        double X0, Y0, X1, Y1, X2, Y2;
        bool ok = pixelToPlane(P, cam, cam.cx, cam.cy, X0, Y0) && pixelToPlane(P, cam, cam.cx + 1, cam.cy, X1, Y1) &&
                  pixelToPlane(P, cam, cam.cx, cam.cy + 1, X2, Y2);
        double scale = 1.0;
        if (ok) {
            double s1 = std::hypot(X1 - X0, Y1 - Y0), s2 = std::hypot(X2 - X0, Y2 - Y0);
            scale = std::max(s1, s2) / 25.4 * m.dpi;
        }
        int lvl = std::min((int)m.pyr.size() - 1, std::max(0, (int)std::floor(std::log2(std::max(scale, 1.0)) + 0.25)));
        const Level &L = m.pyr[lvl]; double ls = (double)(1 << lvl);
        static const double so[2] = {-0.25, 0.25};
        for (int y = 0; y < cam.h; y++) for (int x = 0; x < cam.w; x++) {
            float a = 0;
            for (int sy = 0; sy < 2; sy++) for (int sx = 0; sx < 2; sx++) {
                double X, Y; float v = bg[(size_t)y * cam.w + x];
                if (pixelToPlane(P, cam, x + so[sx], y + so[sy], X, Y)) {
                    double u = X / 25.4 * m.dpi - 0.5, vv = m.pyr[0].h - 0.5 - Y / 25.4 * m.dpi;
                    if (u >= 0 && u <= m.pyr[0].w - 1 && vv >= 0 && vv <= m.pyr[0].h - 1)
                        v = sampleBilinear(L, (u + 0.5) / ls - 0.5, (vv + 0.5) / ls - 0.5);
                }
                a += v;
            }
            acc[(size_t)y * cam.w + x] += a * 0.25f;
        }
    }
    for (float &v : acc) v /= (float)poses.size();

    // Occlusion patch over the marker (use the middle pose).
    if (dg.occlusion > 0) {
        const Pose &P = poses[poses.size() / 2];
        double xs[4], ys[4], W = m.widthMM(), H = m.heightMM();
        projectMarkerPoint(P, cam, 0, 0, xs[0], ys[0]); projectMarkerPoint(P, cam, W, 0, xs[1], ys[1]);
        projectMarkerPoint(P, cam, W, H, xs[2], ys[2]); projectMarkerPoint(P, cam, 0, H, xs[3], ys[3]);
        double x0 = *std::min_element(xs, xs + 4), x1 = *std::max_element(xs, xs + 4);
        double y0 = *std::min_element(ys, ys + 4), y1 = *std::max_element(ys, ys + 4);
        double bw = x1 - x0, bh = y1 - y0, a = std::sqrt(dg.occlusion);
        double pw = bw * std::min(1.0, a * rng.uni(0.8, 1.25)), ph = bh * std::min(1.0, dg.occlusion * bw * bh / std::max(pw * bh, 1.0));
        double px0 = x0 + rng.u01() * (bw - pw), py0 = y0 + rng.u01() * (bh - ph);
        for (int y = std::max(0, (int)py0); y < std::min(cam.h, (int)(py0 + ph)); y++)
            for (int x = std::max(0, (int)px0); x < std::min(cam.w, (int)(px0 + pw)); x++) acc[(size_t)y * cam.w + x] = 70.0f;
    }

    gaussianBlur(acc, cam.w, cam.h, dg.blurSigma);
    out.resize(acc.size());
    for (int y = 0; y < cam.h; y++) for (int x = 0; x < cam.w; x++) {
        double v = acc[(size_t)y * cam.w + x];
        v = (v - 128.0) * dg.gain + 128.0 + dg.offset;
        if (dg.ramp != 0) v *= 1.0 + dg.ramp * ((double)x / cam.w - 0.5) * 2.0;
        if (dg.noiseSigma > 0) v += dg.noiseSigma * rng.gauss();
        out[(size_t)y * cam.w + x] = (uint8_t)std::min(255.0, std::max(0.0, v + 0.5));
    }
}


Pose makePose(const PoseSpec &s, const Marker &m, const Camera &cam) {
    double W = m.widthMM(), H = m.heightMM();
    double d0 = cam.fy * H / (0.8 * cam.h);
    double Zc = d0 * s.distFactor;
    Mat3 Rbase = {{1, 0, 0}, {0, -1, 0}, {0, 0, -1}};   // marker +Z (out of page) towards the camera, camera y down
    Mat3 Rroll, Rtilt, Rm, R;
    rotAxis(0, 0, 1, deg2rad(s.rollDeg), Rroll);
    rotAxis(std::cos(deg2rad(s.tiltAzimuthDeg)), std::sin(deg2rad(s.tiltAzimuthDeg)), 0, deg2rad(s.tiltDeg), Rtilt);
    // Tilt about the marker's own centre, roll in-plane first.
    matMul(Rtilt, Rroll, Rm);
    matMul(Rbase, Rm, R);
    Pose P; memcpy(P.R, R, sizeof(R));
    double px = cam.cx + s.dxFrac * cam.w, py = cam.cy + s.dyFrac * cam.h;
    double C0[3] = {Zc * (px - cam.cx) / cam.fx, Zc * (py - cam.cy) / cam.fy, Zc};
    // Rotation is about the marker centre (W/2, H/2, 0): t = C0 - R * centre.
    for (int i = 0; i < 3; i++) P.t[i] = C0[i] - (R[i][0] * W * 0.5 + R[i][1] * H * 0.5);
    return P;
}


}  // namespace nftbench
