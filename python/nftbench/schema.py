#
#  schema.py
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

"""Frame-bank and result file formats (see the spec, section 4)."""
from __future__ import annotations

import gzip
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


class IncompatibleResult(ValueError):
    """A result was produced with a different marker or camera than the bank it is scored against."""


@dataclass
class Camera:
    fx: float
    fy: float
    cx: float
    cy: float


@dataclass
class Frame:
    seq: int
    i: int
    file: str
    t: float
    group: str
    gt_pose: np.ndarray | None
    gt_corners: np.ndarray | None


@dataclass
class Bank:
    kind: str
    name: str
    width: int
    height: int
    camera: Camera
    marker_image: str
    marker_dataset: str
    marker_dpi: float
    marker_w_mm: float
    marker_h_mm: float
    frames: list[Frame]
    root: Path


@dataclass
class ResultFrame:
    seq: int
    i: int
    state: str
    pose: np.ndarray | None
    t_detect_ms: float | None
    t_track_ms: float | None
    t_total_ms: float
    blocked_ms: float


@dataclass
class Result:
    header: dict
    init: dict
    frames: list[ResultFrame]


def _read_json(path: Path) -> dict:
    path = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def _arr(v, shape):
    return None if v is None else np.asarray(v, dtype=float).reshape(shape)


def load_bank(path: Path) -> Bank:
    path = Path(path)
    if path.is_dir():
        path = path / "bank.json"
    d = _read_json(path)
    m = d["marker"]
    frames = [Frame(f["seq"], f["i"], f["file"], float(f["t"]), f.get("group", ""),
                    _arr(f.get("gt_pose"), (3, 4)), _arr(f.get("gt_corners"), (4, 2)))
              for f in d["frames"]]
    return Bank(d["kind"], d["name"], d["width"], d["height"], Camera(**d["camera"]),
                m["image"], m.get("dataset", ""), float(m["dpi"]), float(m["width_mm"]), float(m["height_mm"]),
                frames, path.parent)


def load_result(path: Path) -> Result:
    d = _read_json(path)
    frames = [ResultFrame(f["seq"], f["i"], f["state"], _arr(f.get("pose"), (3, 4)),
                          f.get("t_detect_ms"), f.get("t_track_ms"), float(f["t_total_ms"]),
                          float(f.get("blocked_ms", f["t_total_ms"])))
              for f in d["frames"]]
    return Result(d["header"], d.get("init", {}), frames)


def check_compatible(bank: Bank, result: Result) -> None:
    h = result.header
    if abs(float(h.get("marker_dpi", -1)) - bank.marker_dpi) > 1e-6:
        raise IncompatibleResult(f"marker dpi differs: result {h.get('marker_dpi')} vs bank {bank.marker_dpi}")
    if bank.marker_dataset and h.get("marker_dataset") != bank.marker_dataset:
        raise IncompatibleResult(f"marker dataset differs: result {h.get('marker_dataset')} vs bank {bank.marker_dataset}")
    cam = h.get("camera", {})
    for k in ("fx", "fy", "cx", "cy"):
        if abs(float(cam.get(k, -1)) - getattr(bank.camera, k)) > 1e-3:
            raise IncompatibleResult(f"camera {k} differs: result {cam.get(k)} vs bank {getattr(bank.camera, k)}")
