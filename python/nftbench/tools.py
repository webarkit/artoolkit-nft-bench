#
#  tools.py
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

"""Locate the native tools (nft_export, nft_run, genTexData) in a build tree, on Windows and Linux.

    python -m nftbench.tools which nft_run      # prints the path, for shell scripts

Search order: $NFTBENCH_BUILD, then the CMake presets' build directories (build/windows-msvc, build/linux-gcc), each in the
multi-config (Release/) and single-config layouts.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRESET_DIRS = ("build/windows-msvc", "build/linux-gcc")


def _candidates(build: Path, name: str):
    exe = name + (".exe" if os.name == "nt" else "")
    for sub in ("native", ""):
        base = build / sub if sub else build
        yield base / "Release" / exe
        yield base / exe


def find_tool(name: str, root: Path | None = None) -> Path:
    root = Path(root) if root else ROOT
    builds = [Path(os.environ["NFTBENCH_BUILD"])] if os.environ.get("NFTBENCH_BUILD") else []
    builds += [root / d for d in PRESET_DIRS]
    for b in builds:
        for c in _candidates(b, name):
            if c.is_file():
                return c
    raise FileNotFoundError(f"{name} not found in {', '.join(map(str, builds))}; build it first: "
                            f"cmake --preset <windows-msvc|linux-gcc> && cmake --build --preset <same>")


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] == "which":
        try:
            print(find_tool(argv[1]))
            return 0
        except FileNotFoundError as e:
            print(e, file=sys.stderr)
            return 1
    print("usage: python -m nftbench.tools which <tool>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
