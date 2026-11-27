#!/bin/bash
#
#  encode_session.sh
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

# Make a recording session's committed clips from the camera originals (docs/recording-guide.md).
#
#   scripts/encode_session.sh [--force] <originals_dir> <out_dir> <name>=<original>:<crf> [...]
#
# Every spec is checked before the first encode: <name> must be a file name (no '/', '\' or '..'), unique among the outputs,
# not an input, and not an existing file unless --force is given. A refusal names the spec and encodes nothing.
#
# Example (the Tab 9 session of 2026-11-26, see data/videos/tab9-2026-11-26/README.md):
#
#   scripts/encode_session.sh ../media-originals/tab9-2026-11-26 data/videos/tab9-2026-11-26 \
#       fast.mp4=VID_20261126_230851.mp4:18 static-tripod.mp4=VID_20261126_231929.mp4:18 \
#       calib-chessboard.mp4=VID_20261126_232056.mp4:22
#
# Each clip: video only (the audio is dropped), all container and stream metadata removed, H.264 (libx264, preset slow, the
# given CRF), yuv420p at 1280x720, moov atom first. Frames are neither dropped, duplicated nor retimed: every frame keeps
# its original timestamp (-copyts, -fps_mode passthrough, the encoder on the demuxer's clock and the camera files' 90 kHz
# track timescale; without these ffmpeg re-quantises timestamps to 1/30 s and shifts the first one to zero).
# Colour: the Tab 9 files contradict themselves (the MP4 'colr' atom says full range, BT.601; the H.264 VUI says limited
# range, BT.709) and decoders, OpenCV included, follow the VUI. The output declares limited range and BT.709 in both places,
# so it decodes to the same colours as the original.
# The originals are never modified; the script prints the SHA-256 of every input and output.
set -euo pipefail
force=0
if [ "${1:-}" = --force ]; then force=1; shift; fi
[ $# -ge 3 ] || { echo "usage: $0 [--force] <originals_dir> <out_dir> <name>=<original>:<crf> [...]" >&2; exit 2; }
src=$1 out=$2
shift 2
refuse() { echo "refused: $1: $2" >&2; exit 2; }
# Validate every spec before the first encode.
names=() inputs=()
for spec in "$@"; do
    name=${spec%%=*} rest=${spec#*=}
    orig=${rest%:*} crf=${rest##*:}
    [ "$name" != "$spec" ] && [ "$orig" != "$rest" ] && [ -n "$name" ] && [[ $crf =~ ^[0-9]+$ ]] || refuse "$spec" "bad clip spec"
    case $name in */* | *\\* | *..* | . ) refuse "$spec" "the output name must be a file name, without '/', '\\' or '..'" ;; esac
    [ -f "$src/$orig" ] || { echo "missing original: $src/$orig ($spec)" >&2; exit 1; }
    for n in ${names[@]+"${names[@]}"}; do
        [ "$n" != "$name" ] || refuse "$spec" "output name '$name' given twice"
    done
    names+=("$name")
    inputs+=("$(realpath -m -- "$src/$orig")")
done
for spec in "$@"; do
    name=${spec%%=*}
    dest=$(realpath -m -- "$out/$name")
    for i in "${inputs[@]}"; do
        [ "$dest" != "$i" ] || refuse "$spec" "output $out/$name is an input"
    done
    [ "$force" = 1 ] || [ ! -e "$out/$name" ] || refuse "$spec" "output $out/$name exists (pass --force to overwrite)"
done
mkdir -p "$out"
for spec in "$@"; do
    name=${spec%%=*} rest=${spec#*=}
    orig=${rest%:*} crf=${rest##*:}
    in="$src/$orig"
    ffmpeg -hide_banner -loglevel error -nostdin -y -copyts -i "$in" \
        -map 0:v:0 -an -sn -dn -map_metadata -1 -map_chapters -1 -fflags +bitexact -flags:v +bitexact \
        -vf "scale=1280:720,format=yuv420p,setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709" \
        -c:v libx264 -preset slow -crf "$crf" \
        -fps_mode passthrough -enc_time_base:v demux -video_track_timescale 90000 \
        -movflags +faststart \
        "$out/$name"
    echo "$name <- $orig (crf $crf): $(wc -c < "$out/$name") bytes"
    echo "  in  $(sha256sum "$in" | cut -d' ' -f1)"
    echo "  out $(sha256sum "$out/$name" | cut -d' ' -f1)"
done
