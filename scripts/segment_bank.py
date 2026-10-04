#
#  segment_bank.py
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

"""Segment poster corners in a real-video bank: python scripts/segment_bank.py --bank banks/pinball-bench"""
import argparse

from nftbench.segment import segment_bank

ap = argparse.ArgumentParser()
ap.add_argument("--bank", required=True)
ap.add_argument("--video", help="colour source video of the bank (recommended)")
ap.add_argument("--min-conf", type=float, default=0.5)
a = ap.parse_args()
segment_bank(a.bank, video=a.video, min_conf=a.min_conf)
