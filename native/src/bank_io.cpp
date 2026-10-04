/*
 *  bank_io.cpp
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

#include "bank_io.hpp"

#include <cstdio>
#include <filesystem>
#include <fstream>
#include <stdexcept>

#include <nlohmann/json.hpp>

#define STB_IMAGE_IMPLEMENTATION
#define STBI_ONLY_PNG
#include <stb_image.h>
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include <stb_image_write.h>

namespace nftbench {

using nlohmann::json;
namespace fs = std::filesystem;

static json poseJson(const Pose &P) {
    json a = json::array();
    for (int r = 0; r < 3; r++) { for (int q = 0; q < 3; q++) a.push_back(P.R[r][q]); a.push_back(P.t[r]); }
    return a;
}

void writeBank(const std::string &dir, const Marker &m, const std::string &markerImage, const std::string &markerDataset,
               const Camera &c, const std::vector<BankFrame> &frames, const std::string &name) {
    fs::create_directories(fs::path(dir) / "frames");
    json j;
    j["schema"] = 1; j["kind"] = "synthetic"; j["name"] = name; j["width"] = c.w; j["height"] = c.h;
    j["camera"] = {{"fx", c.fx}, {"fy", c.fy}, {"cx", c.cx}, {"cy", c.cy}};
    j["marker"] = {{"image", markerImage}, {"dataset", markerDataset}, {"dpi", m.dpi},
                   {"width_mm", m.widthMM()}, {"height_mm", m.heightMM()}};
    json arr = json::array();
    const double W = m.widthMM(), H = m.heightMM();
    const double pts[4][2] = {{0, H}, {W, H}, {W, 0}, {0, 0}};
    for (size_t k = 0; k < frames.size(); k++) {
        const BankFrame &f = frames[k];
        char fn[64]; std::snprintf(fn, sizeof(fn), "frames/%06zu.png", k);
        if (!stbi_write_png((fs::path(dir) / fn).string().c_str(), c.w, c.h, 1, f.grey.data(), c.w))
            throw std::runtime_error(std::string("cannot write ") + fn);
        json corners = json::array();
        for (auto &p : pts) { double x, y; projectMarkerPoint(f.gt, c, p[0], p[1], x, y); corners.push_back(x); corners.push_back(y); }
        arr.push_back({{"seq", f.seq}, {"i", f.i}, {"file", fn}, {"t", f.t}, {"group", f.group},
                       {"gt_pose", poseJson(f.gt)}, {"gt_corners", corners}});
    }
    j["frames"] = arr;
    std::ofstream(fs::path(dir) / "bank.json") << j.dump(1);
}

BankData readBank(const std::string &dir) {
    std::ifstream in(fs::path(dir) / "bank.json");
    if (!in) throw std::runtime_error("cannot open " + dir + "/bank.json");
    json j = json::parse(in);
    BankData b;
    b.dir = dir; b.kind = j["kind"]; b.name = j["name"]; b.width = j["width"]; b.height = j["height"];
    b.camera.w = b.width; b.camera.h = b.height;
    b.camera.fx = j["camera"]["fx"]; b.camera.fy = j["camera"]["fy"]; b.camera.cx = j["camera"]["cx"]; b.camera.cy = j["camera"]["cy"];
    const json &mk = j["marker"];
    b.markerImage = mk["image"]; b.markerDataset = mk.value("dataset", ""); b.markerDpi = mk["dpi"];
    b.markerWmm = mk["width_mm"]; b.markerHmm = mk["height_mm"];
    for (const json &f : j["frames"]) {
        BankEntry e;
        e.seq = f["seq"]; e.i = f["i"]; e.t = f["t"]; e.group = f.value("group", ""); e.file = f["file"];
        if (f.contains("gt_pose") && !f["gt_pose"].is_null()) {
            e.hasPose = true;
            for (int r = 0; r < 3; r++) { for (int q = 0; q < 3; q++) e.gt.R[r][q] = f["gt_pose"][r * 4 + q]; e.gt.t[r] = f["gt_pose"][r * 4 + 3]; }
        }
        if (f.contains("gt_corners") && !f["gt_corners"].is_null()) {
            e.hasCorners = true;
            for (int k = 0; k < 8; k++) e.corners[k] = f["gt_corners"][k];
        }
        b.frames.push_back(e);
    }
    return b;
}

std::vector<uint8_t> loadGrey(const BankData &b, size_t index) {
    const std::string path = (fs::path(b.dir) / b.frames.at(index).file).string();
    int w = 0, h = 0, n = 0;
    unsigned char *px = stbi_load(path.c_str(), &w, &h, &n, 1);
    if (!px) throw std::runtime_error("cannot read " + path);
    if (w != b.width || h != b.height) { stbi_image_free(px); throw std::runtime_error("frame size mismatch in " + path); }
    std::vector<uint8_t> out(px, px + (size_t)w * h);
    stbi_image_free(px);
    return out;
}

}  // namespace nftbench
