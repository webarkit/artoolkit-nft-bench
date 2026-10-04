#
#  test_publish.py
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

from pathlib import Path

from nftbench.publish import manifest_entry, scan_text, scrub_text

USER, HOST = "alice", "WORKSTATION-7"


def reasons(text):
    return {r for _, r in scan_text(text, USER, HOST)}


def test_scan_flags_absolute_windows_path():
    assert "absolute path" in reasons(r'{"log": "C:\Users\x\file.txt"}')
    assert "absolute path" in reasons("D:/kalwalt-github/repo/banks")


def test_scan_flags_posix_home_path():
    assert "absolute path" in reasons("/home/bob/work/out.json")


def test_scan_flags_username_and_hostname():
    assert "user name" in reasons("built by alice yesterday")
    assert "host name" in reasons("machine workstation-7 ran it")


def test_scan_flags_email_token_ip_mac():
    r = reasons("mail me@example.org token gho_abcdefghijklmnopqrstuvwxyz0123 ip 192.168.1.20 mac 00:1A:2B:3C:4D:5E")
    assert {"email", "token", "IP address", "MAC address"} <= r


def test_scan_accepts_clean_result_header():
    clean = '{"host": {"host_label": "desktop-1", "os": "Windows build 26200", "cpu": "Intel(R) Core(TM) i7-9700"}, "t": 1.5}'
    assert scan_text(clean, USER, HOST) == []


def test_scan_reports_line_numbers():
    hits = scan_text("ok\nok\nsee /home/bob/x\n", USER, HOST)
    assert hits and hits[0][0] == 3


def test_scrub_rewrites_repo_paths_relative():
    root = Path("D:/work/artoolkit-nft-bench")
    s = scrub_text(r"loading D:\work\artoolkit-nft-bench\data\markers\x and D:/work/artoolkit-nft-bench/banks/y", root)
    assert s == "loading <repo>/data/markers/x and <repo>/banks/y"


def test_manifest_entry_fields():
    e = manifest_entry("phase-1", b"abc", "1234567", "89abcde", "results/phase-1")
    assert e == {"name": "phase-1", "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
                 "size": 3, "code_commit": "1234567", "results_commit": "89abcde", "release_tag": "results/phase-1"}
