#
#  test_geometry.py
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

import math
import numpy as np
from nftbench.geometry import project_corners, corner_error_px, pose_valid, pose_error
from nftbench.schema import Camera

CAM = Camera(fx=500.0, fy=500.0, cx=320.0, cy=240.0)
W, H = 100.0, 200.0

def frontal(z=500.0):
    # marker centre on the optical axis, marker +Z towards the camera
    return np.array([[1, 0, 0, -W / 2], [0, -1, 0, H / 2], [0, 0, -1, z]], dtype=float)

def test_frontal_pose_projects_to_expected_corners():
    c = project_corners(frontal(), CAM, W, H)
    expected = np.array([[270, 140], [370, 140], [370, 340], [270, 340]], dtype=float)
    assert np.allclose(c, expected, atol=1e-6)

def test_corner_error_zero_for_identical_pose():
    gt = project_corners(frontal(), CAM, W, H).reshape(-1)
    assert corner_error_px(frontal(), gt, CAM, W, H) < 1e-9

def test_pose_valid_rejects_nan_and_behind_camera():
    assert pose_valid(frontal(), W, H)
    bad = frontal(); bad[0, 0] = math.nan
    assert not pose_valid(bad, W, H)
    assert not pose_valid(frontal(z=-500.0), W, H)
    assert not pose_valid(None, W, H)

def test_pose_error_rotation_90deg():
    a = frontal()
    b = frontal().copy()
    rz = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]], dtype=float)
    b[:, :3] = a[:, :3] @ rz
    t_mm, r_deg = pose_error(b, a, W, H)
    assert abs(r_deg - 90.0) < 1e-6
