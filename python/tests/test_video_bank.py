#
#  test_video_bank.py
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

import json
import math

import cv2
import numpy as np
import pytest

from nftbench.schema import load_bank
from nftbench.video_bank import make_bank


@pytest.fixture
def tiny_video(tmp_path):
    p = tmp_path / "clip.mp4"
    w = cv2.VideoWriter(str(p), cv2.VideoWriter_fourcc(*"mp4v"), 25.0, (64, 48))
    for k in range(10):
        img = np.full((48, 64, 3), 20 * k, np.uint8)
        w.write(img)
    w.release()
    return p


def test_frame_count_matches_video(tiny_video, tmp_path):
    b = load_bank(make_bank(tiny_video, tmp_path / "bank", "pinball.jpg", 220.0, "pinball-d220-l2-i1", marker_px=(1637, 2048)))
    assert len(b.frames) == 10 and b.kind == "real" and (b.width, b.height) == (64, 48)
    assert all((b.root / f.file).exists() for f in b.frames)


def test_timestamps_come_from_container_not_index(tiny_video, tmp_path):
    b = load_bank(make_bank(tiny_video, tmp_path / "bank", "pinball.jpg", 220.0, "pinball-d220-l2-i1", marker_px=(1637, 2048)))
    ts = [f.t for f in b.frames]
    assert all(t2 > t1 for t1, t2 in zip(ts, ts[1:]))
    cap = cv2.VideoCapture(str(tiny_video))
    expected = []
    while cap.read()[0]:
        expected.append(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0)
    assert ts == pytest.approx(expected)


def test_camera_uses_fovy(tiny_video, tmp_path):
    b = load_bank(make_bank(tiny_video, tmp_path / "bank", "pinball.jpg", 220.0, "pinball-d220-l2-i1", fovy_deg=60.0, marker_px=(1637, 2048)))
    assert b.camera.fy == pytest.approx(24.0 / math.tan(math.radians(30.0)))
    assert (b.camera.cx, b.camera.cy) == (32.0, 24.0)


def test_gt_fields_null_and_marker_size_from_dpi(tiny_video, tmp_path):
    b = load_bank(make_bank(tiny_video, tmp_path / "bank", "pinball.jpg", 220.0, "pinball-d220-l2-i1", marker_px=(1637, 2048)))
    assert all(f.gt_pose is None and f.gt_corners is None for f in b.frames)
    assert b.marker_w_mm == pytest.approx(1637 / 220 * 25.4)
    assert len({f.seq for f in b.frames}) == 1
