#
#  make_chessboard.py
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

"""Write the calibration chessboard PDF: python scripts/make_chessboard.py [--cols 9 --rows 6 --square-mm 25] --out board.pdf"""
import argparse
from pathlib import Path

from nftbench.chessboard import chessboard_pdf

ap = argparse.ArgumentParser()
ap.add_argument("--cols", type=int, default=9, help="inner corners per row")
ap.add_argument("--rows", type=int, default=6, help="inner corners per column")
ap.add_argument("--square-mm", type=float, default=25.0)
ap.add_argument("--out", type=Path, default=Path("results/local/print/chessboard-9x6-25mm.pdf"))
a = ap.parse_args()
a.out.parent.mkdir(parents=True, exist_ok=True)
a.out.write_bytes(chessboard_pdf(a.cols, a.rows, a.square_mm))
print(f"wrote {a.out}: print at 100% (actual size), then check the 100 mm ruler")
