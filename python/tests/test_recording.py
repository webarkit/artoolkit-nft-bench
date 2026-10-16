#
#  test_recording.py
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

import cv2
import numpy as np
import pytest

from nftbench.recording import check_video, print_dpi, sensitive_tags


def test_print_dpi_from_measured_print():
    r = print_dpi(1637, 2048, 128.0, 159.0)
    assert r["dpi_w"] == pytest.approx(324.85, abs=0.05) and r["dpi_h"] == pytest.approx(327.16, abs=0.05)
    assert r["dpi"] == pytest.approx(326.0, abs=0.5)
    assert r["consistent"]                                   # 0.7 % apart, within measurement error


def test_print_dpi_flags_inconsistent_measurements():
    r = print_dpi(1637, 2048, 128.0, 259.0)                  # the earlier typo: aspect does not match the image
    assert not r["consistent"]


def test_print_dpi_suggests_marker_command():
    r = print_dpi(1637, 2048, 128.0, 159.0)
    assert r["marker_dir"] == "pinball-d326-l2-i1"
    assert "make_marker.sh" in r["command"] and " 326 44 326 2 1 " in r["command"]


def write_video(path, frames, fps=30.0, size=(160, 90)):
    w = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, size)
    for k in range(frames):
        w.write(np.full((size[1], size[0], 3), (k * 7) % 255, np.uint8))
    w.release()


def test_check_video_accepts_expected_format(tmp_path):
    p = tmp_path / "static-tripod.mp4"
    write_video(p, 60)
    r = check_video(p, expect_size=(160, 90), expect_fps=30.0)
    assert r["issues"] == [] and r["frames"] == 60 and not r["variable_fps"]
    assert r["duration_s"] == pytest.approx(2.0, abs=0.05)


def test_check_video_reports_wrong_size_and_fps(tmp_path):
    p = tmp_path / "x.mp4"
    write_video(p, 30, fps=25.0)
    issues = " ".join(check_video(p, expect_size=(1280, 720), expect_fps=30.0)["issues"])
    assert "resolution" in issues and "fps" in issues


def test_sensitive_tags_finds_location_and_device():
    tags = {"location": "+45.4642+009.1900/", "com.android.manufacturer": "samsung", "com.android.model": "SM-X200",
            "creation_time": "2026-10-05T10:00:00Z", "major_brand": "isom"}
    found = sensitive_tags(tags)
    assert set(found) == {"location", "com.android.manufacturer", "com.android.model"}


def test_sensitive_tags_ignores_technical_tags():
    assert sensitive_tags({"major_brand": "isom", "encoder": "Lavf60", "creation_time": "2026-10-05"}) == []
