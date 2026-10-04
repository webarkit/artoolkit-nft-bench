#
#  test_tools.py
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

import os
import sys
from pathlib import Path

import pytest

from nftbench import tools


def make(dirpath: Path, name: str) -> Path:
    dirpath.mkdir(parents=True, exist_ok=True)
    p = dirpath / (name + (".exe" if os.name == "nt" else ""))
    p.write_text("")
    return p


def test_env_build_dir_wins(tmp_path, monkeypatch):
    b = tmp_path / "custom"
    exe = make(b / "native", "nft_run")
    monkeypatch.setenv("NFTBENCH_BUILD", str(b))
    assert tools.find_tool("nft_run") == exe


def test_multi_config_release_layout(tmp_path, monkeypatch):
    monkeypatch.delenv("NFTBENCH_BUILD", raising=False)
    exe = make(tmp_path / "build/windows-msvc/native/Release", "nft_export")
    assert tools.find_tool("nft_export", root=tmp_path) == exe


def test_linux_preset_layout(tmp_path, monkeypatch):
    monkeypatch.delenv("NFTBENCH_BUILD", raising=False)
    exe = make(tmp_path / "build/linux-gcc/native", "nft_run")
    assert tools.find_tool("nft_run", root=tmp_path) == exe


def test_gentexdata_is_at_the_build_root(tmp_path, monkeypatch):
    monkeypatch.delenv("NFTBENCH_BUILD", raising=False)
    exe = make(tmp_path / "build/linux-gcc", "genTexData")
    assert tools.find_tool("genTexData", root=tmp_path) == exe


def test_missing_tool_raises_with_hint(tmp_path, monkeypatch):
    monkeypatch.delenv("NFTBENCH_BUILD", raising=False)
    with pytest.raises(FileNotFoundError, match="cmake --preset"):
        tools.find_tool("nft_run", root=tmp_path)
