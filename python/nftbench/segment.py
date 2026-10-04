#
#  segment.py
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

"""Ground truth for real footage: the four corners of the printed poster, found without any NFT code.

Method: the wall colour is estimated from the frame border; pixels far from it (Lab distance above an Otsu threshold) form
the poster mask; the largest component is reduced to a quadrilateral; each side is then refined to sub-pixel accuracy by
locating the strongest edge along its normal and fitting a line, and the corners are the intersections of those lines.
Frames where the poster touches the frame border, is too small, or is not a clean convex quadrilateral are rejected, so
the output is either a trustworthy quad or nothing.
"""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

MARKER_ASPECT = 1637.0 / 2048.0   # pinball.jpg width / height


def _lab_distance(bgr: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    h, w = lab.shape[:2]
    m = max(2, int(0.04 * min(h, w)))
    border = np.concatenate([lab[:m].reshape(-1, 3), lab[-m:].reshape(-1, 3), lab[:, :m].reshape(-1, 3), lab[:, -m:].reshape(-1, 3)])
    wall = np.median(border, axis=0)
    d = np.linalg.norm(lab - wall, axis=2)
    # Ignore slow illumination changes on the wall: subtract a heavily smoothed version of the border-like level.
    return d


def order_corners(quad: np.ndarray, prev: np.ndarray | None) -> np.ndarray:
    """Return corners as TL, TR, BR, BL (clockwise on screen). With `prev`, pick the cyclic shift closest to it."""
    q = np.asarray(quad, dtype=np.float64).reshape(4, 2)
    c = q.mean(axis=0)
    ang = np.arctan2(q[:, 1] - c[1], q[:, 0] - c[0])
    q = q[np.argsort(ang)]                       # increasing angle = clockwise on screen (y down)
    if prev is None:
        start = int(np.argmin(q[:, 0] + q[:, 1]))
        return np.roll(q, -start, axis=0)
    p = np.asarray(prev, dtype=np.float64).reshape(4, 2)
    costs = [np.sum(np.linalg.norm(np.roll(q, -k, axis=0) - p, axis=1)) for k in range(4)]
    return np.roll(q, -int(np.argmin(costs)), axis=0)


def _refine_side(dist: np.ndarray, a: np.ndarray, b: np.ndarray, search: int = 6):
    """Sub-pixel edge points along side a->b; returns (vx, vy, x0, y0) of the fitted line or None."""
    v = b - a
    length = np.linalg.norm(v)
    if length < 10:
        return None
    t = v / length
    n = np.array([-t[1], t[0]])
    pts = []
    offsets = np.arange(-search, search + 1, dtype=np.float32)
    for s in np.linspace(0.12, 0.88, max(8, int(length / 4))):
        p = a + s * v
        xs = (p[0] + offsets * n[0]).astype(np.float32)
        ys = (p[1] + offsets * n[1]).astype(np.float32)
        prof = cv2.remap(dist, xs.reshape(1, -1), ys.reshape(1, -1), cv2.INTER_LINEAR).ravel()
        g = np.abs(np.gradient(prof))
        k = int(np.argmax(g))
        if g[k] <= 0 or k == 0 or k == len(g) - 1:
            continue
        den = g[k - 1] - 2 * g[k] + g[k + 1]
        dk = 0.5 * (g[k - 1] - g[k + 1]) / den if den != 0 else 0.0
        pts.append(p + (offsets[k] + dk) * n)
    if len(pts) < 5:
        return None
    vx, vy, x0, y0 = cv2.fitLine(np.array(pts, np.float32), cv2.DIST_HUBER, 0, 0.01, 0.01).ravel()
    return vx, vy, x0, y0


def _intersect(l1, l2):
    (vx1, vy1, x1, y1), (vx2, vy2, x2, y2) = l1, l2
    A = np.array([[vx1, -vx2], [vy1, -vy2]], dtype=np.float64)
    if abs(np.linalg.det(A)) < 1e-9:
        return None
    s, _ = np.linalg.solve(A, np.array([x2 - x1, y2 - y1]))
    return np.array([x1 + s * vx1, y1 + s * vy1])


def segment_quad(image: np.ndarray, min_area_frac: float = 0.002) -> tuple[np.ndarray | None, float]:
    """Find the poster quad. Returns (corners (4,2) float32 TL,TR,BR,BL or None, confidence in [0, 1])."""
    bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR) if image.ndim == 2 else image
    h, w = bgr.shape[:2]
    dist = _lab_distance(bgr)
    d8 = np.clip(dist * (255.0 / max(dist.max(), 1e-6)), 0, 255).astype(np.uint8)
    if dist.max() < 6.0:
        return None, 0.0
    thr, mask = cv2.threshold(d8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    if n < 2:
        return None, 0.0
    i = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x, y, bw, bh, area = stats[i]
    if area < min_area_frac * w * h:
        return None, 0.0
    if x <= 1 or y <= 1 or x + bw >= w - 1 or y + bh >= h - 1:
        return None, 0.0                                  # truncated by the frame border
    comp = (labels == i).astype(np.uint8) * 255
    contours, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cnt = max(contours, key=cv2.contourArea)
    hull = cv2.convexHull(cnt)
    peri = cv2.arcLength(hull, True)
    approx = None
    for eps in np.linspace(0.01, 0.08, 15):
        a = cv2.approxPolyDP(hull, eps * peri, True)
        if len(a) == 4:
            approx = a.reshape(4, 2).astype(np.float64)
            break
    if approx is None:
        return None, 0.0
    rough = order_corners(approx, None)
    rect = cv2.contourArea(cnt) / max(cv2.contourArea(rough.astype(np.float32)), 1.0)
    if rect < 0.9:
        return None, 0.0
    lines = [_refine_side(dist, rough[j], rough[(j + 1) % 4]) for j in range(4)]
    if any(l is None for l in lines):
        return None, 0.0
    corners = [_intersect(lines[(j - 1) % 4], lines[j]) for j in range(4)]
    if any(c is None for c in corners):
        return None, 0.0
    quad = np.array(corners)
    diag = np.linalg.norm(rough[2] - rough[0])
    if np.max(np.linalg.norm(quad - rough, axis=1)) > max(6.0, 0.03 * diag):
        return None, 0.0                                  # refinement disagrees with the rough quad
    widths = np.linalg.norm(quad[1] - quad[0]) + np.linalg.norm(quad[2] - quad[3])
    heights = np.linalg.norm(quad[3] - quad[0]) + np.linalg.norm(quad[2] - quad[1])
    aspect = widths / max(heights, 1e-6)
    if not (MARKER_ASPECT * 0.65 <= aspect <= MARKER_ASPECT * 1.35):
        return None, 0.0
    inside = float(np.median(dist[comp > 0]))
    conf = float(np.clip((rect - 0.85) / 0.08, 0, 1) * np.clip(inside / 40.0, 0, 1))
    return quad.astype(np.float32), conf


def segment_bank(bank_dir: Path, video: Path | None = None, report: bool = True, min_conf: float = 0.5,
                 sample: int = 24, seed: int = 0) -> dict:
    """Write gt_corners into bank.json for accepted frames; write overlays and a spot-check sheet; return counts.

    Segmentation needs colour (in grey, the poster's light areas merge with the wall), so frames are read from `video`,
    the colour source the bank was decoded from; it must yield the same number of frames as the bank.
    Without `video`, the bank's grey frames are used.
    """
    bank_dir = Path(bank_dir)
    doc = json.loads((bank_dir / "bank.json").read_text(encoding="utf-8"))
    (bank_dir / "overlay").mkdir(exist_ok=True)
    counts = {"n_total": 0, "n_accepted": 0, "n_rejected_truncated": 0, "n_rejected_lowconf": 0}
    prev = None
    tiles = []
    cap = cv2.VideoCapture(str(video)) if video is not None else None
    for f in doc["frames"]:
        counts["n_total"] += 1
        img = cv2.imread(str(bank_dir / f["file"]), cv2.IMREAD_GRAYSCALE)
        src = img
        if cap is not None:
            ok, src = cap.read()
            if not ok or src.shape[:2] != img.shape:
                raise ValueError(f"{video} does not match the bank at frame {f['i']}")
        quad, conf = segment_quad(src)
        if quad is not None and conf >= min_conf:
            quad = order_corners(quad, prev).astype(np.float32)
            prev = quad
            f["gt_corners"] = [float(v) for v in quad.reshape(-1)]
            counts["n_accepted"] += 1
        else:
            f["gt_corners"] = None
            counts["n_rejected_lowconf" if quad is not None else "n_rejected_truncated"] += 1
        vis = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        if f["gt_corners"] is not None:
            q = np.array(f["gt_corners"]).reshape(4, 2)
            cv2.polylines(vis, [np.round(q).astype(np.int32)], True, (0, 255, 0), 2)
            cv2.circle(vis, tuple(np.round(q[0]).astype(int)), 7, (0, 0, 255), -1)   # TL in red
        else:
            cv2.putText(vis, "rejected", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 0, 255), 3)
        cv2.putText(vis, f"#{f['i']}", (20, vis.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 0), 3)
        cv2.imwrite(str(bank_dir / "overlay" / Path(f["file"]).name), vis)
        tiles.append(vis)
    (bank_dir / "bank.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")
    rng = np.random.default_rng(seed)
    pick = sorted(rng.choice(len(tiles), size=min(sample, len(tiles)), replace=False))
    small = [cv2.resize(tiles[k], (480, int(480 * tiles[k].shape[0] / tiles[k].shape[1]))) for k in pick]
    while len(small) % 6:
        small.append(np.zeros_like(small[0]))
    rows = [np.hstack(small[r:r + 6]) for r in range(0, len(small), 6)]
    cv2.imwrite(str(bank_dir / "spotcheck.png"), np.vstack(rows))
    counts["spotcheck_frames"] = [int(doc["frames"][k]["i"]) for k in pick]
    if report:
        print(json.dumps(counts))
    return counts
