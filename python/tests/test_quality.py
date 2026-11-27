#
#  test_quality.py
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

import pytest

from clips import chessboard_clip, poster_clip
from nftbench.quality import check_chessboard_clip, check_poster_clip, clip_kind

MARKER = "data/markers/pinball-d150-l2-i3/pinball"


def test_clip_kind_from_guide_names():
    assert clip_kind("calib-chessboard.mp4") == "chessboard"
    assert clip_kind("static-tripod.mp4") == "static-tripod"
    assert clip_kind("low-light.MP4") == "low-light"
    assert clip_kind("photo-03.jpg") == "photo"
    assert clip_kind("holiday.mp4") is None


def test_good_poster_clip_is_ok(tmp_path):
    r = check_poster_clip(poster_clip(tmp_path / "approach.mp4"), "approach")
    assert r["status"] == "ok", r["reasons"]
    assert r["gt_frac"] >= 0.8 and r["sharp_frac"] >= 0.8


def test_blurred_poster_clip_fails_on_sharpness(tmp_path):
    r = check_poster_clip(poster_clip(tmp_path / "approach.mp4", blur=5.0), "approach")
    assert r["status"] == "redo" and any("sharp" in s for s in r["reasons"])


def test_fast_clip_is_exempt_from_sharpness(tmp_path):
    r = check_poster_clip(poster_clip(tmp_path / "fast.mp4", blur=5.0), "fast")
    assert not any("sharp" in s for s in r["reasons"])


def test_truncated_poster_fails_on_ground_truth(tmp_path):
    r = check_poster_clip(poster_clip(tmp_path / "roll.mp4", truncate=True), "roll")
    assert r["status"] == "redo" and any("ground truth" in s for s in r["reasons"])


def test_kpm_detection_on_sampled_frames(tmp_path):
    r = check_poster_clip(poster_clip(tmp_path / "static-tripod.mp4", size=220), "static-tripod", marker=MARKER, dpi=150.0)
    assert r["kpm_checked"] and r["kpm_hits"] >= 8, r


def test_chessboard_covering_the_frame_is_ok(tmp_path):
    r = check_chessboard_clip(chessboard_clip(tmp_path / "calib-chessboard.mp4"), step=1, min_found=40)
    assert r["status"] == "ok", r["reasons"]
    assert r["cells_covered"] >= 8 and r["tilted_frac"] >= 0.3


def test_chessboard_only_in_the_centre_fails_on_coverage(tmp_path):
    r = check_chessboard_clip(chessboard_clip(tmp_path / "calib-chessboard.mp4", cover=False), step=1, min_found=40)
    assert r["status"] == "redo" and any("coverage" in s for s in r["reasons"])
    assert any("tilt" in s for s in r["reasons"])


def test_summary_images_are_written(tmp_path):
    from nftbench.quality import render_summary
    p = check_poster_clip(poster_clip(tmp_path / "approach.mp4"), "approach")
    c = check_chessboard_clip(chessboard_clip(tmp_path / "calib-chessboard.mp4"), step=1, min_found=40)
    for r in (p, c):
        out = render_summary(r, tmp_path / "out")
        import cv2
        img = cv2.imread(str(out))
        assert img is not None and img.shape[1] >= 800


def test_quality_cli_reports_and_exits_nonzero_on_redo(tmp_path):
    import subprocess, sys
    from pathlib import Path
    d = tmp_path / "session"; d.mkdir()
    poster_clip(d / "approach.mp4")
    poster_clip(d / "roll.mp4", truncate=True)
    root = Path(__file__).resolve().parents[2]
    p = subprocess.run([sys.executable, str(root / "scripts/check_recording.py"), "quality", str(d), "--out", str(tmp_path / "rep")],
                       capture_output=True, text=True)
    assert p.returncode == 1
    assert "ok    approach.mp4" in p.stdout and "redo  roll.mp4" in p.stdout and "ground truth" in p.stdout


def test_check_photo_flags_blur_and_missing_marker(tmp_path):
    import cv2
    from clips import poster_clip
    from nftbench.quality import check_photo
    clip = poster_clip(tmp_path / "c.mp4", n=1)
    cap = cv2.VideoCapture(str(clip)); ok, f = cap.read(); cap.release()
    cv2.imwrite(str(tmp_path / "photo-01.jpg"), f)
    cv2.imwrite(str(tmp_path / "photo-02.jpg"), cv2.GaussianBlur(f, (0, 0), 5))
    cv2.imwrite(str(tmp_path / "photo-03.jpg"), f[:, :200])               # marker cropped away
    assert check_photo(tmp_path / "photo-01.jpg")["status"] == "ok"
    assert any("sharp" in s for s in check_photo(tmp_path / "photo-02.jpg")["reasons"])
    assert any("ground truth" in s for s in check_photo(tmp_path / "photo-03.jpg")["reasons"])


def test_summary_samples_pair_each_frame_with_its_own_corners(tmp_path):
    import numpy as np
    from nftbench.segment import segment_quad
    r = check_poster_clip(poster_clip(tmp_path / "approach.mp4", n=40), "approach", max_frames=13)
    assert len(r["samples"]) == 8
    for frame, quad, sharp in r["samples"]:
        q, conf = segment_quad(frame)
        assert quad is not None and q is not None
        assert np.max(np.abs(q - quad)) < 1e-3
