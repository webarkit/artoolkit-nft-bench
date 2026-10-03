#
#  test_score_cli.py
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
import subprocess
import sys
from pathlib import Path

DATA = Path(__file__).parent / "data"

def write_result(tmp_path, dpi=220.0):
    doc = {"schema": 1, "header": {"engine": "native", "marker_dataset": "pinball-d220-l2-i1", "marker_dpi": dpi,
                                    "camera": {"fx": 579.4, "fy": 579.4, "cx": 320.0, "cy": 240.0}, "params": {"threads": 1}},
           "init": {}, "frames": [
               {"seq": 0, "i": 0, "state": "detected", "pose": [1,0,0,-94.5, 0,-1,0,118.25, 0,0,-1,600],
                "t_detect_ms": 40.0, "t_track_ms": None, "t_total_ms": 40.0, "blocked_ms": 40.0},
               {"seq": 1, "i": 0, "state": "lost", "pose": None,
                "t_detect_ms": 30.0, "t_track_ms": None, "t_total_ms": 30.0, "blocked_ms": 30.0}]}
    p = tmp_path / "r.json"; p.write_text(json.dumps(doc)); return p

def run(*args):
    return subprocess.run([sys.executable, "-m", "nftbench.score", *map(str, args)], capture_output=True, text=True,
                          env={**__import__("os").environ, "PYTHONPATH": str(Path(__file__).parents[1])})

def test_cli_prints_table_for_small_fixture(tmp_path):
    p = run("--bank", DATA / "bank_small.json", "--result", write_result(tmp_path))
    assert p.returncode == 0, p.stderr
    assert "detect/scale=1.5" in p.stdout and "native" in p.stdout and "| valid%" in p.stdout

def test_cli_refuses_incompatible_result(tmp_path):
    p = run("--bank", DATA / "bank_small.json", "--result", write_result(tmp_path, dpi=150.0))
    assert p.returncode != 0 and "dpi" in p.stderr
