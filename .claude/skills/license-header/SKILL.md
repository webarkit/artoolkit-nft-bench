---
name: license-header
description: Add or check the webarkit LGPL-3.0-or-later header on source files (C/C++, Python, shell, CMake, JS/TS). Use whenever you create a new source file, rename one, or when pytest fails on test_license_headers.
---

# license-header

## Run it

```bash
.venv/Scripts/python scripts/license_headers.py          # check: lists files without the header, exit 1 if any
.venv/Scripts/python scripts/license_headers.py --fix    # add the header to every file that lacks it
```

It covers every tracked or untracked (not ignored) file with suffix `.cpp .hpp .c .h .py .sh .cmake .mjs .js .ts` and every
`CMakeLists.txt`, except `extern/` (upstream submodules keep their own headers and are never modified).
The same check runs inside `pytest` (`python/tests/test_license_headers.py`), so a missing header fails the suite.

## The template

The same one used across `webarkit/webarkit`: file name, `artoolkit-nft-bench`, `This file is part of artoolkit-nft-bench.`,
`SPDX-License-Identifier: LGPL-3.0-or-later`, the LGPL notice, `Copyright 2026 WebARKit.`,
`Author(s): Walter Perdan @kalwalt https://github.com/kalwalt`. `/* ... */` for C/C++/JS/TS, `#` lines for Python, shell and CMake.
A shebang stays on the first line. The authoritative text is `BODY` in `scripts/license_headers.py`; change it there, never by hand
in individual files.

## After a rename

The header contains the file name. `--fix` does not rewrite an existing header, so update the name line by hand after renaming.

## When not to use it

Data files (`.json`, `.png`, `.iset`/`.fset`/`.fset3`, videos), Markdown and generated build output carry no header.
