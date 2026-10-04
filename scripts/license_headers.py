#
#  license_headers.py
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
"""Check (default) or add (--fix) the project LGPL header, the same template as webarkit/webarkit."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SUFFIXES = {".cpp", ".hpp", ".c", ".h", ".py", ".sh", ".cmake", ".mjs", ".js", ".ts"}
SOURCE_NAMES = {"CMakeLists.txt"}
EXCLUDE_PREFIXES = ("extern/",)

BODY = """{name}
artoolkit-nft-bench

This file is part of artoolkit-nft-bench.

SPDX-License-Identifier: LGPL-3.0-or-later

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Copyright 2026 WebARKit.

Author(s): Walter Perdan @kalwalt https://github.com/kalwalt
"""


def header(path: Path) -> str:
    lines = BODY.format(name=path.name).splitlines()
    if path.suffix in {".cpp", ".hpp", ".c", ".h", ".mjs", ".js", ".ts"}:
        return "/*\n" + "".join(f" *  {l}".rstrip() + "\n" for l in lines) + " *\n */\n"
    return "#\n" + "".join(f"#  {l}".rstrip() + "\n" for l in lines) + "#\n"


def source_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout.split()
    return [ROOT / p for p in out if not p.startswith(EXCLUDE_PREFIXES)
            and (Path(p).suffix in SOURCE_SUFFIXES or Path(p).name in SOURCE_NAMES) and (ROOT / p).exists()]


def has_header(text: str) -> bool:
    head = "\n".join(text.splitlines()[:30])
    return "SPDX-License-Identifier: LGPL-3.0-or-later" in head and "Copyright 2026 WebARKit." in head


def strip_old(text: str) -> str:
    # Remove a short SPDX-only preamble written before the template existed.
    lines = text.splitlines(keepends=True)
    while lines and ("SPDX-License-Identifier" in lines[0] or "Part of artoolkit-nft-bench" in lines[0]):
        lines.pop(0)
    return "".join(lines)


def is_source(path: Path) -> bool:
    try:
        rel = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return False
    return not rel.startswith(EXCLUDE_PREFIXES) and (path.suffix in SOURCE_SUFFIXES or path.name in SOURCE_NAMES)


def fix_file(p: Path) -> bool:
    """Add the header to one file if it is a source without one. Returns True if the file was changed."""
    if not p.is_file() or not is_source(p):
        return False
    text = p.read_text(encoding="utf-8")
    if has_header(text):
        return False
    body = strip_old(text)
    shebang = ""
    if body.startswith("#!"):
        shebang, body = body.split("\n", 1)
        shebang += "\n"
    p.write_text(shebang + header(p) + ("\n" if body and not body.startswith("\n") else "") + body, encoding="utf-8")
    return True


def main(argv: list[str]) -> int:
    fix = "--fix" in argv
    missing = []
    for p in source_files():
        text = p.read_text(encoding="utf-8")
        if has_header(text):
            continue
        if not fix:
            missing.append(p.relative_to(ROOT).as_posix())
            continue
        fix_file(p)
    for m in missing:
        print(f"missing license header: {m}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
