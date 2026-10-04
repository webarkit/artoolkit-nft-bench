#
#  metrics.py
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

"""Metrics computed from a bank (ground truth) and a result (engine output). See the spec, section 5."""
from __future__ import annotations

from collections import defaultdict

import numpy as np

from .geometry import corner_error_px, pose_error, pose_valid, project_corners
from .schema import Bank, Result

VALID_STATES = ("detected", "tracked")


def _pct(v: list[float]) -> dict:
    if not v:
        return {"p50": None, "p95": None, "max": None}
    a = np.asarray(v, dtype=float)
    return {"p50": float(np.percentile(a, 50)), "p95": float(np.percentile(a, 95)), "max": float(a.max())}


def _q(v: list[float], q: float):
    return float(np.percentile(np.asarray(v, dtype=float), q)) if v else None


def track_time_share(states: list[list[str]], times: list[list[float]], bin_ms: float = 10.0) -> float:
    """Share of time spent tracking, as in webarkit/webarkit benchmarks.

    Each sequence is a stretch. Bins of bin_ms are laid from the stretch's first frame time up to (not including) its
    last frame time; each bin takes the state of the most recent frame at or before the bin start. Bins are pooled.
    """
    tracked = total = 0
    for st, ts in zip(states, times):
        if len(st) < 2:
            continue
        ms = [round(t * 1000.0, 6) for t in ts]
        end, k, nbin = ms[-1], 0, 0
        while True:
            b = ms[0] + nbin * bin_ms
            if b >= end - 1e-9:
                break
            while k + 1 < len(ms) and ms[k + 1] <= b + 1e-9:
                k += 1
            total += 1
            tracked += st[k] == "tracked"
            nbin += 1
    return tracked / total if total else 0.0


def jitter_px(corners_seq: np.ndarray) -> float:
    """RMS of the second difference of projected corners over consecutive frames, shape (n, 4, 2)."""
    c = np.asarray(corners_seq, dtype=float)
    if len(c) < 3:
        return 0.0
    d2 = c[2:] - 2 * c[1:-1] + c[:-2]
    return float(np.sqrt(np.mean(np.sum(d2 ** 2, axis=-1))))


def _gt_corners(f, cam, w, h):
    if f.gt_corners is not None:
        return f.gt_corners
    if f.gt_pose is not None:
        return project_corners(f.gt_pose, cam, w, h)
    return None


def summarize(bank: Bank, result: Result, ok_px: float = 5.0, gt_margin_mm: float = 0.0) -> dict:
    """Per-group metrics. Error percentiles cover every valid frame; `ok` is the share below `ok_px`.

    gt_margin_mm: width of a print border around the marker image, applied only to segmented corner ground truth.
    Bank frames with no result frame count as lost (`n_missing`); a result frame not in the bank is an error.
    """
    from .schema import IncompatibleResult, ResultFrame
    gt = {(f.seq, f.i): f for f in bank.frames}
    W, H, cam = bank.marker_w_mm, bank.marker_h_mm, bank.camera
    got = {}
    for r in result.frames:
        if (r.seq, r.i) not in gt:
            raise IncompatibleResult(f"result frame seq={r.seq} i={r.i} is not in bank {bank.name}")
        got[(r.seq, r.i)] = r
    by_group = defaultdict(lambda: defaultdict(list))
    missing = defaultdict(int)
    for key, f in gt.items():
        r = got.get(key)
        if r is None:
            missing[f.group] += 1
            r = ResultFrame(f.seq, f.i, "lost", None, None, None, 0.0, 0.0)
        by_group[f.group][f.seq].append(r)

    groups, all_states, all_times = {}, [], []
    for name, seqs in by_group.items():
        n = excl = valid = ok = lost_events = 0
        px, mm, deg, jit, t_det, t_trk, t_tot, blocked, locks = [], [], [], [], [], [], [], [], []
        for seq_frames in seqs.values():
            seq_frames.sort(key=lambda r: r.i)
            i0 = seq_frames[0].i
            prev_valid, run, states, times, lock = False, [], [], [], None
            for r in seq_frames:
                f = gt[(r.seq, r.i)]
                ok_pose = r.state in VALID_STATES and pose_valid(r.pose, W, H)
                state = r.state if ok_pose else "lost"
                states.append(state)
                times.append(f.t)
                if prev_valid and not ok_pose:
                    lost_events += 1
                if ok_pose and lock is None:
                    lock = r.i - i0
                if state == "tracked":
                    run.append(project_corners(r.pose, cam, W, H))
                else:
                    if len(run) >= 3:
                        jit.append(jitter_px(np.stack(run)))
                    run = []
                prev_valid = ok_pose
                if r.t_detect_ms is not None:
                    t_det.append(r.t_detect_ms)
                if r.t_track_ms is not None:
                    t_trk.append(r.t_track_ms)
                t_tot.append(r.t_total_ms)
                blocked.append(r.blocked_ms)
                gc = _gt_corners(f, cam, W, H)
                if gc is None:
                    excl += 1
                    continue
                n += 1
                if not ok_pose:
                    continue
                valid += 1
                margin = gt_margin_mm if f.gt_corners is not None else 0.0
                e = corner_error_px(r.pose, gc, cam, W, H, margin)
                px.append(e)
                ok += e < ok_px
                if f.gt_pose is not None:
                    t_mm, r_deg = pose_error(r.pose, f.gt_pose, W, H)
                    mm.append(t_mm)
                    deg.append(r_deg)
            if len(run) >= 3:
                jit.append(jitter_px(np.stack(run)))
            if lock is not None:
                locks.append(lock)
            all_states.append(states)
            all_times.append(times)
        groups[name] = {
            "n": n, "n_excluded": excl, "n_missing": missing[name],
            "valid_pct": 100.0 * valid / n if n else None, "ok_pct": 100.0 * ok / n if n else None,
            "median_px": _q(px, 50), "p90_px": _q(px, 90), "median_mm": _q(mm, 50), "median_deg": _q(deg, 50),
            "lost_events": lost_events,
            "first_lock_median": _q(locks, 50), "first_lock_max": max(locks) if locks else None,
            "jitter_px": float(np.mean(jit)) if jit else None,
            "t_detect_ms": _pct(t_det), "t_track_ms": _pct(t_trk), "t_total_ms": _pct(t_tot),
            "blocked_ms_max": max(blocked) if blocked else None,
        }
    flat = [s for st in all_states for s in st]
    return {"groups": groups,
            "track_share": flat.count("tracked") / len(flat) if flat else 0.0,
            "track_time_share": track_time_share(all_states, all_times)}


def estimate_margin_mm(bank: Bank, result: Result, max_frames: int = 50, search_mm: float = 10.0) -> tuple[float, float]:
    """Print-border width that best explains segmented corners given the engine's poses.

    Uses the first `max_frames` frames that have both a valid engine pose and segmented corners; returns
    (margin in mm, mean corner residual in px at that margin). A 1-D search is enough: the margin enters linearly.
    """
    gt = {(f.seq, f.i): f for f in bank.frames}
    W, H, cam = bank.marker_w_mm, bank.marker_h_mm, bank.camera
    pairs = []
    for r in result.frames:
        f = gt[(r.seq, r.i)]
        if f.gt_corners is not None and r.state in VALID_STATES and pose_valid(r.pose, W, H):
            pairs.append((r.pose, f.gt_corners))
            if len(pairs) >= max_frames:
                break
    if not pairs:
        return 0.0, float("nan")

    def cost(m):
        return float(np.mean([corner_error_px(p, c, cam, W, H, m) for p, c in pairs]))

    grid = np.arange(-search_mm, search_mm + 1e-9, 0.25)
    best = float(grid[int(np.argmin([cost(m) for m in grid]))])
    fine = np.arange(best - 0.25, best + 0.25 + 1e-9, 0.01)
    best = float(fine[int(np.argmin([cost(m) for m in fine]))])
    return best, cost(best)
