#
#  test_segment.py
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

from nftbench.segment import order_corners, segment_quad

W_IMG, H_IMG = 640, 360
TRUE = np.array([[250, 80], [380, 95], [372, 262], [242, 250]], np.float32)  # TL, TR, BR, BL; aspect ~0.8


def poster_texture(seed=0, contrast=1.0):
    rng = np.random.default_rng(seed)
    tex = rng.integers(0, 256, (64, 51, 3), dtype=np.uint8)
    tex = cv2.resize(tex, (510, 640), interpolation=cv2.INTER_NEAREST)
    tex = cv2.GaussianBlur(tex, (0, 0), 3)
    # Pinball-like: dark, saturated reds and blues.
    tex = (tex.astype(np.float32) * np.array([0.5, 0.3, 0.9]) * 0.7).astype(np.uint8)
    if contrast != 1.0:
        wall = 205.0
        tex = np.clip(wall + (tex.astype(np.float32) - wall) * contrast, 0, 255).astype(np.uint8)
    return tex


def scene(quad=TRUE, blur=0.0, gradient=0.0, contrast=1.0, seed=0):
    rng = np.random.default_rng(seed + 1)
    wall = np.full((H_IMG, W_IMG, 3), (200, 205, 210), np.float32)
    if gradient:
        wall *= np.linspace(1 - gradient, 1 + gradient, W_IMG, dtype=np.float32)[None, :, None]
    tex = poster_texture(seed, contrast)
    src = np.array([[0, 0], [tex.shape[1], 0], [tex.shape[1], tex.shape[0]], [0, tex.shape[0]]], np.float32)
    Hm = cv2.getPerspectiveTransform(src, quad.astype(np.float32))
    warped = cv2.warpPerspective(tex, Hm, (W_IMG, H_IMG), flags=cv2.INTER_LINEAR)
    mask = cv2.warpPerspective(np.full(tex.shape[:2], 255, np.uint8), Hm, (W_IMG, H_IMG))
    img = np.where(mask[..., None] > 127, warped.astype(np.float32), wall)
    img += rng.normal(0, 2.0, img.shape)
    img = np.clip(img, 0, 255).astype(np.uint8)
    if blur:
        img = cv2.GaussianBlur(img, (0, 0), blur)
    return img


def err(c, true=TRUE):
    return float(np.max(np.linalg.norm(c - true, axis=1)))


def test_recovers_known_quad_within_1px():
    c, conf = segment_quad(scene())
    assert c is not None and conf > 0.5
    assert err(c) < 1.0


def test_recovers_quad_under_gaussian_blur_sigma2_within_2px():
    c, _ = segment_quad(scene(blur=2.0))
    assert c is not None and err(c) < 2.0


def test_recovers_quad_with_horizontal_illumination_gradient():
    c, _ = segment_quad(scene(gradient=0.25))
    assert c is not None and err(c) < 1.5


def test_truncated_quad_returns_none():
    q = TRUE.copy(); q[:, 0] += 330   # right half leaves the frame
    c, _ = segment_quad(scene(quad=q))
    assert c is None


def test_blank_wall_returns_none():
    img = np.full((H_IMG, W_IMG, 3), 205, np.uint8)
    c, _ = segment_quad(img)
    assert c is None


def test_low_contrast_poster_returns_low_confidence_or_none():
    c, conf = segment_quad(scene(contrast=0.08))
    assert c is None or conf < 0.5


def test_order_corners_follows_previous_frame_after_roll():
    centre = TRUE.mean(axis=0)
    a = np.radians(120)
    R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    rolled = (TRUE - centre) @ R.T + centre
    # small step from the previous frame: rotate by 120 deg in 12 steps, ordering must follow each step
    prev = order_corners(TRUE, None)
    for k in range(1, 13):
        b = np.radians(10 * k)
        Rk = np.array([[np.cos(b), -np.sin(b)], [np.sin(b), np.cos(b)]])
        q = (TRUE - centre) @ Rk.T + centre
        shuffled = np.roll(q, k % 4, axis=0)             # detector returns corners in arbitrary cyclic order
        prev = order_corners(shuffled, prev)
        assert np.allclose(prev, q, atol=1e-4), f"step {k}"
    assert np.allclose(prev, rolled, atol=1e-4)


def test_order_corners_initial_is_tl_tr_br_bl():
    shuffled = TRUE[[2, 3, 0, 1]]
    assert np.allclose(order_corners(shuffled, None), TRUE)


def test_segment_bank_uses_colour_frames_from_the_video(tmp_path):
    from nftbench.segment import segment_bank
    from nftbench.video_bank import make_bank
    import json
    # A colour poster whose grey level matches the wall: invisible in grey, obvious in colour.
    img = np.full((H_IMG, W_IMG, 3), (200, 205, 210), np.uint8)
    poly = np.round(TRUE).astype(np.int32)
    cv2.fillConvexPoly(img, poly, (255, 120, 220))            # grey ~ same as the wall
    vid = tmp_path / "c.mp4"
    wr = cv2.VideoWriter(str(vid), cv2.VideoWriter_fourcc(*"mp4v"), 25.0, (W_IMG, H_IMG))
    for _ in range(3):
        wr.write(img)
    wr.release()
    bank = make_bank(vid, tmp_path / "b", "m.jpg", 220.0, "ds", marker_px=(1637, 2048))
    counts = segment_bank(bank, video=vid, report=False, sample=3)
    assert counts["n_accepted"] == 3
    q = np.array(json.loads((bank / "bank.json").read_text())["frames"][0]["gt_corners"]).reshape(4, 2)
    assert err(q) < 2.0


def test_large_poster_with_ragged_mask_edges_is_accepted():
    # Big poster (like the real clip at close range) with light patches touching its edges: the mask has notches,
    # rectangularity drops to ~0.93 and the rough quad is several pixels off, but the edges are clean.
    big = np.array([[200, 30], [432, 40], [426, 330], [194, 322]], np.float32)
    img = scene(quad=big)
    rng = np.random.default_rng(5)
    for _ in range(14):
        t = rng.uniform(0.05, 0.95); side = rng.integers(0, 4)
        a, b = big[side], big[(side + 1) % 4]
        p = a + t * (b - a)
        inward = (big.mean(axis=0) - p); inward /= np.linalg.norm(inward)
        c = p + inward * 14
        cv2.circle(img, (int(c[0]), int(c[1])), 13, (200, 205, 210), -1)   # wall-coloured patch just inside the edge
    q, conf = segment_quad(img)
    assert q is not None and conf >= 0.5
    assert err(q, big) < 2.0
