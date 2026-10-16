#
#  test_chessboard.py
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

import re

from nftbench.chessboard import chessboard_pdf

MM = 72.0 / 25.4


def test_pdf_is_a4_landscape_with_the_right_number_of_squares():
    pdf = chessboard_pdf(cols=9, rows=6, square_mm=25.0)
    assert pdf.startswith(b"%PDF-1.4") and pdf.rstrip().endswith(b"%%EOF")
    assert b"/MediaBox [0 0 841.89 595.28]" in pdf
    squares = re.findall(rb"([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+) re f", pdf)
    black = [s for s in squares if abs(float(s[2]) - 25.0 * MM) < 0.01]
    assert len(black) == 35                      # (9+1) x (6+1) squares, half of 70 are black


def test_squares_have_the_requested_physical_size():
    pdf = chessboard_pdf(cols=9, rows=6, square_mm=20.0)
    sizes = {round(float(w) / MM, 3) for _, _, w, h in re.findall(rb"([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+) re f", pdf)}
    assert 20.0 in sizes


def test_pdf_states_size_and_carries_a_100mm_ruler():
    pdf = chessboard_pdf(cols=9, rows=6, square_mm=25.0)
    assert b"9x6 inner corners, squares 25 mm" in pdf and b"100 mm" in pdf
    assert re.search(rb"([\d.]+) ([\d.]+) m ([\d.]+) ([\d.]+) l S", pdf)


def test_pdf_xref_offsets_are_valid():
    pdf = chessboard_pdf(cols=9, rows=6, square_mm=25.0)
    xref = int(re.search(rb"startxref\s+(\d+)", pdf).group(1))
    assert pdf[xref:xref + 4] == b"xref"
    offsets = [int(o) for o in re.findall(rb"(\d{10}) 00000 n", pdf)]
    for k, off in enumerate(offsets, start=1):
        assert pdf[off:].startswith(f"{k} 0 obj".encode())


def test_opencv_finds_all_inner_corners_in_the_rasterised_page():
    import cv2
    import numpy as np
    pdf = chessboard_pdf(cols=9, rows=6, square_mm=25.0)
    px_per_pt = 4.0 / MM                                   # 4 px per mm
    h, w = int(595.28 * px_per_pt), int(841.89 * px_per_pt)
    img = np.full((h, w), 255, np.uint8)
    for x, y, rw, rh in re.findall(rb"([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+) re f", pdf):
        x, y, rw, rh = (float(v) * px_per_pt for v in (x, y, rw, rh))
        img[int(round(h - y - rh)):int(round(h - y)), int(round(x)):int(round(x + rw))] = 0
    found, corners = cv2.findChessboardCornersSB(img, (9, 6))
    assert found and len(corners) == 54
    step = np.median(np.linalg.norm(np.diff(corners.reshape(6, 9, 2), axis=1), axis=2))
    assert abs(step - 100.0) < 1.0                         # 25 mm at 4 px/mm
