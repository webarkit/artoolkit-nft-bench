#
#  check_recording.py
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

"""Checks before adding a recording session (docs/recording-guide.md).

    python scripts/check_recording.py dpi --mm 128 159            # measured print size -> dpi and make_marker command
    python scripts/check_recording.py videos data/videos/tab9-2026-10-05 [--size 1280x720 --fps 30]
    python scripts/check_recording.py quality data/videos/tab9-2026-10-05 [--marker data/markers/pinball-d326-l2-i1/pinball --dpi 326]
"""
import argparse
import sys
from pathlib import Path

from nftbench.quality import check_chessboard_clip, check_photo, check_poster_clip, clip_kind, render_summary
from nftbench.recording import check_video, container_tags, print_dpi, sensitive_tags

ap = argparse.ArgumentParser()
sub = ap.add_subparsers(dest="cmd", required=True)
d = sub.add_parser("dpi", help="effective dpi of a printed marker")
d.add_argument("--px", type=int, nargs=2, default=[1637, 2048], metavar=("W", "H"), help="marker image size in pixels")
d.add_argument("--mm", type=float, nargs=2, required=True, metavar=("W", "H"), help="measured printed size in mm")
v = sub.add_parser("videos", help="format and metadata of every clip in a directory")
v.add_argument("dir", type=Path)
v.add_argument("--size", default="1280x720")
v.add_argument("--fps", type=float, default=30.0)
q = sub.add_parser("quality", help="is each clip usable? marker visible and sharp, chessboard coverage")
q.add_argument("dir", type=Path)
q.add_argument("--marker", help="NFT dataset path without extension, to also check KPM detection (needs the native build)")
q.add_argument("--dpi", type=float, help="dpi of that dataset")
q.add_argument("--out", type=Path, default=Path("results/local/recording-check"), help="summary images")
a = ap.parse_args()

if a.cmd == "quality":
    bad = 0
    for p in sorted(a.dir.iterdir()):
        kind = clip_kind(p.name)
        if kind is None or kind == "photo" and p.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        if kind == "photo":
            r = check_photo(p)
            print(f"{r['status']:5} {p.name}: photo, sharpness {r['sharpness']:.0f}")
        elif kind == "chessboard":
            r = check_chessboard_clip(p)
            print(f"{r['status']:5} {p.name}: found {r['found']}, cells {r['cells_covered']}/9, tilted {r['tilted_frac']:.0%}  "
                  f"-> {render_summary(r, a.out)}")
        else:
            r = check_poster_clip(p, kind, a.marker, a.dpi)
            kpm = f", KPM {r['kpm_hits']}/10" if r["kpm_checked"] else ", KPM not checked (pass --marker/--dpi)"
            print(f"{r['status']:5} {p.name}: ground truth {r['gt_frac']:.0%}, sharp {r['sharp_frac']:.0%}{kpm}  "
                  f"-> {render_summary(r, a.out)}")
        for reason in r["reasons"]:
            print(f"      - {reason}")
        bad += r["status"] != "ok"
    sys.exit(1 if bad else 0)

if a.cmd == "dpi":
    r = print_dpi(*a.px, *a.mm)
    print(f"dpi from width {r['dpi_w']:.1f}, from height {r['dpi_h']:.1f} -> {r['dpi']} dpi")
    if not r["consistent"]:
        print("the two measurements disagree by more than 2%: re-measure (the image area only, no margins)", file=sys.stderr)
        sys.exit(1)
    print(f"marker directory: data/markers/{r['marker_dir']}\n{r['command']}")
    sys.exit(0)

w, h = (int(x) for x in a.size.lower().split("x"))
bad = 0
for p in sorted(a.dir.iterdir()):
    if p.suffix.lower() not in {".mp4", ".mov", ".mkv"}:
        continue
    r = check_video(p, (w, h), a.fps)
    personal = sensitive_tags(container_tags(p))
    issues = r["issues"] + [f"personal metadata: {', '.join(personal)} (strip it: ffmpeg -i in -map_metadata -1 -c copy out)"] * bool(personal)
    status = "ok" if not issues else "CHECK"
    print(f"{status:5} {p.name}: {r.get('width')}x{r.get('height')} {r.get('fps', 0):.2f} fps, {r.get('frames')} frames, "
          f"{r.get('duration_s', 0):.1f} s")
    for i in issues:
        print(f"      - {i}")
    bad += bool(issues)
sys.exit(1 if bad else 0)
