---
name: run-benchmark
description: Build frame banks, run an engine's runner and produce the result tables. Use when asked to (re)run the benchmark, reproduce a phase, measure a change in a runner or in the native build, or regenerate tables after a metric change.
---

# run-benchmark

## Whole phase 1

```bash
scripts/run_phase1.sh                      # REPEATS=5 by default; long (tens of minutes)
```

It creates, when missing: the marker `data/markers/pinball-d220-l2-i1`, the synthetic bank `banks/synthetic-d220` (2010 frames),
the real-clip bank `banks/pinball-bench` with segmented corners; then runs `nft_run` at `threads=1` and `threads=-1`.
Raw results go to `results/local/phase1/` (git-ignored). Run it in the background and redirect output to a log.

## Single steps

```bash
B=build/win-vs2022/native/Release
$B/nft_export.exe out=banks/<name> image=data/markers/pinball.jpg dpi=220 dataset=pinball-d220-l2-i1 [trials= mode= scenarios= speeds=]
$B/nft_run.exe bank=banks/<name> dataset=data/markers/pinball-d220-l2-i1/pinball dpi=220 out=results/local/<file>.json threads=1 repeats=5
.venv/Scripts/python -m nftbench.score --bank banks/<name> --result results/local/<file>.json [--result ...] --md results/phase<n>/<table>.md
```

## Rules

* `dpi` must match the bank's marker dpi; `nft_run` and the scorer refuse a mismatch — fix the inputs, never the check.
* Timing comparisons need `repeats>=3` on an idle machine; say so when you report numbers from fewer.
* Tables in `results/phase<n>/` come only from `nftbench.score --md`; never edit numbers by hand.
* Report every number with its configuration (engine, threads, dpi, bank, build); the result header has it.
