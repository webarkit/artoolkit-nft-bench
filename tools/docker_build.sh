#!/bin/bash
# Runs inside the container: /src is the (read-only) repo, /out receives results.
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq >/dev/null
apt-get install -y -qq build-essential cmake ninja-build libjpeg-dev zlib1g-dev >/dev/null
cmake -S /src -B /build -G Ninja -DCMAKE_BUILD_TYPE=Release -DARX_FETCH_DEPS=OFF 2>&1 | tail -3
cmake --build /build -j 8 2>&1 | grep -E "error|warning: implicit|FAILED|Linking" | head -20
gcc --version | head -1

# --- 1. regenerate the NFT dataset on Linux and compare with the Windows-generated one -------------
mkdir -p /tmp/gen && cp /src/data/markers/pinball.jpg /tmp/gen/ && cd /tmp/gen
/build/genTexData pinball.jpg -dpi=150 -min_dpi=30 -max_dpi=150 -level=2 -leveli=3 < /dev/null > /out/gentex.log 2>&1
echo "== dataset md5 (linux-generated vs windows-generated)"
for e in iset fset fset3; do
    printf "%s linux=%s windows=%s\n" "$e" "$(md5sum /tmp/gen/pinball.$e | cut -c1-12)" "$(md5sum /src/data/markers/pinball.$e | cut -c1-12)"
done
# --- 2. quality suite on the *Windows-generated* dataset (cross-platform dataset compatibility) -----
/build/tests/nft_eval dataset=/src/data/markers/pinball image=/src/data/markers/pinball.jpg dpi=150 mode=all trials=10 \
    csv=/out/pinball_full.csv > /out/pinball_full.txt 2>&1
echo "== done"
