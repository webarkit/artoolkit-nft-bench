#!/bin/bash
#
#  docker_build.sh
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

set -euo pipefail
# Runs inside an ubuntu:24.04 container: /src is the repository (read-only); the same steps as the CI linux job.
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq >/dev/null
apt-get install -y -qq build-essential cmake ninja-build libjpeg-dev zlib1g-dev python3-venv git >/dev/null
mkdir -p /work && cd /src && tar --exclude=./build --exclude=./.venv --exclude=./banks --exclude=./results/local -cf - . | tar -xf - -C /work
cd /work && git config --global --add safe.directory '*'
cmake --preset linux-gcc 2>&1 | tail -2
cmake --build --preset linux-gcc 2>&1 | grep -E "error|warning: implicit|FAILED" | head -20 || true
ctest --preset linux-gcc 2>&1 | tail -3
python3 -m venv .venv && .venv/bin/pip install -q -r requirements-dev.txt && .venv/bin/pip install -q --no-build-isolation -e .
.venv/bin/python -m pytest -q 2>&1 | tail -5
gcc --version | head -1
