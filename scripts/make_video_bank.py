#
#  make_video_bank.py
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

"""Build a real-video frame bank: python scripts/make_video_bank.py --video ... --out banks/x --marker-image ... --dpi 220 --dataset ..."""
import argparse

from nftbench.video_bank import make_bank

ap = argparse.ArgumentParser()
ap.add_argument("--video", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--marker-image", required=True, help="path to the marker image (its pixel size gives the size in mm)")
ap.add_argument("--dpi", type=float, required=True)
ap.add_argument("--dataset", required=True, help="marker dataset directory name, e.g. pinball-d220-l2-i1")
ap.add_argument("--fovy", type=float, default=45.0)
a = ap.parse_args()
print(make_bank(a.video, a.out, a.marker_image, a.dpi, a.dataset, a.fovy))
