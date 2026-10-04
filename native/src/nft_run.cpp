/*
 *  nft_run.cpp
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

// nft_run: the `native` runner. Reads a frame bank, runs KPM detection + AR2 tracking frame by frame (as nftSimple
// does, synchronously), and writes result.json (schema in python/nftbench/schema.py). Never reads ground truth.
//
//   nft_run bank=<dir> dataset=<path-no-ext> dpi=<f> out=<result.json> [threads=1 kpm_proc=1 repeats=1]
//
// With repeats>1 the first pass is a discarded warm-up and frame timings are medians over the remaining passes.
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <map>
#include <string>
#include <thread>
#include <vector>

#include <nlohmann/json.hpp>

#ifdef _WIN32
#include <windows.h>
#else
#include <sys/utsname.h>
#include <unistd.h>
#endif

#include "bank_io.hpp"
#include "engine.hpp"

using namespace nftbench;
using nlohmann::json;
namespace fs = std::filesystem;

#ifndef NFTBENCH_ARTK5_COMMIT
#define NFTBENCH_ARTK5_COMMIT "unknown"
#endif
#ifndef NFTBENCH_BUILD_FLAGS
#define NFTBENCH_BUILD_FLAGS "unknown"
#endif

// Host description restricted to the allow-listed fields (CONTRIBUTING.md, "Sensitive data in published files").
static json hostInfo() {
    json h;
    std::string label = "unlabelled";
    std::ifstream lf("bench.local.json");
    if (lf) {
        try { json l = json::parse(lf); label = l.value("host_label", label); } catch (...) {}
    }
    h["host_label"] = label;
    std::string os = "unknown", cpu = "unknown";
    double ramGb = 0;
    int cores = 0;
#ifdef _WIN32
    char buf[256]; DWORD sz = sizeof(buf);
    if (RegGetValueA(HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion", "CurrentBuildNumber",
                     RRF_RT_REG_SZ, nullptr, buf, &sz) == ERROR_SUCCESS) os = std::string("Windows build ") + buf;
    sz = sizeof(buf);
    if (RegGetValueA(HKEY_LOCAL_MACHINE, "HARDWARE\\DESCRIPTION\\System\\CentralProcessor\\0", "ProcessorNameString",
                     RRF_RT_REG_SZ, nullptr, buf, &sz) == ERROR_SUCCESS) cpu = buf;
    MEMORYSTATUSEX ms; ms.dwLength = sizeof(ms);
    if (GlobalMemoryStatusEx(&ms)) ramGb = ms.ullTotalPhys / (1024.0 * 1024.0 * 1024.0);
    DWORD len = 0;
    GetLogicalProcessorInformationEx(RelationProcessorCore, nullptr, &len);
    std::vector<char> info(len);
    if (len && GetLogicalProcessorInformationEx(RelationProcessorCore, (PSYSTEM_LOGICAL_PROCESSOR_INFORMATION_EX)info.data(), &len)) {
        for (DWORD off = 0; off < len;) {
            auto *p = (PSYSTEM_LOGICAL_PROCESSOR_INFORMATION_EX)(info.data() + off);
            cores++; off += p->Size;
        }
    }
#else
    struct utsname u;
    if (uname(&u) == 0) os = std::string(u.sysname) + " " + u.release;
    std::ifstream ci("/proc/cpuinfo"); std::string line;
    while (std::getline(ci, line)) if (line.rfind("model name", 0) == 0) { cpu = line.substr(line.find(':') + 2); break; }
    ramGb = (double)sysconf(_SC_PHYS_PAGES) * sysconf(_SC_PAGE_SIZE) / (1024.0 * 1024.0 * 1024.0);
#endif
    while (!cpu.empty() && cpu.back() == ' ') cpu.pop_back();
    h["os"] = os; h["cpu"] = cpu; h["cores"] = cores;
    h["threads_hw"] = (int)std::thread::hardware_concurrency();
    h["ram_gb"] = std::round(ramGb * 10) / 10;
#if defined(_MSC_VER)
    h["compiler"] = "MSVC " + std::to_string(_MSC_VER);
#elif defined(__clang__)
    h["compiler"] = std::string("clang ") + __clang_version__;
#else
    h["compiler"] = std::string("gcc ") + __VERSION__;
#endif
    h["build_flags"] = NFTBENCH_BUILD_FLAGS;
    h["runtime"] = "native";
    return h;
}

static double median(std::vector<double> v) {
    std::sort(v.begin(), v.end());
    size_t n = v.size();
    return n % 2 ? v[n / 2] : 0.5 * (v[n / 2 - 1] + v[n / 2]);
}

struct FrameOut { std::string state; bool hasPose = false; float pose[3][4]; std::vector<double> tDet, tTrk, tTot; };

int main(int argc, char **argv) {
    std::map<std::string, std::string> a;
    for (int i = 1; i < argc; i++) { std::string s = argv[i]; size_t e = s.find('='); if (e != std::string::npos) a[s.substr(0, e)] = s.substr(e + 1); }
    auto get = [&](const char *k, const char *def) { auto it = a.find(k); return it == a.end() ? std::string(def) : it->second; };
    if (!a.count("bank") || !a.count("dataset") || !a.count("dpi") || !a.count("out")) {
        std::fprintf(stderr, "usage: nft_run bank=<dir> dataset=<path-no-ext> dpi=<f> out=<result.json> [threads=1 kpm_proc=1 repeats=1]\n");
        return 2;
    }
    arLogLevel = AR_LOG_LEVEL_ERROR;
    BankData bank = readBank(a["bank"]);
    const double dpi = std::atof(a["dpi"].c_str());
    if (std::fabs(dpi - bank.markerDpi) > 1e-6) {
        std::fprintf(stderr, "error: dpi=%g but the bank was rendered for a %g dpi marker\n", dpi, bank.markerDpi);
        return 2;
    }
    EngineConfig cfg;
    cfg.dataset = a["dataset"]; cfg.cam = bank.camera;
    cfg.kpmProc = std::atoi(get("kpm_proc", "1").c_str());
    cfg.threads = std::atoi(get("threads", "1").c_str());
    const int repeats = std::max(1, std::atoi(get("repeats", "1").c_str()));

    double t0 = nowMs();
    Engine eng;
    if (!eng.init(cfg)) return 1;
    const double loadMs = nowMs() - t0;

    std::vector<FrameOut> outs(bank.frames.size());
    for (int rep = 0; rep < repeats; rep++) {
        const bool keep = repeats == 1 || rep > 0;
        bool tracking = false;
        int curSeq = -1;
        for (size_t k = 0; k < bank.frames.size(); k++) {
            const BankEntry &e = bank.frames[k];
            if (e.seq != curSeq) { curSeq = e.seq; tracking = false; }
            std::vector<uint8_t> grey = loadGrey(bank, k);
            FrameOut &o = outs[k];
            float pose[3][4]; double tDet = -1, tTrk = -1; std::string state;
            if (!tracking) {
                int inl = 0;
                if (eng.detect(grey.data(), pose, &inl, &tDet)) { state = "detected"; eng.setInitPose(pose); tracking = true; }
                else state = "lost";
            } else {
                if (eng.track(grey.data(), pose, &tTrk) == 0) state = "tracked";
                else { state = "lost"; tracking = false; }
            }
            if (!keep) continue;
            o.state = state;
            o.hasPose = state != "lost";
            if (o.hasPose) std::copy(&pose[0][0], &pose[0][0] + 12, &o.pose[0][0]);
            if (tDet >= 0) o.tDet.push_back(tDet);
            if (tTrk >= 0) o.tTrk.push_back(tTrk);
            o.tTot.push_back(std::max(tDet, 0.0) + std::max(tTrk, 0.0));
        }
    }

    json frames = json::array();
    for (size_t k = 0; k < outs.size(); k++) {
        const FrameOut &o = outs[k];
        json pose = nullptr;
        if (o.hasPose) { pose = json::array(); for (int r = 0; r < 3; r++) for (int q = 0; q < 4; q++) pose.push_back(o.pose[r][q]); }
        double tot = median(o.tTot);
        frames.push_back({{"seq", bank.frames[k].seq}, {"i", bank.frames[k].i}, {"state", o.state}, {"pose", pose},
                          {"t_detect_ms", o.tDet.empty() ? json(nullptr) : json(median(o.tDet))},
                          {"t_track_ms", o.tTrk.empty() ? json(nullptr) : json(median(o.tTrk))},
                          {"t_total_ms", tot}, {"blocked_ms", tot}});
    }
    json doc;
    doc["schema"] = 1;
    doc["header"] = {{"engine", "native"}, {"engine_version", "artoolkit5@" NFTBENCH_ARTK5_COMMIT},
                     {"build", NFTBENCH_BUILD_FLAGS}, {"host", hostInfo()},
                     {"marker_dataset", fs::path(cfg.dataset).parent_path().filename().string()},
                     {"marker_dpi", dpi}, {"bank", bank.name},
                     {"camera", {{"fx", bank.camera.fx}, {"fy", bank.camera.fy}, {"cx", bank.camera.cx}, {"cy", bank.camera.cy}}},
                     {"params", {{"threads", cfg.threads}, {"kpm_proc", cfg.kpmProc}, {"repeats", repeats}, {"mode", "sync"}}}};
    doc["init"] = {{"load_marker_ms", loadMs}};
    doc["frames"] = frames;
    fs::path out(a["out"]);
    if (out.has_parent_path()) fs::create_directories(out.parent_path());
    std::ofstream(out) << doc.dump(1);
    return 0;
}
