#
#  license_on_edit.py
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

"""PostToolUse hook: add the project LGPL header to a source file that was just written without one.

Never fails a tool call: missing files, non-source files and unexpected input are silent no-ops.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        path = Path(payload["tool_input"]["file_path"])
        if not path.is_absolute():
            path = Path(payload.get("cwd") or ROOT) / path
        from license_headers import fix_file
        fix_file(path)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
