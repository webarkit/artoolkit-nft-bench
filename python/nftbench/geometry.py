# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright 2026 webarkit contributors. Part of artoolkit-nft-bench.
"""Pose projection and error measures. Poses are 3x4 [R|t], marker to camera, millimetres (ARToolKit convention)."""
from __future__ import annotations

import numpy as np

from .schema import Camera


def _marker_corners_mm(w_mm: float, h_mm: float) -> np.ndarray:
    # Marker-image TL, TR, BR, BL; marker frame origin at the image's bottom-left, y up.
    return np.array([[0, h_mm, 0], [w_mm, h_mm, 0], [w_mm, 0, 0], [0, 0, 0]], dtype=float)


def _camera_points(pose: np.ndarray, w_mm: float, h_mm: float) -> np.ndarray:
    P = np.asarray(pose, dtype=float)
    return _marker_corners_mm(w_mm, h_mm) @ P[:, :3].T + P[:, 3]


def project_corners(pose: np.ndarray, cam: Camera, w_mm: float, h_mm: float) -> np.ndarray:
    pc = _camera_points(pose, w_mm, h_mm)
    return np.stack([cam.fx * pc[:, 0] / pc[:, 2] + cam.cx, cam.fy * pc[:, 1] / pc[:, 2] + cam.cy], axis=1)


def pose_valid(pose, w_mm: float, h_mm: float) -> bool:
    if pose is None:
        return False
    P = np.asarray(pose, dtype=float)
    if P.shape != (3, 4) or not np.all(np.isfinite(P)):
        return False
    return bool(np.all(_camera_points(P, w_mm, h_mm)[:, 2] > 0))


def corner_error_px(pose, gt_corners, cam: Camera, w_mm: float, h_mm: float) -> float:
    gt = np.asarray(gt_corners, dtype=float).reshape(4, 2)
    return float(np.mean(np.linalg.norm(project_corners(pose, cam, w_mm, h_mm) - gt, axis=1)))


def pose_error(pose_est, pose_gt, w_mm: float, h_mm: float) -> tuple[float, float]:
    E, G = np.asarray(pose_est, dtype=float), np.asarray(pose_gt, dtype=float)
    c = np.array([w_mm / 2, h_mm / 2, 0.0])
    t_mm = float(np.linalg.norm((E[:, :3] @ c + E[:, 3]) - (G[:, :3] @ c + G[:, 3])))
    cos = (np.trace(E[:, :3].T @ G[:, :3]) - 1.0) / 2.0
    return t_mm, float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))
