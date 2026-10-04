# Equivalence check: new pipeline vs the exploratory `nft_eval` harness

Purpose: show that splitting `tests/nft_eval.cpp` into exporter (`nft_export`), runner (`nft_run`) and scorer (`nftbench.score`)
did not change what is measured, before the old harness is deleted.

## Setup

* Marker dataset `data/markers/pinball-d150-l2-i3/` (150 dpi, min/max dpi 30/150, level 2, leveli 3), the one the exploratory
  runs used.
* Bank: `nft_export ... dpi=150 trials=10 mode=detect legacy_hash=1` (390 frames, 640x480, fovy 45). `legacy_hash=1` seeds each
  group with `std::hash<std::string>` exactly as `nft_eval` did, so on the same compiler (MSVC 19.44) the frames are the ones
  `nft_eval` rendered.
* Runner: `nft_run threads=1`. Reference: `results/win-msvc/pinball_full.txt` (exploratory run, same machine, same compiler).

## Result

* `found%` and `ok%`: **identical in all 39 detection rows**.
* Median corner error: identical in all 39 rows when computed with `nft_eval`'s definition (mean over the 4 marker corners
  **plus the marker centre**). The new scorer follows the spec (mean over the 4 corners), which moves medians by up to a few
  hundredths of a pixel (e.g. `scale=2.5`: 0.25 old, 0.28 new). This is a definition change, not a behaviour change.

## Not compared

Tracking rows are not expected to match: `nft_eval` stopped tracking as soon as the pose error exceeded 5 px *using ground truth*,
which no real application can do. `nft_run` never reads ground truth; AR2 decides by itself when tracking is lost. Tracking is
checked for plausibility in the phase 1 results instead.

## Cross-platform note

`std::hash<std::string>` differs between MSVC and libstdc++, so the exploratory Windows and Linux runs (`results/win-msvc/`,
`results/linux-gcc/`) used different synthetic frames for the detection groups, although their results agreed. New banks use a
stable FNV-1a hash and are identical on every platform.
