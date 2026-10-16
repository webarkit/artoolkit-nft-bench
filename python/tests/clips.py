#
#  clips.py
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

"""Synthetic clips for the recording-quality tests: the real marker image or a chessboard warped onto a plain wall."""
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
W, H = 640, 360


def _write(path, frames, fps=30.0):
    wr = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))
    for f in frames:
        wr.write(f)
    wr.release()
    return path


def _warp_onto_wall(src, quad):
    wall = np.full((H, W, 3), (200, 205, 210), np.uint8)
    h, w = src.shape[:2]
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), np.float32(quad))
    warped = cv2.warpPerspective(src, M, (W, H), flags=cv2.INTER_AREA)
    mask = cv2.warpPerspective(np.full((h, w), 255, np.uint8), M, (W, H))
    return np.where(mask[..., None] > 127, warped, wall)


def poster_clip(path, n=24, blur=0.0, truncate=False, size=150):
    img = cv2.imread(str(ROOT / "data/markers/pinball.jpg"))
    frames = []
    for k in range(n):
        x = 220 + 3 * k + (300 if truncate else 0)
        y = 60 + k
        hh = int(size * 1.25)
        quad = [[x, y], [x + size, y + 4], [x + size - 3, y + hh], [x - 2, y + hh - 3]]
        f = _warp_onto_wall(img, quad)
        if blur:
            f = cv2.GaussianBlur(f, (0, 0), blur)
        frames.append(f)
    return _write(path, frames)


def _board_image(sq=40, cols=9, rows=6):
    b = np.full(((rows + 1) * sq + 2 * sq, (cols + 1) * sq + 2 * sq, 3), 255, np.uint8)
    for j in range(rows + 1):
        for i in range(cols + 1):
            if (i + j) % 2 == 0:
                b[sq + j * sq:sq + (j + 1) * sq, sq + i * sq:sq + (i + 1) * sq] = 0
    return b


def chessboard_clip(path, cover=True, n=60):
    board = _board_image()
    frames = []
    for k in range(n):
        if cover:
            cx = 120 + (k % 5) * 100
            cy = 80 + ((k // 5) % 3) * 100
            tilt = 0.35 if k % 3 == 0 else 0.0
        else:
            cx, cy, tilt = 320, 180, 0.0
        w, h = 230, 160
        d = tilt * h
        quad = [[cx - w / 2 + d, cy - h / 2], [cx + w / 2 - d, cy - h / 2], [cx + w / 2, cy + h / 2], [cx - w / 2, cy + h / 2]]
        frames.append(_warp_onto_wall(board, quad))
    return _write(path, frames)
