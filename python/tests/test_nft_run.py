#
#  test_nft_run.py
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

import getpass
import json
import os
import re
import socket
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ALLOWED_HOST_FIELDS = {"host_label", "os", "cpu", "cores", "threads_hw", "ram_gb", "compiler", "build_flags", "runtime"}


def exe(name):
    from nftbench.tools import find_tool
    try:
        return find_tool(name)
    except FileNotFoundError as e:
        pytest.fail(str(e))


@pytest.fixture(scope="module")
def bank(tmp_path_factory):
    out = tmp_path_factory.mktemp("bank")
    subprocess.run([exe("nft_export"), f"out={out}", f"image={ROOT / 'data/markers/pinball.jpg'}", "dpi=150",
                    "dataset=pinball-d150-l2-i3", "trials=1", "scenarios=scale", "mode=detect"], check=True,
                   capture_output=True)
    return out


def run(bank, out, dpi="150"):
    return subprocess.run([exe("nft_run"), f"bank={bank}", f"dataset={ROOT / 'data/markers/pinball-d150-l2-i3/pinball'}",
                           f"dpi={dpi}", f"out={out}"], capture_output=True, text=True, cwd=ROOT)


def test_result_header_has_only_allowed_host_fields(bank, tmp_path):
    out = tmp_path / "r.json"
    p = run(bank, out)
    assert p.returncode == 0, p.stderr
    doc = json.loads(out.read_text())
    assert set(doc["header"]["host"]) == ALLOWED_HOST_FIELDS
    text = json.dumps(doc)
    assert getpass.getuser() not in text
    assert socket.gethostname() not in text
    assert not re.search(r"[A-Za-z]:[\/]{1,2}", text), "absolute Windows path in result"


def test_result_is_scorable_and_detects_frontal_frames(bank, tmp_path):
    from nftbench.schema import check_compatible, load_bank, load_result
    out = tmp_path / "r.json"
    assert run(bank, out).returncode == 0
    b, r = load_bank(bank), load_result(out)
    check_compatible(b, r)
    assert len(r.frames) == len(b.frames) == 8
    states = {f.i if False else gf.group: f.state for f, gf in zip(r.frames, b.frames)}
    assert states["detect/scale=1.5"] == "detected"
    assert r.header["engine"] == "native" and r.header["marker_dataset"] == "pinball-d150-l2-i3"


def test_dpi_mismatch_exits_2(bank, tmp_path):
    assert run(bank, tmp_path / "r.json", dpi="220").returncode == 2
