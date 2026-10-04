#!/bin/bash
#
#  make_marker.sh
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

# Generate an NFT dataset reproducibly with the upstream genTexData tool.
#   scripts/make_marker.sh <jpg> <dpi> <min_dpi> <max_dpi> <level> <leveli> <outdir>
set -euo pipefail
[ $# -eq 7 ] || { echo "usage: $0 <jpg> <dpi> <min_dpi> <max_dpi> <level> <leveli> <outdir>" >&2; exit 2; }
jpg=$1 dpi=$2 mindpi=$3 maxdpi=$4 level=$5 leveli=$6 out=$7
root=$(cd "$(dirname "$0")/.." && pwd)
gen="$root/build/win-vs2022/Release/genTexData.exe"
[ -x "$gen" ] || gen="$root/build/genTexData"
mkdir -p "$out"
cp "$jpg" "$out/"
cd "$out"
"$gen" "$(basename "$jpg")" -dpi="$dpi" -min_dpi="$mindpi" -max_dpi="$maxdpi" -level="$level" -leveli="$leveli" < /dev/null \
    > genTexData.log 2>&1
ls "${jpg##*/}" >/dev/null && echo "dataset written to $out (log: genTexData.log, not committed)"
