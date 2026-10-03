# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright 2026 webarkit contributors. Part of artoolkit-nft-bench.
"""Score result files against a frame bank and print markdown tables.

    python -m nftbench.score --bank banks/x --result a.json [--result b.json.gz] [--ok-px 5] [--md out.md]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .metrics import summarize
from .schema import IncompatibleResult, check_compatible, load_bank, load_result


def _f(v, fmt="{:.2f}"):
    return "-" if v is None else fmt.format(v)


def _label(h: dict) -> str:
    return f"{h.get('engine', '?')} threads={h.get('params', {}).get('threads', '?')}"


def render(bank, scored: list, ok_px: float) -> str:
    out = [f"# {bank.name} ({bank.kind}, {bank.width}x{bank.height}, marker {bank.marker_dataset} @ {bank.marker_dpi:g} dpi)",
           "", f"ok = valid pose with mean corner error < {ok_px:g} px.", ""]
    for h, s in scored:
        out += [f"## {_label(h)} — track share {100 * s['track_share']:.1f}%, "
                f"trackTimeShare {100 * s['track_time_share']:.1f}%", "",
                "| group | n | excl | valid% | ok% | med px | p90 px | med mm | med deg | lost | 1st lock | jitter px "
                "| det ms p50/p95 | trk ms p50/p95 | total ms p50/p95/max |",
                "|" + "---|" * 15]
        for g, m in sorted(s["groups"].items()):
            d, t, tt = m["t_detect_ms"], m["t_track_ms"], m["t_total_ms"]
            out.append(
                f"| {g} | {m['n']} | {m['n_excluded']} | {_f(m['valid_pct'], '{:.0f}')} | {_f(m['ok_pct'], '{:.0f}')} "
                f"| {_f(m['median_px'])} | {_f(m['p90_px'])} | {_f(m['median_mm'])} | {_f(m['median_deg'])} "
                f"| {m['lost_events']} | {_f(m['first_lock_frame'], '{}')} | {_f(m['jitter_px'])} "
                f"| {_f(d['p50'], '{:.1f}')}/{_f(d['p95'], '{:.1f}')} | {_f(t['p50'], '{:.1f}')}/{_f(t['p95'], '{:.1f}')} "
                f"| {_f(tt['p50'], '{:.1f}')}/{_f(tt['p95'], '{:.1f}')}/{_f(tt['max'], '{:.1f}')} |")
        out.append("")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="nftbench.score")
    ap.add_argument("--bank", required=True, type=Path)
    ap.add_argument("--result", required=True, action="append", type=Path)
    ap.add_argument("--ok-px", type=float, default=5.0)
    ap.add_argument("--md", type=Path)
    a = ap.parse_args(argv)
    bank = load_bank(a.bank)
    scored = []
    for rp in a.result:
        r = load_result(rp)
        try:
            check_compatible(bank, r)
        except IncompatibleResult as e:
            print(f"error: {rp}: {e}", file=sys.stderr)
            return 2
        scored.append((r.header, summarize(bank, r, a.ok_px)))
    text = render(bank, scored, a.ok_px)
    print(text)
    if a.md:
        a.md.parent.mkdir(parents=True, exist_ok=True)
        a.md.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
