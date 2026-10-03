import json
from pathlib import Path
import pytest
from nftbench.schema import load_bank, load_result, check_compatible, IncompatibleResult

DATA = Path(__file__).parent / "data"

def make_result(tmp_path, **header_overrides):
    header = {"engine": "native", "marker_dataset": "pinball-d220-l2-i1", "marker_dpi": 220.0,
              "camera": {"fx": 579.4, "fy": 579.4, "cx": 320.0, "cy": 240.0}}
    header.update(header_overrides)
    doc = {"schema": 1, "header": header, "init": {},
           "frames": [{"seq": 0, "i": 0, "state": "lost", "pose": None, "t_detect_ms": 10.0,
                       "t_track_ms": None, "t_total_ms": 10.0, "blocked_ms": 10.0}]}
    p = tmp_path / "r.json"; p.write_text(json.dumps(doc)); return p

def test_load_bank_roundtrip():
    b = load_bank(DATA / "bank_small.json")
    assert b.width == 640 and b.marker_dpi == 220.0 and len(b.frames) == 2
    assert b.frames[0].gt_pose.shape == (3, 4) and b.frames[0].gt_corners is None
    assert b.frames[1].gt_corners.shape == (4, 2)

def test_check_compatible_rejects_dpi_mismatch(tmp_path):
    with pytest.raises(IncompatibleResult, match="dpi"):
        check_compatible(load_bank(DATA / "bank_small.json"), load_result(make_result(tmp_path, marker_dpi=150.0)))

def test_check_compatible_rejects_camera_mismatch(tmp_path):
    cam = {"fx": 600.0, "fy": 579.4, "cx": 320.0, "cy": 240.0}
    with pytest.raises(IncompatibleResult, match="camera"):
        check_compatible(load_bank(DATA / "bank_small.json"), load_result(make_result(tmp_path, camera=cam)))

def test_check_compatible_rejects_dataset_mismatch(tmp_path):
    with pytest.raises(IncompatibleResult, match="dataset"):
        check_compatible(load_bank(DATA / "bank_small.json"), load_result(make_result(tmp_path, marker_dataset="other")))

def test_check_compatible_accepts_matching(tmp_path):
    check_compatible(load_bank(DATA / "bank_small.json"), load_result(make_result(tmp_path)))
