#
#  publish_results.py
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

"""Publish a set of results (ADR-0001).

    python scripts/publish_results.py <name> --from results/local/<dir> --results-repo <local clone of
        webarkit/artoolkit-nft-bench-results> [--release] [--dry-run]

Steps: scrub absolute repository paths from text files, scan every file for forbidden data (abort, naming file and line,
on any hit), pack <name>.tar.gz, commit it to the results repository and push, optionally attach it to an immutable release
`results/<name>` of this repository, and append the entry to results/manifest.json (commit that file yourself).
"""
import argparse
import getpass
import io
import json
import socket
import subprocess
import sys
import tarfile
from pathlib import Path

from nftbench.publish import manifest_entry, scan_text, scrub_text

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".json", ".md", ".txt", ".log", ".csv"}


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--from", dest="src", required=True, type=Path)
    ap.add_argument("--results-repo", type=Path)
    ap.add_argument("--release", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="scrub and scan only")
    a = ap.parse_args()

    files = sorted(p for p in a.src.rglob("*") if p.is_file())
    if not files:
        print(f"nothing to publish in {a.src}", file=sys.stderr)
        return 2
    user, host = getpass.getuser(), socket.gethostname()
    payload, problems = {}, []
    for p in files:
        rel = p.relative_to(a.src).as_posix()
        data = p.read_bytes()
        if p.suffix in TEXT_SUFFIXES:
            text = scrub_text(data.decode("utf-8", errors="replace"), ROOT)
            problems += [f"{rel}:{line}: {reason}" for line, reason in scan_text(text, user, host)]
            data = text.encode("utf-8")
        payload[rel] = data
    if problems:
        print("refusing to publish, forbidden data found:", file=sys.stderr)
        print("\n".join(problems), file=sys.stderr)
        return 1
    if a.dry_run:
        print(f"{len(payload)} files clean")
        return 0
    if not a.results_repo:
        print("--results-repo is required to publish", file=sys.stderr)
        return 2

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for rel, data in sorted(payload.items()):
            info = tarfile.TarInfo(f"{a.name}/{rel}")
            info.size, info.mtime = len(data), 0
            tar.addfile(info, io.BytesIO(data))
    archive = buf.getvalue()

    dest = a.results_repo / a.name / f"{a.name}.tar.gz"
    if dest.exists():
        print(f"{dest} exists; publications are never overwritten, choose a new name", file=sys.stderr)
        return 2
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(archive)
    code_commit = git("rev-parse", "--short", "HEAD", cwd=ROOT)
    git("add", str(dest.relative_to(a.results_repo)), cwd=a.results_repo)
    git("commit", "-m", f"results: publish {a.name} (code {code_commit})", cwd=a.results_repo)
    git("push", cwd=a.results_repo)
    results_commit = git("rev-parse", "--short", "HEAD", cwd=a.results_repo)

    tag = None
    if a.release:
        tag = f"results/{a.name}"
        subprocess.run(["gh", "release", "create", tag, str(dest), "--prerelease", "--target", code_commit,
                        "--title", f"Results: {a.name}", "--notes", f"Archive SHA-256 in results/manifest.json."],
                       cwd=ROOT, check=True)

    manifest = ROOT / "results" / "manifest.json"
    entries = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else []
    entries.append(manifest_entry(a.name, archive, code_commit, results_commit, tag))
    manifest.write_text(json.dumps(entries, indent=1) + "\n", encoding="utf-8")
    print(f"published {a.name}: {len(archive)} bytes, results commit {results_commit}; now commit results/manifest.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
