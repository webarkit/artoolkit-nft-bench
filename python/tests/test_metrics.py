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
    assert summarize(bank(fr), r)["groups"]["g"]["first_lock_frame"] == 2
