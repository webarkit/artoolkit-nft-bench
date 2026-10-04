# AGENTS.md — native/

Adds to the root [AGENTS.md](../AGENTS.md); never overrides it.

* `src/synth.*`, `src/scenarios.*` render synthetic frames. **Do not change the order in which `Rng` is consumed** without saying
  so: it changes every synthetic bank, and results stop being comparable with earlier publications. Seeds use FNV-1a; `std::hash`
  is only behind `legacy_hash=1` (it differs between standard libraries).
* `src/nft_run.cpp` is the native runner. A runner **never reads ground truth** (`gt_pose`, `gt_corners`): it decides tracking loss
  by itself, as an application would.
* Result headers carry only the allow-listed host fields (`hostInfo()`); `python/tests/test_nft_run.py` enforces it. Never add
  host names, user names, paths or environment variables.
* Timing: wall time around the library call only (`nowMs()`); with `repeats>1` the first pass is warm-up.
* Tests: `native/tests/*.cpp` with the assertion helpers in `check.hpp`, registered with `add_test`; run
  `ctest --preset windows-msvc`. New test → add it to the `foreach` in `native/CMakeLists.txt`.
* Bank and result formats are defined by `python/nftbench/schema.py`; change both sides together.
