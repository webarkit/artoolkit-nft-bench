#
#  test_encode_scripts.py
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

"""scripts/encode_session.sh refuses bad output specs before encoding; scripts/verify_encode.py refuses a file OpenCV cannot
decode in full and an encode with another frame size."""
import importlib.util
import shutil
import subprocess
from pathlib import Path

import cv2
import pytest

from clips import chessboard_clip, poster_clip

ROOT = Path(__file__).resolve().parents[2]
ENCODE = ROOT / "scripts/encode_session.sh"


def _verify_module():
    spec = importlib.util.spec_from_file_location("verify_encode", ROOT / "scripts/verify_encode.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- encode_session.sh: every refusal happens before ffmpeg runs, so these need only a POSIX shell. ---

def _encode(tmp_path, *args):
    sh = shutil.which("bash")
    assert sh, "bash is needed to run scripts/encode_session.sh"
    return subprocess.run([sh, str(ENCODE), *map(str, args)], capture_output=True, text=True, cwd=tmp_path)


@pytest.fixture
def originals(tmp_path):
    src = tmp_path / "orig"
    src.mkdir()
    for n in ("a.mp4", "b.mp4"):
        (src / n).write_bytes(b"not a video")
    return src


@pytest.mark.parametrize("name", ["sub/x.mp4", "..\\x.mp4", "../x.mp4", ".."])
def test_encode_refuses_an_output_name_with_a_path(tmp_path, originals, name):
    spec = f"{name}=a.mp4:18"
    p = _encode(tmp_path, originals, tmp_path / "out", spec)
    assert p.returncode == 2 and "refused" in p.stderr and spec in p.stderr
    assert not (tmp_path / "out").exists()


def test_encode_refuses_a_duplicate_output_name(tmp_path, originals):
    p = _encode(tmp_path, originals, tmp_path / "out", "x.mp4=a.mp4:18", "x.mp4=b.mp4:18")
    assert p.returncode == 2 and "refused" in p.stderr and "x.mp4=b.mp4:18" in p.stderr
    assert not (tmp_path / "out").exists()


def test_encode_refuses_an_output_that_is_an_input(tmp_path, originals):
    before = (originals / "b.mp4").read_bytes()
    p = _encode(tmp_path, "--force", originals, originals, "x.mp4=a.mp4:18", "b.mp4=b.mp4:18")
    assert p.returncode == 2 and "refused" in p.stderr and "b.mp4=b.mp4:18" in p.stderr
    assert (originals / "b.mp4").read_bytes() == before and not (originals / "x.mp4").exists()


def test_encode_refuses_an_existing_output_without_force(tmp_path, originals):
    out = tmp_path / "out"
    out.mkdir()
    (out / "x.mp4").write_bytes(b"keep me")
    p = _encode(tmp_path, originals, out, "x.mp4=a.mp4:18")
    assert p.returncode == 2 and "refused" in p.stderr and "x.mp4=a.mp4:18" in p.stderr and "--force" in p.stderr
    assert (out / "x.mp4").read_bytes() == b"keep me"


def test_encode_with_force_gets_past_the_existing_output_check(tmp_path, originals):
    out = tmp_path / "out"
    out.mkdir()
    (out / "x.mp4").write_bytes(b"old")
    p = _encode(tmp_path, "--force", originals, out, "x.mp4=a.mp4:18")
    assert "refused" not in p.stderr        # it reaches ffmpeg, which fails on the fake original


# --- verify_encode.py ---

def test_decode_check_names_the_file_and_frame_of_a_short_read(tmp_path):
    ve = _verify_module()
    clip = poster_clip(tmp_path / "a.mp4", n=12)
    r = ve.decode_check({"orig": str(clip)}, {"orig": 12})
    assert r["decode_ok"] and r["decoded_orig"] == 12
    r = ve.decode_check({"orig": str(clip)}, {"orig": 15})          # ffprobe counts more than OpenCV can read
    assert not r["decode_ok"] and str(clip) in r["decode_errors"][0] and "frame 12" in r["decode_errors"][0]


def test_decode_check_fails_on_a_truncated_video(tmp_path):
    ve = _verify_module()
    clip = poster_clip(tmp_path / "a.mp4", n=12)
    cut = tmp_path / "cut.mp4"
    cut.write_bytes(clip.read_bytes()[: clip.stat().st_size // 2])
    r = ve.decode_check({"enc": str(cut)}, {"enc": 12})
    assert not r["decode_ok"] and r["decoded_enc"] < 12 and str(cut) in r["decode_errors"][0]


def _resized(src, dst, size):
    cap, frames = cv2.VideoCapture(str(src)), []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(cv2.resize(f, size, interpolation=cv2.INTER_AREA))
    cap.release()
    wr = cv2.VideoWriter(str(dst), cv2.VideoWriter_fourcc(*"mp4v"), 30.0, size)
    for f in frames:
        wr.write(f)
    wr.release()
    return dst


def test_decode_check_refuses_an_encode_with_another_frame_size(tmp_path):
    ve = _verify_module()
    orig = chessboard_clip(tmp_path / "orig.mp4", n=10)
    enc = _resized(orig, tmp_path / "enc.mp4", (480, 270))
    r = ve.decode_check({"orig": str(orig), "enc": str(enc)}, {"orig": 10, "enc": 10})
    assert not r["decode_ok"] and any("frame sizes differ" in e for e in r["decode_errors"])


def test_chessboard_check_refuses_an_encode_with_another_frame_size(tmp_path):
    ve = _verify_module()
    orig = chessboard_clip(tmp_path / "orig.mp4", n=20)
    enc = _resized(orig, tmp_path / "enc.mp4", (480, 270))
    r = ve.check_chessboard(str(orig), str(enc))
    assert r["frame_size_orig"] == (640, 360) and r["frame_size_enc"] == (480, 270) and r["ok"] is False


def test_chessboard_check_passes_an_identical_copy(tmp_path):
    ve = _verify_module()
    orig = chessboard_clip(tmp_path / "orig.mp4", n=20)
    r = ve.check_chessboard(str(orig), str(orig))
    assert r["ok"] and r["frame_size_orig"] == (640, 360) and r["found_orig"] > 0
