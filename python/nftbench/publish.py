#
#  publish.py
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

"""Publishing results (ADR-0001): sensitive-data scan, log scrubbing and manifest entries.

The orchestration (archive, commit to the results repository, optional release) lives in scripts/publish_results.py;
the checks here are pure functions so they can be tested.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

_PATTERNS = [
    ("absolute path", re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]")),
    ("absolute path", re.compile(r"(?:^|[\s\"'=(])/(?:home|Users|root|mnt)/[^\s\"']+")),
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b")),
    ("IP address", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("MAC address", re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b")),
]


def scan_text(text: str, user: str, host: str) -> list[tuple[int, str]]:
    """Return (line number, reason) for every forbidden item found. Empty list means publishable."""
    hits = []
    words = [("user name", user), ("host name", host)]
    for n, line in enumerate(text.splitlines(), start=1):
        for reason, pat in _PATTERNS:
            if pat.search(line):
                hits.append((n, reason))
        low = line.lower()
        for reason, word in words:
            if word and len(word) >= 3 and re.search(rf"(?<![A-Za-z0-9]){re.escape(word.lower())}(?![A-Za-z0-9])", low):
                hits.append((n, reason))
    return hits


def scrub_text(text: str, repo_root: Path) -> str:
    """Replace absolute paths inside the repository with `<repo>`-relative ones, using forward slashes."""
    root = str(Path(repo_root)).replace("\\", "/").rstrip("/")
    variants = {root, root.replace("/", "\\")}
    out = text
    for v in sorted(variants, key=len, reverse=True):
        out = re.sub(re.escape(v) + r"([\\/][^\s\"']*)?",
                     lambda m: "<repo>" + (m.group(1) or "").replace("\\", "/"), out, flags=re.IGNORECASE)
    return out


def manifest_entry(name: str, archive: bytes, code_commit: str, results_commit: str, release_tag: str | None) -> dict:
    return {"name": name, "sha256": hashlib.sha256(archive).hexdigest(), "size": len(archive),
            "code_commit": code_commit, "results_commit": results_commit, "release_tag": release_tag}


def release_commands(results_repo: str, name: str, archive_relpath: str, results_commit: str) -> list[list[str]]:
    """Commands (run inside the local clone of the results repository) that create the optional immutable release.

    The release lives in the results repository, next to the data (see ADR-0001, "To revisit"): an annotated tag `<name>`
    on the commit that stores the archive, then a GitHub Release on that tag with the archive attached.
    """
    return [
        ["git", "tag", "-a", name, results_commit, "-m", f"{name} raw results"],
        ["git", "push", "origin", name],
        ["gh", "release", "create", name, archive_relpath, "--repo", results_repo, "--verify-tag",
         "--title", f"{name} raw results", "--notes", "SHA-256 of the archive: see results/manifest.json in "
         "webarkit/artoolkit-nft-bench."],
    ]


START, END = "<!-- publications:start -->", "<!-- publications:end -->"


def add_publication_row(readme: str, name: str, milestone: str, code_release: str | None, sha256: str,
                        data_release: str | None) -> str:
    """Append one row to the publications table of the results repository README (between the two markers)."""
    if START not in readme or END not in readme:
        raise ValueError("README has no publications table markers")
    head, rest = readme.split(START, 1)
    table, tail = rest.split(END, 1)
    if any(line.startswith(f"| {name} |") for line in table.splitlines()):
        raise ValueError(f"publication {name} already listed")
    row = f"| {name} | {milestone} | {code_release or '-'} | `{sha256}` | {data_release or '-'} |\n"
    return head + START + table.rstrip("\n") + "\n" + row + END + tail
