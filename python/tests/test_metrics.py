#
#  test_metrics.py
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
import pytest
from nftbench.schema import Bank, Camera, Frame, Result, ResultFrame
from nftbench.geometry import project_corners
from nftbench.metrics import summarize, track_time_share, jitter_px

CAM = Camera(500.0, 500.0, 320.0, 240.0)
W, H = 100.0, 200.0

def pose(z=500.0, dx=0.0):
    return np.array([[1, 0, 0, -W / 2 + dx], [0, -1, 0, H / 2], [0, 0, -1, z]], dtype=float)

def bank(frames):
    return Bank("synthetic", "t", 640, 480, CAM, "m.jpg", "ds", 220.0, W, H, frames, None)

def gt_frame(seq, i, p, group="g", t=None, corners=False):
    c = project_corners(p, CAM, W, H) if corners else None
    return Frame(seq, i, f"f{seq}_{i}.png", i / 30.0 if t is None else t, group, None if corners else p, c)

def rf(seq, i, state, p, t=10.0):
    return ResultFrame(seq, i, state, p, t if state != "tracked" else None, t if state == "tracked" else None, t, t)

def result(frames):
    return Result({}, {}, frames)

def test_lost_frames_are_not_zero_error():
    b = bank([gt_frame(0, 0, pose()), gt_frame(1, 0, pose()), gt_frame(2, 0, pose())])
    nan = pose(); nan[0, 0] = math.nan
    r = result([rf(0, 0, "detected", pose(dx=1.0)), rf(1, 0, "lost", None), rf(2, 0, "detected", nan)])
    g = summarize(b, r)["groups"]["g"]
    assert g["valid_pct"] == pytest.approx(100 / 3)
    assert g["median_px"] == pytest.approx(1.0, rel=1e-6)   # 1 mm shift at 500 mm, f=500 -> 1 px

def test_frames_without_gt_are_excluded():
    no_gt = Frame(1, 0, "x.png", 0.0, "g", None, None)
    b = bank([gt_frame(0, 0, pose()), no_gt])
    r = result([rf(0, 0, "detected", pose()), rf(1, 0, "detected", pose(dx=50))])
    g = summarize(b, r)["groups"]["g"]
    assert g["n_excluded"] == 1 and g["n"] == 1 and g["ok_pct"] == 100.0

def test_corner_gt_is_used_when_present():
    b = bank([gt_frame(0, 0, pose(), corners=True)])
    g = summarize(b, result([rf(0, 0, "detected", pose(dx=2.0))]))["groups"]["g"]
    assert g["median_px"] == pytest.approx(2.0, rel=1e-6)

def test_track_time_share_hand_computed():
    # bins of 10 ms from t=0 to the last frame (0.3 s): 30 bins; bins 0..9 take 'detected', 10..29 'tracked'
    s = track_time_share([["detected", "tracked", "tracked", "tracked"]], [[0.0, 0.1, 0.2, 0.3]])
    assert s == pytest.approx(20 / 30)

def test_track_time_share_uses_timestamps_not_indices():
    s = track_time_share([["detected", "tracked", "tracked", "tracked"]], [[0.0, 0.25, 0.28, 0.3]])
    assert s == pytest.approx(5 / 30)

def test_jitter_zero_for_linear_motion():
    seq = np.stack([project_corners(pose(dx=k), CAM, W, H) for k in range(5)])
    assert jitter_px(seq) == pytest.approx(0.0, abs=1e-9)

def test_jitter_positive_for_shaking():
    seq = np.stack([project_corners(pose(dx=(k % 2) * 2.0), CAM, W, H) for k in range(6)])
    assert jitter_px(seq) > 1.0

def test_lost_events_counts_tracked_to_lost_transitions():
    fr = [gt_frame(0, i, pose()) for i in range(6)]
    st = ["detected", "tracked", "lost", "detected", "tracked", "lost"]
    r = result([rf(0, i, s, None if s == "lost" else pose()) for i, s in enumerate(st)])
    assert summarize(bank(fr), r)["groups"]["g"]["lost_events"] == 2

def test_first_lock_frame():
    fr = [gt_frame(0, i, pose()) for i in range(4)]
    st = ["lost", "lost", "detected", "tracked"]
    r = result([rf(0, i, s, None if s == "lost" else pose()) for i, s in enumerate(st)])
    assert summarize(bank(fr), r)["groups"]["g"]["first_lock_median"] == 2


def test_project_corners_with_margin_expands_the_quad():
    inner = project_corners(pose(), CAM, W, H)
    outer = project_corners(pose(), CAM, W, H, margin_mm=5.0)
    # 5 mm at 500 mm with f=500 is 5 px outward on each side
    assert np.allclose(outer - inner, [[-5, -5], [5, -5], [5, 5], [-5, 5]], atol=1e-6)


def test_estimate_margin_recovers_paper_border():
    from nftbench.metrics import estimate_margin_mm
    frames = [Frame(0, i, f"f{i}.png", i / 30, "real", None,
                    project_corners(pose(dx=i * 0.5), CAM, W, H, margin_mm=3.0)) for i in range(20)]
    st = ["detected"] + ["tracked"] * 19
    r = result([rf(0, i, s, pose(dx=i * 0.5)) for i, s in enumerate(st)])
    m, residual = estimate_margin_mm(bank(frames), r)
    assert m == pytest.approx(3.0, abs=0.05) and residual < 0.1


def test_summarize_applies_gt_margin_to_corner_ground_truth():
    f = Frame(0, 0, "f.png", 0.0, "real", None, project_corners(pose(), CAM, W, H, margin_mm=3.0))
    r = result([rf(0, 0, "detected", pose())])
    assert summarize(bank([f]), r)["groups"]["real"]["median_px"] is None or \
        summarize(bank([f]), r)["groups"]["real"]["median_px"] > 2.9
    assert summarize(bank([f]), r, gt_margin_mm=3.0)["groups"]["real"]["median_px"] == pytest.approx(0.0, abs=1e-6)


def test_error_percentiles_cover_all_valid_frames_not_only_ok_ones():
    fr = [gt_frame(k, 0, pose()) for k in range(4)]
    r = result([rf(k, 0, "detected", pose(dx=d)) for k, d in enumerate([1.0, 2.0, 8.0, 12.0])])
    g = summarize(bank(fr), r, ok_px=5.0)["groups"]["g"]
    assert g["ok_pct"] == 50.0
    assert g["median_px"] == pytest.approx(5.0)          # median of 1, 2, 8, 12
    assert g["p90_px"] > 5.0


def test_loss_right_after_detection_is_a_lost_event():
    fr = [gt_frame(0, i, pose()) for i in range(3)]
    st = ["detected", "lost", "detected"]
    r = result([rf(0, i, s, None if s == "lost" else pose()) for i, s in enumerate(st)])
    assert summarize(bank(fr), r)["groups"]["g"]["lost_events"] == 1


def test_first_lock_is_per_sequence_relative_to_its_start():
    fr = [gt_frame(s, i, pose()) for s in range(3) for i in range(5)]
    locks = {0: 0, 1: 3, 2: 4}
    r = result([rf(s, i, "detected" if i >= locks[s] else "lost", pose() if i >= locks[s] else None)
                for s in range(3) for i in range(5)])
    g = summarize(bank(fr), r)["groups"]["g"]
    assert g["first_lock_median"] == 3 and g["first_lock_max"] == 4


def test_bank_frames_missing_from_result_count_as_lost():
    fr = [gt_frame(k, 0, pose()) for k in range(4)]
    r = result([rf(0, 0, "detected", pose()), rf(1, 0, "detected", pose())])
    g = summarize(bank(fr), r)["groups"]["g"]
    assert g["n"] == 4 and g["valid_pct"] == 50.0 and g["n_missing"] == 2


def test_result_frame_not_in_bank_is_incompatible():
    from nftbench.schema import IncompatibleResult
    with pytest.raises(IncompatibleResult):
        summarize(bank([gt_frame(0, 0, pose())]), result([rf(0, 0, "detected", pose()), rf(9, 0, "detected", pose())]))
