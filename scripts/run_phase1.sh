#!/bin/bash
#
#  run_phase1.sh
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

# Phase 1: native results at 220 dpi on the synthetic and the real bank. Raw results go to results/local/phase1/.
set -euo pipefail
cd "$(dirname "$0")/.."
B=build/win-vs2022/native/Release
PY=.venv/Scripts/python
DS=data/markers/pinball-d220-l2-i1
OUT=results/local/phase1
REPEATS=${REPEATS:-5}
mkdir -p "$OUT"
[ -f "$DS/pinball.fset3" ] || scripts/make_marker.sh data/markers/pinball.jpg 220 30 220 2 1 "$DS"
[ -f banks/synthetic-d220/bank.json ] || "$B/nft_export.exe" out=banks/synthetic-d220 image=data/markers/pinball.jpg dpi=220 \
    dataset=pinball-d220-l2-i1 trials=10 seqs=3 seqlen=90 speeds=0,2,5,10,20,35 name=synthetic-d220
if [ ! -f banks/pinball-bench/bank.json ]; then
    $PY scripts/make_video_bank.py --video data/videos/pinball-bench.mp4 --out banks/pinball-bench \
        --marker-image data/markers/pinball.jpg --dpi 220 --dataset pinball-d220-l2-i1
    $PY scripts/segment_bank.py --bank banks/pinball-bench --video data/videos/pinball-bench.mp4
fi
for bank in synthetic-d220 pinball-bench; do
    for t in 1 -1; do
        tag=$([ "$t" = 1 ] && echo t1 || echo tN)
        "$B/nft_run.exe" bank=banks/$bank dataset=$DS/pinball dpi=220 threads=$t repeats=$REPEATS out=$OUT/native-$bank-$tag.json
        echo "done $bank $tag"
    done
done
