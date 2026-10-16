#
#  quality.py
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

"""Content checks for a recording session (docs/recording-guide.md): is each clip usable, or should it be re-shot?

Format checks (resolution, fps, metadata) live in recording.py; these look at what is in the frames.
"""
from __future__ import annotations

import json
import math
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np

from .segment import segment_quad

POSTER_KINDS = ("static-tripod", "approach", "tilt", "roll", "fast", "occlusion", "low-light")

# Thresholds, per clip kind where they differ. Revisit after the first real session: reports show the measured values.
GT_MIN = {"default": 0.8, "occlusion": 0.5, "tilt": 0.6}      # share of frames with segmented corners
SHARP_MIN_FRAC = 0.8                                            # share of frames above SHARPNESS_MIN
SHARPNESS_MIN = 60.0                                            # variance of the Laplacian inside the marker
SHARP_EXEMPT = ("fast",)
KPM_SAMPLES = 10
KPM_MIN = {"default": 1, "static-tripod": 8}                   # sampled frames where KPM must find the marker
CHESS_MIN_FOUND = 40
CHESS_MIN_CELLS = 8                                             # of the 3x3 grid
CHESS_MIN_TILTED = 1 / 3
CHESS_TILT_RATIO = 0.94                                         # opposite-edge length ratio below this ~ more than 20 deg


def clip_kind(name: str) -> str | None:
    stem = Path(name).stem.lower()
    if stem == "calib-chessboard":
        return "chessboard"
    if stem.startswith("photo-"):
        return "photo"
    return stem if stem in POSTER_KINDS else None


def sharpness(grey: np.ndarray, quad: np.ndarray | None) -> float:
    lap = cv2.Laplacian(grey, cv2.CV_64F)
    if quad is None:
        return float(lap.var())
    mask = np.zeros(grey.shape, np.uint8)
    cv2.fillConvexPoly(mask, np.round(quad).astype(np.int32), 1)
    mask = cv2.erode(mask, np.ones((7, 7), np.uint8))           # ignore the marker's own outline
    vals = lap[mask > 0]
    return float(vals.var()) if vals.size else float(lap.var())


def _frames(path: Path):
    cap = cv2.VideoCapture(str(path))
    while True:
        ok, f = cap.read()
        if not ok:
            break
        yield f
    cap.release()


def _kpm_hits(samples: list[np.ndarray], marker: str, dpi: float, fovy: float = 45.0) -> int:
    """Run the native runner on sampled frames, each as its own sequence (detection only); count detections."""
    from .tools import find_tool
    img = cv2.imread(str(Path(marker).parent / "pinball.jpg"), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"marker image next to {marker}")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "frames").mkdir()
        h, w = samples[0].shape[:2]
        f = h / 2 / math.tan(math.radians(fovy) / 2)
        frames = []
        for k, s in enumerate(samples):
            fn = f"frames/{k:06d}.png"
            cv2.imwrite(str(td / fn), cv2.cvtColor(s, cv2.COLOR_BGR2GRAY) if s.ndim == 3 else s)
            frames.append({"seq": k, "i": 0, "file": fn, "t": 0.0, "group": "kpm", "gt_pose": None, "gt_corners": None})
        bank = {"schema": 1, "kind": "real", "name": "quality-check", "width": w, "height": h,
                "camera": {"fx": f, "fy": f, "cx": w / 2, "cy": h / 2},
                "marker": {"image": "pinball.jpg", "dataset": Path(marker).parent.name, "dpi": dpi,
                           "width_mm": img.shape[1] / dpi * 25.4, "height_mm": img.shape[0] / dpi * 25.4},
                "frames": frames}
        (td / "bank.json").write_text(json.dumps(bank), encoding="utf-8")
        out = td / "r.json"
        subprocess.run([str(find_tool("nft_run")), f"bank={td}", f"dataset={marker}", f"dpi={dpi}", f"out={out}"],
                       check=True, capture_output=True)
        res = json.loads(out.read_text(encoding="utf-8"))
        return sum(fr["state"] == "detected" for fr in res["frames"])


def check_poster_clip(path: Path, kind: str, marker: str | None = None, dpi: float | None = None,
                      max_frames: int = 300) -> dict:
    frames = list(_frames(path))
    stride = max(1, len(frames) // max_frames)
    analysed = frames[::stride]
    quads, sharp = [], []
    for f in analysed:
        q, conf = segment_quad(f)
        q = q if q is not None and conf >= 0.5 else None
        quads.append(q)
        sharp.append(sharpness(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), q))
    n = len(quads)
    gt_frac = sum(q is not None for q in quads) / n if n else 0.0
    sharp_frac = sum(s >= SHARPNESS_MIN for s in sharp) / n if n else 0.0
    reasons = []
    gt_min = GT_MIN.get(kind, GT_MIN["default"])
    if gt_frac < gt_min:
        reasons.append(f"ground truth in {gt_frac:.0%} of frames (need {gt_min:.0%}): marker cut by the frame edge, "
                       "too small, or low contrast with the background")
    if kind not in SHARP_EXEMPT and sharp_frac < SHARP_MIN_FRAC:
        reasons.append(f"sharp in {sharp_frac:.0%} of frames (need {SHARP_MIN_FRAC:.0%}, sharpness >= {SHARPNESS_MIN:g}): "
                       "motion blur or out of focus")
    r = {"file": str(path), "kind": kind, "frames": len(frames), "gt_frac": gt_frac, "sharp_frac": sharp_frac,
         "sharpness_median": float(np.median(sharp)) if sharp else 0.0, "kpm_checked": False, "kpm_hits": None,
         "quads": quads, "sharpness": sharp}
    # Summary samples: (frame, its own corners, its own sharpness), evenly spread over the analysed frames.
    pick = np.linspace(0, n - 1, min(8, n)).astype(int) if n else []
    r["samples"] = [(analysed[k], quads[k], sharp[k]) for k in pick]
    if marker and dpi and frames:
        idx = np.linspace(0, len(frames) - 1, min(KPM_SAMPLES, len(frames))).astype(int)
        hits = _kpm_hits([frames[i] for i in idx], marker, dpi)
        need = KPM_MIN.get(kind, KPM_MIN["default"])
        r.update(kpm_checked=True, kpm_hits=hits)
        if hits < need:
            reasons.append(f"KPM found the marker in {hits}/{len(idx)} sampled frames (need {need}): wrong marker or dpi, "
                           "marker too small or too dark")
    r["reasons"] = reasons
    r["status"] = "redo" if reasons else "ok"
    return r


def check_chessboard_clip(path: Path, pattern: tuple[int, int] = (9, 6), step: int = 5,
                          min_found: int = CHESS_MIN_FOUND) -> dict:
    found, cells, tilted, shape, sample = 0, set(), 0, None, None
    for k, f in enumerate(_frames(path)):
        if k % step:
            continue
        shape = f.shape[:2]
        grey = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        ok, c = cv2.findChessboardCornersSB(grey, pattern)
        if not ok:
            continue
        found += 1
        if sample is None:
            sample = f
        pts = c.reshape(-1, 2)
        h, w = shape
        for x, y in pts:
            cells.add((min(2, int(3 * x / w)), min(2, int(3 * y / h))))
        g = pts.reshape(pattern[1], pattern[0], 2)
        top, bottom = np.linalg.norm(g[0, -1] - g[0, 0]), np.linalg.norm(g[-1, -1] - g[-1, 0])
        left, right = np.linalg.norm(g[-1, 0] - g[0, 0]), np.linalg.norm(g[-1, -1] - g[0, -1])
        ratio = min(min(top, bottom) / max(top, bottom), min(left, right) / max(left, right))
        tilted += ratio < CHESS_TILT_RATIO
    tilted_frac = tilted / found if found else 0.0
    reasons = []
    if found < min_found:
        reasons.append(f"chessboard found in {found} checked frames (need {min_found}): move slower, keep it whole in view")
    if len(cells) < CHESS_MIN_CELLS:
        reasons.append(f"coverage {len(cells)}/9 image cells (need {CHESS_MIN_CELLS}): bring the board to the edges and "
                       "corners of the image too")
    if tilted_frac < CHESS_MIN_TILTED:
        reasons.append(f"tilted in {tilted_frac:.0%} of detections (need {CHESS_MIN_TILTED:.0%}): show the board at angles "
                       "up to ~45 degrees")
    return {"file": str(path), "kind": "chessboard", "found": found, "cells_covered": len(cells), "cells": sorted(cells),
            "tilted_frac": tilted_frac, "reasons": reasons, "status": "redo" if reasons else "ok", "sample_frame": sample}


def _label(img, text, org, colour, scale=0.7):
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 2)
    cv2.rectangle(img, (org[0] - 4, org[1] - th - 6), (org[0] + tw + 4, org[1] + 6), (0, 0, 0), -1)
    cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, colour, 2, cv2.LINE_AA)


def render_summary(r: dict, out_dir: Path) -> Path:
    """Write <out_dir>/<clip>.png: sampled frames with the segmented marker, or the chessboard coverage map."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    green, red = (0, 200, 0), (0, 0, 230)
    if r["kind"] == "chessboard":
        f = r["sample_frame"]
        img = f.copy() if f is not None else np.zeros((360, 640, 3), np.uint8)
        h, w = img.shape[:2]
        for i in range(3):
            for j in range(3):
                covered = (i, j) in r["cells"]
                x0, y0, x1, y1 = i * w // 3, j * h // 3, (i + 1) * w // 3, (j + 1) * h // 3
                over = img.copy()
                cv2.rectangle(over, (x0, y0), (x1, y1), green if covered else red, -1)
                img[y0:y1, x0:x1] = cv2.addWeighted(over, 0.25, img, 0.75, 0)[y0:y1, x0:x1]
                cv2.rectangle(img, (x0, y0), (x1, y1), (255, 255, 255), 1)
        _label(img, f"{r['status'].upper()}  found {r['found']}, cells {r['cells_covered']}/9, tilted {r['tilted_frac']:.0%}",
               (10, 25), green if r["status"] == "ok" else red)
        img = cv2.resize(img, (960, int(960 * h / w)))
    else:
        tiles = []
        for f, q, s in r["samples"]:
            f = cv2.resize(f, (480, int(480 * f.shape[0] / f.shape[1])))
            scale = 480 / r["samples"][0][0].shape[1]
            if q is not None:
                cv2.polylines(f, [np.round(np.asarray(q) * scale).astype(np.int32)], True, green, 2)
            else:
                _label(f, "no corners", (10, 50), red)
            _label(f, f"sharpness {s:.0f}", (10, f.shape[0] - 12), (255, 255, 255))
            tiles.append(f)
        while len(tiles) % 4:
            tiles.append(np.zeros_like(tiles[0]))
        img = np.vstack([np.hstack(tiles[i:i + 4]) for i in range(0, len(tiles), 4)])
        # Strip along the clip: green = ground truth and sharp, red = not.
        strip = np.zeros((24, img.shape[1], 3), np.uint8)
        n = len(r["quads"])
        for k in range(n):
            good = r["quads"][k] is not None and (r["kind"] in SHARP_EXEMPT or r["sharpness"][k] >= SHARPNESS_MIN)
            x0, x1 = k * img.shape[1] // n, (k + 1) * img.shape[1] // n
            strip[:, x0:max(x1, x0 + 1)] = green if good else red
        img = np.vstack([img, strip])
        kpm = f", KPM {r['kpm_hits']}/{KPM_SAMPLES}" if r["kpm_checked"] else ""
        _label(img, f"{r['status'].upper()}  {r['kind']}: ground truth {r['gt_frac']:.0%}, sharp {r['sharp_frac']:.0%}{kpm}",
               (10, 25), green if r["status"] == "ok" else red)
    out = out_dir / (Path(r["file"]).stem + ".png")
    cv2.imwrite(str(out), img)
    return out


def check_photo(path: Path) -> dict:
    img = cv2.imread(str(path))
    if img is None:
        return {"file": str(path), "kind": "photo", "status": "redo", "reasons": ["cannot read the image"], "sharpness": 0.0}
    quad, conf = segment_quad(img)
    quad = quad if quad is not None and conf >= 0.5 else None
    s = sharpness(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), quad)
    reasons = []
    if quad is None:
        reasons.append("no ground truth: marker cut by the edge, too small, or low contrast with the background")
    if s < SHARPNESS_MIN:
        reasons.append(f"sharpness {s:.0f} < {SHARPNESS_MIN:g}: motion blur or out of focus")
    return {"file": str(path), "kind": "photo", "sharpness": s, "reasons": reasons, "status": "redo" if reasons else "ok"}
