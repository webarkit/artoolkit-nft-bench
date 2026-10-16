#
#  chessboard.py
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

"""A printable calibration chessboard as a vector PDF (A4 landscape), with no third-party dependency.

Print at 100% / "actual size" (never "fit to page"), then check the 100 mm ruler and measure a square before calibrating.
"""
from __future__ import annotations

MM = 72.0 / 25.4                     # PDF points per millimetre
A4_LANDSCAPE = (841.89, 595.28)


def _f(v: float) -> str:
    return f"{v:.3f}".rstrip("0").rstrip(".")


def chessboard_pdf(cols: int = 9, rows: int = 6, square_mm: float = 25.0) -> bytes:
    """`cols` x `rows` inner corners, i.e. (cols+1) x (rows+1) squares of `square_mm`."""
    pw, ph = A4_LANDSCAPE
    nx, ny = cols + 1, rows + 1
    s = square_mm * MM
    # Layout from the top: 8 mm margin, board, 10 mm gap, ruler, label; at least 6 mm left at the bottom.
    if nx * s > pw - 20 * MM or ny * s > ph - 32 * MM:
        raise ValueError("the chessboard does not fit on an A4 landscape page with margins")
    x0, y0 = (pw - nx * s) / 2, ph - 8 * MM - ny * s
    ops = ["0 g"]
    for j in range(ny):
        for i in range(nx):
            if (i + j) % 2 == 0:
                ops.append(f"{_f(x0 + i * s)} {_f(y0 + j * s)} {_f(s)} {_f(s)} re f")
    # 100 mm ruler with 10 mm ticks, below the board.
    ry = y0 - 10 * MM
    ops.append("0.5 w")
    ops.append(f"{_f(x0)} {_f(ry)} m {_f(x0 + 100 * MM)} {_f(ry)} l S")
    for k in range(11):
        x = x0 + k * 10 * MM
        ops.append(f"{_f(x)} {_f(ry)} m {_f(x)} {_f(ry + (4 if k % 5 == 0 else 2) * MM)} l S")
    label = f"{cols}x{rows} inner corners, squares {square_mm:g} mm. Print at 100% (actual size)."
    ops.append(f"BT /F1 9 Tf {_f(x0)} {_f(ry - 6 * MM)} Td ({label}) Tj ET")
    ops.append(f"BT /F1 8 Tf {_f(x0 + 102 * MM)} {_f(ry - 1 * MM)} Td (100 mm) Tj ET")
    content = "\n".join(ops).encode("ascii")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {pw} {ph}] /Contents 4 0 R "
        f"/Resources << /Font << /F1 5 0 R >> >> >>".encode("ascii"),
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for n, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{n} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)
