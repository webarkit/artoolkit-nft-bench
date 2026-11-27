#
#  verify_encode.py
#  artoolkit-nft-bench
#
#  This file is part of artoolkit-nft-bench.
#
#  SPDX-License-Identifier: LGPL-3.0-or-later
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  Copyright 2026 WebARKit.
#
#  Author(s): Walter Perdan @kalwalt https://github.com/kalwalt
#

"""Does a re-encoded clip keep the measurement of its original? (scripts/encode_session.sh makes the encodes.)

    python scripts/verify_encode.py chessboard <original> <encode>
    python scripts/verify_encode.py poster <original> <encode> [--still] [--tol-frac 0.01 --psnr-median 42 --psnr-min 38 --ssim-median 0.98]

Prints one JSON object with every value and `pass`; exits 1 when a criterion fails (a missing tool or file raises instead). Criteria (data/videos/tab9-2026-11-26/README.md):

* every clip: the same frame count and the same frame timestamps (pts and time base, read with ffprobe), exactly;
* chessboard: on every 5th frame, cv2.findChessboardCornersSB (9x6) finds the board in the same frames; a calibration
  (cv2.calibrateCamera, 25 mm squares) from each file: |dfx|, |dfy|, |dcx|, |dcy| <= 0.5 px and |dRMS| <= 0.05 px;
* poster: nftbench.segment.segment_quad (confidence >= 0.5) accepts the same frames, within `--tol-frac` of the clip;
  per-frame luma PSNR and SSIM of the encode against the original (ffmpeg's psnr and ssim filters, both decoded the same
  way) above the given thresholds. The per-corner difference of the segmented corners (TL, TR, BR, BL) on frames both
  accept is reported, not a criterion; with `--still`, so is the original's own frame-to-frame corner jitter, which on a
  still clip is segment_quad's noise floor on that footage.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

from nftbench.segment import segment_quad

CORNERS = ("TL", "TR", "BR", "BL")


def timestamps(path: str) -> tuple[str, list[int]]:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "frame=pts:stream=time_base",
                          "-of", "json", path], capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    return d["streams"][0]["time_base"], [f.get("pts") for f in d["frames"]]


def frames(path: str):
    cap = cv2.VideoCapture(path)
    while True:
        ok, f = cap.read()
        if not ok:
            break
        yield f
    cap.release()


def luma_quality(orig: str, enc: str) -> dict:
    """Per-frame luma PSNR (dB) and SSIM of `enc` against `orig`, from ffmpeg's psnr and ssim filters."""
    with tempfile.TemporaryDirectory() as td:
        # Frames are paired by index (setpts=N), not by timestamp: ffmpeg rebases each file on its own start time, and a
        # camera original whose audio starts before its video would be shifted against an encode without audio, pairing
        # frame k with frame k-1. Frame count and timestamps are checked equal separately.
        # Relative stats-file names (cwd=td): a Windows drive colon would need escaping inside a filter graph.
        graph = ("[0:v]setpts=N[e0];[1:v]setpts=N[o0];[e0][o0]psnr=stats_file=psnr.log;"
                 "[2:v]setpts=N[e1];[3:v]setpts=N[o1];[e1][o1]ssim=stats_file=ssim.log")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                        "-i", str(Path(enc).resolve()), "-i", str(Path(orig).resolve()),
                        "-i", str(Path(enc).resolve()), "-i", str(Path(orig).resolve()),
                        "-filter_complex", graph, "-f", "null", "-"], cwd=td, check=True)
        psnr, ssim = [], []
        for line in (Path(td) / "psnr.log").read_text().splitlines():
            v = dict(kv.split(":", 1) for kv in line.split())
            psnr.append(float("inf") if v["psnr_y"] == "inf" else float(v["psnr_y"]))
        for line in (Path(td) / "ssim.log").read_text().splitlines():
            v = dict(kv.split(":", 1) for kv in line.split() if ":" in kv)
            ssim.append(float(v["Y"]))
    return {"psnr_y": psnr, "ssim_y": ssim}


def align(q: np.ndarray, ref: np.ndarray) -> np.ndarray:
    """`q`'s corners in `ref`'s order (the cyclic shift that matches best); segment_quad orders both alike, this is a guard."""
    return min((np.roll(q, -s, axis=0) for s in range(4)), key=lambda r: np.linalg.norm(r - ref, axis=1).sum())


def per_corner(d: np.ndarray) -> dict:
    """d: (n, 4) distances in px -> {corner: {median, p99}}."""
    if not len(d):
        return {}
    return {c: {"median": float(np.median(d[:, j])), "p99": float(np.percentile(d[:, j], 99))} for j, c in enumerate(CORNERS)}


def check_chessboard(orig: str, enc: str, pattern=(9, 6), square_mm=25.0, step=5) -> dict:
    objp = np.zeros((pattern[0] * pattern[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:pattern[0], 0:pattern[1]].T.reshape(-1, 2) * square_mm
    det, size = {}, None
    for name, path in (("orig", orig), ("enc", enc)):
        det[name] = {}
        for k, f in enumerate(frames(path)):
            if k % step:
                continue
            g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
            size = g.shape[::-1]
            found, c = cv2.findChessboardCornersSB(g, pattern)
            if found:
                det[name][k] = c.reshape(-1, 1, 2).astype(np.float32)
    so, se = set(det["orig"]), set(det["enc"])
    r = {"found_orig": len(so), "found_enc": len(se), "found_same_frames": so == se,
         "found_only_orig": sorted(so - se), "found_only_enc": sorted(se - so)}
    if not so or not se:
        r.update(calib=None, delta=None, calib_ok=False, ok=False)
        return r
    cal = {}
    for name in ("orig", "enc"):
        ks = sorted(det[name])
        rms, K, _, _, _ = cv2.calibrateCamera([objp] * len(ks), [det[name][k] for k in ks], size, None, None)
        cal[name] = {"rms": rms, "fx": K[0, 0], "fy": K[1, 1], "cx": K[0, 2], "cy": K[1, 2]}
    delta = {k: abs(cal["enc"][k] - cal["orig"][k]) for k in ("fx", "fy", "cx", "cy", "rms")}
    r.update(calib=cal, delta=delta,
             calib_ok=max(delta["fx"], delta["fy"], delta["cx"], delta["cy"]) <= 0.5 and delta["rms"] <= 0.05)
    r["ok"] = r["found_same_frames"] and r["calib_ok"]
    return r


def check_poster(orig: str, enc: str, a) -> dict:
    acc = {}
    for name, path in (("orig", orig), ("enc", enc)):
        acc[name] = []
        for f in frames(path):
            q, conf = segment_quad(f)
            acc[name].append(q.astype(np.float64) if q is not None and conf >= 0.5 else None)
    n = len(acc["orig"])
    differ = [k for k in range(n) if (acc["orig"][k] is None) != (acc["enc"][k] is None)]
    both = [k for k in range(n) if acc["orig"][k] is not None and acc["enc"][k] is not None]
    r = {"accepted_orig": sum(q is not None for q in acc["orig"]), "accepted_enc": sum(q is not None for q in acc["enc"]),
         "acceptance_differs": len(differ), "acceptance_differs_frames": differ, "acceptance_limit": a.tol_frac * n}
    r["acceptance_ok"] = len(differ) <= a.tol_frac * n and r["accepted_orig"] > 0     # nothing accepted proves nothing
    d = np.array([np.linalg.norm(align(acc["enc"][k], acc["orig"][k]) - acc["orig"][k], axis=1) for k in both])
    r["corners_enc_vs_orig"] = {"frames": len(both), **per_corner(d)}
    if a.still:
        pairs = [k for k in range(1, n) if acc["orig"][k] is not None and acc["orig"][k - 1] is not None]
        j = np.array([np.linalg.norm(align(acc["orig"][k], acc["orig"][k - 1]) - acc["orig"][k - 1], axis=1) for k in pairs])
        r["corners_orig_jitter"] = {"pairs": len(pairs), **per_corner(j)}
    lq = luma_quality(orig, enc)
    p, s = np.array(lq["psnr_y"]), np.array(lq["ssim_y"])
    if not len(p) or not len(s):
        r.update(luma=None, luma_ok=False, ok=False)
        return r
    r["luma"] = {"frames": len(p), "psnr_median": float(np.median(p)), "psnr_min": float(p.min()),
                 "ssim_median": float(np.median(s)), "ssim_min": float(s.min())}
    r["luma_ok"] = (len(p) == n and len(s) == n and r["luma"]["psnr_median"] >= a.psnr_median
                    and r["luma"]["psnr_min"] >= a.psnr_min and r["luma"]["ssim_median"] >= a.ssim_median)
    r["ok"] = r["acceptance_ok"] and r["luma_ok"]
    return r


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("kind", choices=["chessboard", "poster"])
    ap.add_argument("orig")
    ap.add_argument("enc")
    ap.add_argument("--still", action="store_true", help="also report the original's frame-to-frame corner jitter")
    ap.add_argument("--tol-frac", type=float, default=0.01, help="acceptance may differ on this share of frames")
    ap.add_argument("--psnr-median", type=float, default=42.0)
    ap.add_argument("--psnr-min", type=float, default=38.0)
    ap.add_argument("--ssim-median", type=float, default=0.98)
    a = ap.parse_args()
    tb_o, p_o = timestamps(a.orig)
    tb_e, p_e = timestamps(a.enc)
    r = {"kind": a.kind, "orig": Path(a.orig).name, "enc": Path(a.enc).name, "frames_orig": len(p_o), "frames_enc": len(p_e),
         "timestamps_identical": tb_o == tb_e and p_o == p_e and None not in p_o}
    if not r["timestamps_identical"]:          # the per-frame comparisons below pair frames by index: stop here
        r["pass"] = False
        print(json.dumps(r, default=float))
        return 1
    r.update(check_chessboard(a.orig, a.enc) if a.kind == "chessboard" else check_poster(a.orig, a.enc, a))
    r["pass"] = bool(r["timestamps_identical"] and r.pop("ok"))
    print(json.dumps(r, default=float))
    return 0 if r["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
