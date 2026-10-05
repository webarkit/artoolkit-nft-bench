#
#  guard_extern.py
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

"""PreToolUse hook: refuse any edit inside extern/ (pinned upstream submodules are never modified).

Reads the hook payload on stdin. Exit code 2 blocks the tool call and shows stderr to the agent. Any unexpected input
exits 0, so the hook never breaks an unrelated tool call.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        path = Path(payload.get("tool_input", {}).get("file_path") or payload.get("tool_input", {}).get("notebook_path"))
    except Exception:
        return 0
    if not path.is_absolute():
        path = Path(payload.get("cwd") or ROOT) / path
    try:
        rel = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return 0
    if rel.startswith("extern/"):
        print(f"Blocked: {rel} is inside a pinned upstream submodule (extern/artoolkit5), which is never modified. "
              "Fix portability problems in this repository's CMake (CMakeLists.txt, cmake/, native/CMakeLists.txt) instead.",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
