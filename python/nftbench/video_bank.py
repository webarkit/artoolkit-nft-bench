#
#  video_bank.py
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

"""Build a frame bank from a real video: grey PNG frames + bank.json, without ground truth (see segment.py)."""
from __future__ import annotations

import json
import math
from pathlib import Path

import cv2


def make_bank(video: Path, out_dir: Path, marker_image: str, marker_dpi: float, marker_dataset: str,
              fovy_deg: float = 45.0, marker_px: tuple[int, int] | None = None, name: str | None = None) -> Path:
    """Decode every frame of `video` into `out_dir` and return the bank directory.

    Timestamps come from the container (CAP_PROP_POS_MSEC), not from the frame index, because clips can have a
    variable or non-integer frame rate. `marker_px` is the marker image size in pixels; if omitted it is read from
    `marker_image`, which must then be a readable path.
    """
    out_dir = Path(out_dir)
    (out_dir / "frames").mkdir(parents=True, exist_ok=True)
    if marker_px is None:
        img = cv2.imread(str(marker_image), cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise FileNotFoundError(marker_image)
        marker_px = (img.shape[1], img.shape[0])
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise FileNotFoundError(video)
    frames, w, h, k = [], 0, 0, 0
    while True:
        ok, bgr = cap.read()
        if not ok:
            break
        t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        grey = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        h, w = grey.shape
        fn = f"frames/{k:06d}.png"
        cv2.imwrite(str(out_dir / fn), grey)
        frames.append({"seq": 0, "i": k, "file": fn, "t": t, "group": "real", "gt_pose": None, "gt_corners": None})
        k += 1
    cap.release()
    f = h / 2.0 / math.tan(math.radians(fovy_deg) / 2.0)
    doc = {"schema": 1, "kind": "real", "name": name or Path(video).stem, "width": w, "height": h,
           "camera": {"fx": f, "fy": f, "cx": w / 2.0, "cy": h / 2.0},
           "marker": {"image": Path(marker_image).name, "dataset": marker_dataset, "dpi": marker_dpi,
                      "width_mm": marker_px[0] / marker_dpi * 25.4, "height_mm": marker_px[1] / marker_dpi * 25.4},
           "source": {"video": Path(video).name, "fovy_deg": fovy_deg},
           "frames": frames}
    (out_dir / "bank.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")
    return out_dir
