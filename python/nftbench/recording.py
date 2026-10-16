#
#  recording.py
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

"""Checks for new benchmark recordings (docs/recording-guide.md): print dpi, video format, personal metadata."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np

# Phase 1 used min_dpi 30 for a 220 dpi marker; new markers keep the same ratio, so they cover equivalent distances.
MIN_DPI_RATIO = 30.0 / 220.0


def print_dpi(width_px: int, height_px: int, width_mm: float, height_mm: float, tolerance: float = 0.02) -> dict:
    """Effective dpi of a printed marker from its measured size; also the marker directory and make_marker command."""
    dpi_w = width_px / (width_mm / 25.4)
    dpi_h = height_px / (height_mm / 25.4)
    dpi = round((dpi_w + dpi_h) / 2)
    min_dpi = round(dpi * MIN_DPI_RATIO)
    marker_dir = f"pinball-d{dpi}-l2-i1"
    return {
        "dpi_w": dpi_w, "dpi_h": dpi_h, "dpi": dpi,
        "consistent": abs(dpi_w - dpi_h) / max(dpi_w, dpi_h) <= tolerance,
        "marker_dir": marker_dir,
        "command": f"scripts/make_marker.sh data/markers/pinball.jpg {dpi} {min_dpi} {dpi} 2 1 data/markers/{marker_dir}",
    }


def check_video(path: Path, expect_size: tuple[int, int] = (1280, 720), expect_fps: float = 30.0) -> dict:
    """Resolution, frame rate, constant timing and duration of a clip, with a list of human-readable issues."""
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return {"file": str(path), "issues": ["cannot open the file"]}
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    times = []
    while cap.read()[0]:
        times.append(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0)
    cap.release()
    issues = []
    if (w, h) != tuple(expect_size):
        issues.append(f"resolution {w}x{h}, expected {expect_size[0]}x{expect_size[1]}")
    if abs(fps - expect_fps) > 0.5:
        issues.append(f"fps {fps:.2f}, expected {expect_fps:g}")
    dt = np.diff(times) if len(times) > 2 else np.array([])
    variable = bool(dt.size and np.max(np.abs(dt - np.median(dt))) > 0.2 * np.median(dt))
    if variable:
        issues.append("variable frame rate (frame intervals differ by more than 20%)")
    duration = times[-1] + (float(np.median(dt)) if dt.size else 0.0) if times else 0.0
    return {"file": str(path), "width": w, "height": h, "fps": fps, "frames": len(times), "duration_s": duration,
            "variable_fps": variable, "issues": issues}


_SENSITIVE_KEYS = ("location", "gps", "manufacturer", "model", "make", "serial", "author", "artist", "owner", "comment")


def sensitive_tags(tags: dict) -> list[str]:
    """Container metadata keys that may identify a place, a device or a person."""
    return [k for k in tags if any(s in k.lower() for s in _SENSITIVE_KEYS)]


def container_tags(path: Path) -> dict:
    """Format and stream tags read with ffprobe; empty if ffprobe is not installed."""
    if shutil.which("ffprobe") is None:
        return {}
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format_tags:stream_tags", "-of", "json", str(path)],
                         capture_output=True, text=True).stdout or "{}"
    d = json.loads(out)
    tags = dict(d.get("format", {}).get("tags", {}))
    for s in d.get("streams", []):
        tags.update(s.get("tags", {}))
    return tags
