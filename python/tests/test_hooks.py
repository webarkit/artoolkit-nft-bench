#
#  test_hooks.py
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

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / ".claude/hooks/guard_extern.py"
HEADER = ROOT / ".claude/hooks/license_on_edit.py"


def run(script, payload):
    return subprocess.run([sys.executable, str(script)], input=json.dumps(payload), capture_output=True, text=True,
                          cwd=ROOT)


def edit(path, tool="Edit"):
    return {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": {"file_path": str(path)}, "cwd": str(ROOT)}


def test_guard_blocks_edits_inside_the_submodule():
    p = run(GUARD, edit(ROOT / "extern/artoolkit5/lib/SRC/KPM/kpmHandle.cpp"))
    assert p.returncode == 2 and "extern/artoolkit5" in p.stderr and "CMake" in p.stderr


def test_guard_blocks_relative_and_write_paths():
    assert run(GUARD, edit("extern/artoolkit5/README.md", tool="Write")).returncode == 2


def test_guard_allows_edits_elsewhere():
    assert run(GUARD, edit(ROOT / "native/src/engine.cpp")).returncode == 0


def test_guard_never_fails_on_malformed_input():
    p = subprocess.run([sys.executable, str(GUARD)], input="not json", capture_output=True, text=True, cwd=ROOT)
    assert p.returncode == 0


def test_header_hook_adds_header_to_a_new_source_file(tmp_path):
    f = ROOT / "python" / "nftbench" / "_hook_probe.py"
    try:
        f.write_text('"""probe"""\n', encoding="utf-8")
        p = run(HEADER, {"hook_event_name": "PostToolUse", "tool_name": "Write", "tool_input": {"file_path": str(f)}})
        assert p.returncode == 0
        text = f.read_text(encoding="utf-8")
        assert "SPDX-License-Identifier: LGPL-3.0-or-later" in text and "_hook_probe.py" in text and text.endswith('"""probe"""\n')
    finally:
        f.unlink(missing_ok=True)


def test_header_hook_ignores_non_sources_and_missing_files():
    md = run(HEADER, {"tool_name": "Write", "tool_input": {"file_path": str(ROOT / "README.md")}})
    gone = run(HEADER, {"tool_name": "Write", "tool_input": {"file_path": str(ROOT / "nope/missing.py")}})
    assert md.returncode == 0 and gone.returncode == 0
