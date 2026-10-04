# artoolkit-nft-bench Phase 1 (native baseline) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the repo scaffolding, a shared frame-bank + result format with a scorer, a native (artoolkit5) runner, ground-truth corner segmentation for `pinball-bench.mp4`, and the first native results table on both frame banks.

**Architecture:** Engines never see ground truth. A *frame bank* (grey PNG frames + `bank.json`) is produced once, either synthetically with an exact pose per frame (C++ `nft_export`) or from the real video with segmented poster corners (Python). Each engine has a runner that reads a bank and writes a `result.json`. A Python scorer reads only a bank and result files and prints the tables. Phase 1 builds the bank/result formats, the scorer, and the `native` runner; later phases add runners without touching the scorer.

**Tech Stack:** C++11 + CMake (existing), nlohmann/json and stb_image(_write) via FetchContent, Python 3.12 with numpy, opencv-python-headless, pytest.

**Spec:** `docs/superpowers/specs/2026-10-03-artoolkit-nft-bench-design.md`

## Global Constraints

- `extern/artoolkit5` is a pinned submodule and is **never modified**; portability fixes go in this repo's CMake.
- Pull requests target `dev`, never `main`; Conventional Commits (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`) for commits and PR titles, scopes `native`, `wasm`, `jsartoolkitnft`, `frames`, `scorer`, `markers`, `runner`, `docs`, `ci`.
- Every repository artifact is in English.
- Every committed result carries its configuration header: engine and version, build flags, threads, dpi, camera, host.
- Never commit build trees, decoded frame banks (`banks/`), raw CSV/logs, `.venv`, `node_modules`. Committed media: small reproducible clips with provenance only.
- Every source file (C/C++, Python, shell, CMake, JS/TS) starts with the webarkit/webarkit LGPL header: file name, `artoolkit-nft-bench`, `This file is part of artoolkit-nft-bench.`, `SPDX-License-Identifier: LGPL-3.0-or-later`, the LGPL notice, `Copyright 2026 WebARKit.`, `Author(s): Walter Perdan @kalwalt https://github.com/kalwalt`. `scripts/license_headers.py` checks it (`--fix` adds it) and `python/tests/test_license_headers.py` runs the check in `pytest`.
- Results storage follows `docs/adr/0001-results-storage.md`: development results go to `results/local/` (git-ignored); only publications go to `webarkit/artoolkit-nft-bench-results` (same visibility as this repo), indexed by `results/manifest.json`.
- Sensitive data: result headers contain only allow-listed host fields (`host_label` from the git-ignored `bench.local.json`, `os`, `cpu`, `cores`, `threads_hw`, `ram_gb`, `compiler`, `build_flags`, `runtime`). Never host names, user names, emails, absolute paths, environment variables, tokens, IP/MAC addresses or device serials.
- Canonical marker: `pinball.jpg`, **220 dpi** (189.0 x 236.5 mm), `genTexData -dpi=220 -min_dpi=30 -max_dpi=220 -level=2 -leveli=1` (genTexData defaults for level/leveli, the same defaults NFT-Marker-Creator-App documents). Marker-dir names encode the parameters: `pinball-d220-l2-i1`.
- Camera for every bank: pinhole, no distortion, `fovy` 45 deg, `cx=w/2`, `cy=h/2`, `fx=fy=(h/2)/tan(fovy/2)`. Synthetic banks 640x480; the real clip stays 1280x720.
- Pose convention: 3x4 row-major `[R|t]`, marker to camera, millimetres, ARToolKit camera (x right, y down, z forward); marker frame origin at the image's bottom-left, y up, z toward the viewer; mm = px / dpi * 25.4. Pose arrays in JSON are the 12 floats row-major.
- Corner order everywhere: marker-image TL, TR, BR, BL, as 8 floats `[x0,y0,...,x3,y3]` in frame pixels.

## Review Focus

Failure modes the spec implies that no feature task exercises directly. Each has a test in the owning task.

1. Poster truncated by the frame edge or too blurred to segment: segmentation returns no corners (never wrong ones) and the scorer excludes the frame (Task 8, Task 3).
2. Engine returns no pose, or a NaN/inf pose: counted as `lost`, never as zero error, never crashing the scorer (Task 3).
3. A result produced with a different marker dpi, marker dataset or camera than its bank: the scorer refuses to score it (Task 2).
4. Corner order flipping cyclically between frames in the segmentation output: continuity picks the cyclic shift closest to the previous frame (Task 8).
5. Variable frame timing in the video (299/12 fps container): timestamps come from the container per frame, and timestamp-based metrics use them (Task 7, Task 3).

---

## File Structure

```
LICENSE  CONTRIBUTING.md  AGENTS.md  CLAUDE.md  GEMINI.md  README.md
.github/{copilot-instructions.md,pull_request_template.md}   .agents/instructions.md
pyproject.toml  requirements.txt  requirements-dev.txt
python/nftbench/{schema,geometry,metrics,score,video_bank,segment}.py
python/tests/{test_*.py,data/}
scripts/{make_video_bank.py,segment_bank.py,make_marker.sh,run_phase1.sh}
native/CMakeLists.txt
native/src/{rng,synth,scenarios,bank_io,engine}.{hpp,cpp}
native/src/{nft_export.cpp,nft_run.cpp}
native/tests/test_*.cpp
data/videos/{pinball-bench.mp4,README.md}   data/markers/pinball-d150-l2-i3/  data/markers/pinball-d220-l2-i1/
banks/ (git-ignored)   results/phase1/
```

`tests/nft_eval.cpp` is split into `native/src/{rng,synth,scenarios}` and then deleted in Task 6.

---

### Task 1: Repo scaffolding, agent/contributor files, remote

**Files:**
- Create: `LICENSE` (LGPL-3.0 text), `CONTRIBUTING.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`, `.github/pull_request_template.md`, `.agents/instructions.md`
- Modify: `README.md` (what the repo is, link to spec, plan and ADRs, layout), `.gitignore` (add `banks/`, `results/local/`, `bench.local.json`, `.venv/`, `node_modules/`, `__pycache__/`, `*.pyc`)
- Already present: `docs/adr/0001-results-storage.md`

**Interfaces:**
- Produces: the contributor rules every later task follows; the `dev` branch and the `feat/phase-1-baseline` working branch.

- [ ] **Step 1: Write `CONTRIBUTING.md`** with the spec section 11 workflow: PRs to `dev`, branch naming `type/short-description`, Conventional Commits with the scope list from Global Constraints, English-only, pre-PR verification commands (CMake build, `ctest`, `pytest`), release PR `dev` to `main`, the results-storage rule (ADR-0001) and the allowed/forbidden data lists for published files.
- [ ] **Step 2: Write `AGENTS.md`** (canonical): what the project is, layout, the exact build/test commands (filled in as tasks add them; Task 1 lists the ones that already exist: CMake configure/build), the hard rules from spec section 11 verbatim in substance, the ADR-0001 storage rule, and the allowed/forbidden data lists. Link to `CONTRIBUTING.md`; do not copy it.
- [ ] **Step 3: Write the pointer files.** `CLAUDE.md` = `@AGENTS.md` plus Claude/Windows notes (prefer POSIX shell; never round-trip source through PowerShell `Get-Content`/`Set-Content`). `GEMINI.md` and `.agents/instructions.md` = pointer to `AGENTS.md` plus the critical rules inlined. `.github/copilot-instructions.md` = critical rules inlined plus link. `.github/pull_request_template.md` = base-branch reminder, PR-title format, checklist.
- [ ] **Step 4: Verify consistency.** Run: `grep -L "AGENTS.md" CLAUDE.md GEMINI.md .github/copilot-instructions.md .agents/instructions.md` — expected: no output. Run: `grep -l "dev" CONTRIBUTING.md AGENTS.md .github/pull_request_template.md` — expected: all three listed.
- [ ] **Step 5: Branches.** From `main`: `git checkout -b dev`, then `git checkout -b feat/phase-1-baseline`. Commit: `docs: add contributor and agent guidance, license and README`.
- [ ] **Step 6: Confirm with the user, then create and push.** Ask the user to confirm creating `webarkit/artoolkit-nft-bench` (private) and pushing `main` and `dev`. Only after an explicit yes: `gh repo create webarkit/artoolkit-nft-bench --private --source=. --remote=origin --push` for `main`, then `git push -u origin dev feat/phase-1-baseline`. Expected: `gh repo view webarkit/artoolkit-nft-bench --json visibility` prints `PRIVATE`.

---

### Task 2: Python environment, schemas and geometry

**Files:**
- Create: `pyproject.toml` (pytest `pythonpath = ["python"]`), `requirements.txt` (`numpy`, `opencv-python-headless`), `requirements-dev.txt` (`-r requirements.txt`, `pytest`), `python/nftbench/__init__.py`, `python/nftbench/schema.py`, `python/nftbench/geometry.py`
- Test: `python/tests/test_schema.py`, `python/tests/test_geometry.py`

**Interfaces:**
- Produces (`schema.py`):
  - `@dataclass Camera(fx, fy, cx, cy)`; `@dataclass Frame(seq:int, i:int, file:str, t:float, gt_pose:np.ndarray|None, gt_corners:np.ndarray|None)`; `@dataclass Bank(kind, name, width, height, camera:Camera, marker_image:str, marker_dpi:float, marker_w_mm:float, marker_h_mm:float, frames:list[Frame], root:Path)`
  - `@dataclass ResultFrame(seq, i, state, pose:np.ndarray|None, t_detect_ms:float|None, t_track_ms:float|None, t_total_ms:float, blocked_ms:float)`; `@dataclass Result(header:dict, init:dict, frames:list[ResultFrame])`
  - `load_bank(path:Path)->Bank`, `load_result(path:Path)->Result`, `check_compatible(bank:Bank, result:Result)->None` (raises `IncompatibleResult` on marker dpi / marker dataset name / camera mismatch)
- Produces (`geometry.py`): `project_corners(pose:np.ndarray, cam:Camera, w_mm:float, h_mm:float)->np.ndarray` shape (4,2) in the corner order TL,TR,BR,BL; `corner_error_px(pose, gt_corners, cam, w_mm, h_mm)->float` (mean distance); `pose_valid(pose)->bool` (finite and positive depth for all four corners); `pose_error(pose_est, pose_gt, w_mm, h_mm)->tuple[float,float]` (centre translation mm, rotation deg).

- [ ] **Step 1: Create the venv** (`python -m venv .venv`, install `requirements-dev.txt`). Verify: `.venv/Scripts/python -c "import cv2, numpy, pytest"` exits 0.
- [ ] **Step 2: Write failing tests.** `test_geometry.py`: `test_frontal_pose_projects_to_expected_corners` (identity-facing pose at 500 mm, 100x200 mm marker, known fx: assert the four pixels to 1e-6), `test_corner_error_zero_for_identical_pose`, `test_pose_valid_rejects_nan_and_behind_camera`, `test_pose_error_rotation_90deg`. `test_schema.py`: `test_load_bank_roundtrip` (fixture bank.json in `python/tests/data/`), `test_check_compatible_rejects_dpi_mismatch`, `test_check_compatible_rejects_camera_mismatch`, `test_check_compatible_accepts_matching`.
- [ ] **Step 3: Run** `.venv/Scripts/python -m pytest python/tests -q` — expected FAIL (modules missing).
- [ ] **Step 4: Implement** `schema.py` and `geometry.py` to the signatures above. Corners: marker mm points `(0,H),(W,H),(W,0),(0,0)` projected with `p = K (R P + t)`.
- [ ] **Step 5: Run** the same command — expected all pass.
- [ ] **Step 6: Commit** `feat(scorer): add bank/result schemas and pose geometry`.

---

### Task 3: Scorer metrics and CLI

**Files:**
- Create: `python/nftbench/metrics.py`, `python/nftbench/score.py`
- Test: `python/tests/test_metrics.py`, `python/tests/test_score_cli.py`, fixtures `python/tests/data/{bank_small.json,result_small.json}` (+ tiny frames not required)

**Interfaces:**
- Consumes: Task 2 dataclasses and `geometry` functions.
- Produces (`metrics.py`):
  - `summarize(bank:Bank, result:Result, ok_px:float=5.0)->dict` with keys `groups` (per bank group: `n`, `valid_pct`, `ok_pct`, `median_px`, `p90_px`, `median_mm`, `median_deg`, `lost_events`, `first_lock_frame`, `jitter_px`, `t_detect_ms{p50,p95,max}`, `t_track_ms{...}`, `t_total_ms{...}`, `blocked_ms_max`), plus `track_share` and `track_time_share`.
  - `track_time_share(states:list[str], times:list[float], bin_ms:float=10.0)->float`: per sequence (stretch), bins laid from the first frame's time; each bin takes the state of the most recent frame at or before the bin start; the last frame contributes no bin; share = bins in `tracked` / all bins, pooled over sequences.
  - `jitter_px(corners_seq:np.ndarray)->float`: RMS of the second difference of the four projected corners over consecutive `tracked` frames only.
- Produces (`score.py`): CLI `python -m nftbench.score --bank <dir> --result <file> [--result ...] [--ok-px 5] [--md out.md]` printing a markdown table per group and one row per result.

- [ ] **Step 1: Failing tests** in `test_metrics.py`: `test_lost_frames_are_not_zero_error` (frames with `pose=None` or NaN pose lower `valid_pct`, never enter `median_px`), `test_frames_without_gt_are_excluded` (frames with `gt_corners=None` excluded from accuracy and counted in `n_excluded`), `test_track_time_share_hand_computed` (states `[detected,tracked,tracked,tracked]` at times `[0,.1,.2,.3]` s, 10 ms bins: assert the exact share by hand), `test_track_time_share_uses_timestamps_not_indices` (non-uniform timestamps change the result), `test_jitter_zero_for_linear_motion`, `test_lost_events_counts_tracked_to_lost_transitions`, `test_first_lock_frame`. `test_score_cli.py`: `test_cli_prints_table_for_small_fixture` and `test_cli_refuses_incompatible_result` (non-zero exit, message names the mismatch).
- [ ] **Step 2: Run** `.venv/Scripts/python -m pytest python/tests -q` — expected FAIL.
- [ ] **Step 3: Implement** `metrics.py` and `score.py` to the signatures. Accuracy uses `corner_error_px` against `gt_corners` when present, else against `gt_pose` projected; `ok` means error below `ok_px`.
- [ ] **Step 4: Run** — expected all pass. **Step 5: Commit** `feat(scorer): add metrics and score CLI`.

---

### Task 4: Native synthetic library and bank exporter

**Files:**
- Create: `native/CMakeLists.txt`, `native/src/rng.hpp`, `native/src/synth.{hpp,cpp}`, `native/src/scenarios.{hpp,cpp}`, `native/src/bank_io.{hpp,cpp}`, `native/src/nft_export.cpp`
- Modify: root `CMakeLists.txt` (`add_subdirectory(native)` replacing the `tests` one only in Task 6; FetchContent for `nlohmann_json` v3.11.3 and `stb` pinned to the SHA of nothings/stb master recorded at that time, in `cmake/ThirdParty.cmake`)
- Test: `native/tests/test_synth.cpp`, `native/tests/test_bank_io.cpp` (plain assert executables registered with `add_test`)

**Interfaces:**
- Produces: library `nftbench_synth` (namespace `nftbench`) with: `struct Rng` (xorshift64*, identical to `tests/nft_eval.cpp`), `struct Camera{int w,h;double fx,fy,cx,cy;}`, `struct Pose{double R[3][3];double t[3];}`, `struct Marker{...; double widthMM() const; double heightMM() const;}`, `Camera makeCamera(int w,int h,double fovyDeg)`, `bool loadMarker(const std::string& jpg,double dpi,Marker&)`, `Pose makePose(const PoseSpec&,const Marker&,const Camera&)`, `std::vector<float> makeBackground(const Camera&,Rng&,double)`, `void renderFrame(const Marker&,const Camera&,const std::vector<Pose>&,const std::vector<float>&,const Degrade&,Rng&,std::vector<uint8_t>&)` — moved from `tests/nft_eval.cpp` **without changing behaviour or the order in which `Rng` is consumed**.
- Produces (`scenarios.hpp`): `struct BankFrame{int seq,i;Pose gt;std::vector<uint8_t> grey;double t;std::string group;}`; `std::vector<BankFrame> buildDetectionFrames(const Marker&,const Camera&,uint64_t seed,int trials,const std::vector<std::string>& scenarioNames)` and `buildTrackingFrames(const Marker&,const Camera&,uint64_t seed,int sequences,int seqlen,const std::vector<double>& speeds)` — extracted from the loops in `main()` of `tests/nft_eval.cpp` with the same seeds, specs and RNG order. Group strings: `detect/<scenario>=<level>`, `track/speed=<v>`.
- Produces (`bank_io.hpp`): `void writeBank(const std::string& dir,const Marker&,const std::string& markerImage,const Camera&,const std::vector<BankFrame>&,const std::string& name)` writing `frames/NNNNNN.png` (8-bit grey) and `bank.json` (schema in Task 2); `struct BankData{...}; BankData readBank(const std::string& dir)`.
- Produces: executable `nft_export out=<dir> image=<jpg> dpi=<f> [width=640 height=480 fovy=45 seed=1 trials=10 seqs=3 seqlen=90 scenarios=a,b speeds=0,2,...]`; corners are computed from the true pose with the Task 2 convention and written as `gt_corners`.

- [ ] **Step 1: Failing tests.** `test_synth.cpp`: `test_pixel_to_plane_roundtrip` (project a marker point then invert, error < 1e-6), `test_make_pose_frontal_distance` (`distFactor=1` puts the marker height at 80% of frame height), `test_render_is_deterministic` (same seed twice gives byte-identical frames), `test_rng_first_values` (pin the first three `u01()` for seed 1 copied from the current `nft_eval` implementation). `test_bank_io.cpp`: `test_bank_roundtrip` (write a 2-frame bank to a temp dir, read back, poses and corners equal to 1e-9), `test_corners_match_python_convention` (a frontal pose's TL corner is the projection of marker point `(0,H)`).
- [ ] **Step 2: Build and run** `cmake --build build/win-vs2022 --config Release --target nftbench_tests` then `ctest --test-dir build/win-vs2022 -C Release` — expected FAIL (library missing).
- [ ] **Step 3: Implement** the library, scenarios and `bank_io` as specified; add FetchContent entries and the `native/CMakeLists.txt` targets (`nftbench_synth`, `nft_export`, tests).
- [ ] **Step 4: Run** the same commands — expected all pass.
- [ ] **Step 5: Commit** `feat(native): extract synthetic frame library and add bank exporter`.

---

### Task 5: Native runner `nft_run`

**Files:**
- Create: `native/src/engine.{hpp,cpp}` (KPM + AR2 wrapper moved from `Engine` in `tests/nft_eval.cpp`), `native/src/nft_run.cpp`
- Test: `native/tests/test_engine.cpp`

**Interfaces:**
- Consumes: Task 4 `readBank`, `Camera`, `Marker`.
- Produces: `struct EngineConfig{std::string dataset;Camera cam;int kpmProc;int threads;}`; class `Engine` with `bool init(const EngineConfig&)`, `bool detect(const uint8_t* grey,float pose[3][4],int* inliers,double* ms)`, `int track(const uint8_t* grey,float pose[3][4],double* ms)` (0 ok, negative lost), `void setInitPose(const float pose[3][4])`.
- Produces: executable `nft_run bank=<dir> dataset=<path-no-ext> dpi=<f> out=<result.json> [threads=1 kpm_proc=1 repeats=1]`. Per sequence it resets state; per frame: if not tracking run `detect`, state `detected` or `lost`; else `track`, state `tracked` or `lost` (and tracking stops on loss). It never reads `gt_*`. With `repeats>1` the whole bank is run that many times (first repeat discarded as warm-up if `repeats>1`), and each frame's `t_*_ms` is the median over the kept repeats. Exit code 2 if `dpi` differs from the bank's `marker.dpi`. `result.json` follows the Task 2 schema with `header` keys: `engine="native"`, `engine_version` (submodule commit), `build` (compiler, config), `host`, `marker_dataset` (directory name), `marker_dpi`, `camera`, `params{threads,kpm_proc,repeats}`; `blocked_ms = t_total_ms` (synchronous). `host` contains exactly the allow-listed fields from Global Constraints; `host_label` is read from `bench.local.json` (`"unlabelled"` if absent). Runs write to `results/local/` by default.

- [ ] **Step 1: Failing test** `test_engine.cpp`: `test_detect_finds_marker_in_clean_synthetic_frame` (render one frontal frame with the 150-dpi dataset under `data/markers/pinball-d150-l2-i3/`; assert `detect` true and pose depth within 2% of truth), `test_track_after_detect_returns_ok_on_same_frame`, `test_result_header_has_only_allowed_host_fields` (run `nft_run` on a 1-frame bank; parse the JSON; assert the `host` keys equal the allow-list exactly and that no string value contains the current user name, the machine name or a drive-letter absolute path).
- [ ] **Step 2: Run** `ctest ... -R test_engine` — expected FAIL. **Step 3: Implement** `engine.*` and `nft_run.cpp`. **Step 4: Run** — expected PASS.
- [ ] **Step 5: Smoke** `build/.../nft_run.exe bank=banks/smoke dataset=... dpi=150 out=results/smoke.json` on a 1-trial bank from `nft_export`, then `.venv/Scripts/python -m nftbench.score --bank banks/smoke --result results/smoke.json` — expected a table with `valid_pct` 100 for `detect/scale=1.5`.
- [ ] **Step 6: Commit** `feat(runner): add native nft_run`.

---

### Task 6: Equivalence check against the earlier suite, then retire `nft_eval`

**Files:**
- Create: `scripts/make_marker.sh`, `data/markers/pinball-d150-l2-i3/` (move existing `data/markers/pinball.*` here), `docs`-free note in `results/phase1/equivalence.md`
- Delete: `tests/nft_eval.cpp`, `tests/CMakeLists.txt`; modify root `CMakeLists.txt` to drop `add_subdirectory(tests)`
- Modify: `README.md`, `AGENTS.md` (replace the `nft_eval` commands)

**Interfaces:**
- Produces: `scripts/make_marker.sh <jpg> <dpi> <min_dpi> <max_dpi> <level> <leveli> <outdir>` copying the jpg into `<outdir>` and running `genTexData` non-interactively (`< /dev/null`), so datasets are reproducible by one command.

- [ ] **Step 1:** Move the existing dataset to `pinball-d150-l2-i3` (parameters: dpi 150, min 30, max 150, level 2, leveli 3) and write `scripts/make_marker.sh`.
- [ ] **Step 2:** Export the detection bank at 150 dpi with the old settings (`seed=1 trials=10`, all scenarios, no tracking), run `nft_run` (threads 1), and score it.
- [ ] **Step 3: Verify equivalence.** Compare the scorer's `valid_pct`, `ok_pct` and `median_px` per `detect/<scenario>=<level>` group with `results/win-msvc/pinball_full.txt` (found%, ok%, med_px). Expected: identical `found%` and `ok%` in every row and `median_px` within 0.01. If any row differs, stop and debug the exporter/runner before continuing. Record the comparison in `results/phase1/equivalence.md`. Tracking rows are **not** required to match: the old harness dropped tracking when the pose error exceeded 5 px using ground truth, which the new runner never does; state this in the note and only check plausibility (all-ok through 20 px/frame).
- [ ] **Step 4:** Delete `tests/` and its references; rebuild everything and run `ctest` and `pytest` — expected green.
- [ ] **Step 5: Commit** `refactor(native): replace nft_eval with exporter, runner and scorer`.

---

### Task 7: Real-video frame bank

**Files:**
- Create: `data/videos/pinball-bench.mp4` (copied from `D:\kalwalt-github\webarkit\examples\videos\pinball-bench.mp4`), `data/videos/README.md` (source repo, source commit from `git rev-parse HEAD` in that clone, 1280x720 H.264, 298 frames, license LGPL-3.0-or-later as the source repo), `python/nftbench/video_bank.py`, `scripts/make_video_bank.py`
- Test: `python/tests/test_video_bank.py`

**Interfaces:**
- Produces: `video_bank.make_bank(video:Path, out_dir:Path, marker_image:str, marker_dpi:float, fovy_deg:float=45.0)->Path` decoding every frame with OpenCV, writing grey PNG `frames/NNNNNN.png` (BGR2GRAY) and `bank.json` (`kind="real"`, one sequence `seq=0`, `t` = `CAP_PROP_POS_MSEC/1000` per frame, `gt_*` null), returning the bank path.

- [ ] **Step 1: Failing tests** with a tiny synthetic mp4 written by `cv2.VideoWriter` in the test: `test_frame_count_matches_video`, `test_timestamps_come_from_container_not_index` (write frames with a deliberately non-uniform timeline or assert `t` is strictly increasing and equals the decoder's per-frame timestamps), `test_camera_uses_fovy`, `test_gt_fields_null`.
- [ ] **Step 2: Run** — expected FAIL. **Step 3: Implement** `make_bank`. **Step 4: Run** — expected PASS.
- [ ] **Step 5:** Build the real bank: `.venv/Scripts/python scripts/make_video_bank.py --video data/videos/pinball-bench.mp4 --out banks/pinball-bench --marker-image pinball.jpg --dpi 220`. Verify: `banks/pinball-bench/bank.json` lists 298 frames and `ffprobe` duration (11.96 s) matches the last timestamp within one frame.
- [ ] **Step 6: Commit** `feat(frames): add real-video frame bank builder and the benchmark clip`.

---

### Task 8: Poster corner segmentation (ground truth for the real clip)

**Files:**
- Create: `python/nftbench/segment.py`, `scripts/segment_bank.py`
- Test: `python/tests/test_segment.py`

**Interfaces:**
- Produces: `segment_quad(grey_or_bgr:np.ndarray, min_area_frac:float=0.002)->tuple[np.ndarray|None,float]` returning (corners (4,2) float32 sub-pixel TL,TR,BR,BL | `None`, confidence in [0,1]); `order_corners(quad:np.ndarray, prev:np.ndarray|None)->np.ndarray` (initial TL,TR,BR,BL by position; afterwards the cyclic shift closest to `prev`); `segment_bank(bank_dir:Path, report:bool=True)->dict` writing `gt_corners` for accepted frames into `bank.json`, plus `banks/<name>/overlay/` PNGs, `spotcheck.png` (seeded sample of 24 frames with the quad drawn) and returning `{n_total, n_accepted, n_rejected_truncated, n_rejected_lowconf}`.
- Method: wall colour estimated robustly (median of the frame border band), foreground = distance from the wall colour above an Otsu threshold, morphological close, largest connected component, `approxPolyDP` to 4 vertices, `cornerSubPix`. Rejection: quad touches the frame border (truncated), area below `min_area_frac`, non-convex, rectangularity (contour area / quad area) below 0.9, or marker aspect ratio (W/H = 0.799 +/- 35% after rough rectification) violated.

- [ ] **Step 1: Failing tests** (images built in the test by warping a textured rectangle onto a grey wall with `cv2.warpPerspective` and known corners): `test_recovers_known_quad_within_1px`, `test_recovers_quad_under_gaussian_blur_sigma2_within_2px`, `test_recovers_quad_with_horizontal_illumination_gradient`, `test_truncated_quad_returns_none` (Review Focus 1), `test_blank_wall_returns_none`, `test_order_corners_follows_previous_frame_after_roll` (Review Focus 4: rotate the quad 120 degrees between two frames; assert the output order does not jump cyclically), `test_low_contrast_poster_returns_low_confidence_or_none`.
- [ ] **Step 2: Run** — expected FAIL. **Step 3: Implement** to the signatures. **Step 4: Run** — expected PASS.
- [ ] **Step 5: Run on the real clip:** `.venv/Scripts/python scripts/segment_bank.py --bank banks/pinball-bench`. Expected: a report with the four counts; `n_accepted + n_rejected_* == 298`.
- [ ] **Step 6: Spot check by eye.** Open `banks/pinball-bench/spotcheck.png` and judge each of the 24 tiles: quad on the poster edges, correct corner order, no accepted frame with a visibly wrong quad. Record the verdict (accepted, rejected, and any wrong ones) in `results/phase1/segmentation.md`. If more than 2 of 24 accepted tiles are wrong, tighten the rejection rules and repeat from Step 5; do not proceed with a ground truth that fails this check.
- [ ] **Step 7: Commit** `feat(frames): add poster corner segmentation for ground truth`.

---

### Task 9: Canonical marker, banks at 220 dpi, native results

**Files:**
- Create: `data/markers/pinball-d220-l2-i1/` (via `scripts/make_marker.sh`), `scripts/run_phase1.sh`, `results/local/phase1/*.json` (not committed), `results/phase1/README.md` and `results/phase1/*.md` tables (committed)

**Interfaces:**
- Consumes: everything above. `scripts/run_phase1.sh` runs, in order: marker generation if missing, synthetic export at 220 dpi, `nft_run` with `threads=1` and with default threads (`threads=-1`, `repeats=5`) on the synthetic and real banks, then `nftbench.score` writing `results/phase1/README.md`.

- [ ] **Step 1:** Generate the marker: `scripts/make_marker.sh data/markers/pinball.jpg 220 30 220 2 1 data/markers/pinball-d220-l2-i1` (about several minutes). Verify the three files `pinball.iset/.fset/.fset3` exist and the `genTexData` log shows level 2 / leveli 1.
- [ ] **Step 2:** Export the synthetic bank at 220 dpi (`trials=10`, `seqs=3`, `seqlen=90`, all scenarios, speeds `0,2,5,10,20,35`) into `banks/synthetic-d220`.
- [ ] **Step 3:** Run `nft_run` (threads 1 and default, `repeats=5`) on `banks/synthetic-d220` and `banks/pinball-bench` with the d220 dataset; expected: four result files with complete headers.
- [ ] **Step 4: Systematic-offset check on the real clip.** Using the scorer, compute the mean signed offset between projected marker corners and `gt_corners` over the first 50 tracked frames. If the mean offset exceeds 3 px and is consistent in direction, the printed poster's visible area is not the full image: record the margin estimate in `results/phase1/README.md` and apply it as a documented correction (never silently).
- [ ] **Step 5:** Score everything: `.venv/Scripts/python -m nftbench.score --bank banks/synthetic-d220 --result results/phase1/native-synthetic-t1.json --result results/phase1/native-synthetic-tN.json --md results/phase1/synthetic.md` and the same for the real bank. Expected: markdown tables for detection scenarios, tracking speeds, and the real clip (valid%, ok%, median/p90 px, lost events, first lock frame, jitter, timing percentiles, `track_share`, `track_time_share`).
- [ ] **Step 6: Commit** `feat(runner): add first native results at 220 dpi` (markdown tables only; raw results stay in `results/local/` until Task 10 publishes them).

---

### Task 10: Documentation and pull request

**Files:**
- Modify: `README.md` (build, marker generation, bank/result formats, scorer usage, Phase 1 results table linked from `results/phase1/`), `AGENTS.md` (final command list), `CONTRIBUTING.md` if commands changed
- Create: `scripts/publish_results.py`, `python/tests/test_publish.py`, `results/manifest.json`

**Interfaces:**
- Produces: `python scripts/publish_results.py <name> --from results/local/<dir> [--release]`: scrubs logs (absolute paths to `<repo>`-relative), scans every file for forbidden patterns (current user and host name, drive-letter or `/home/` absolute paths, emails, IPv4/MAC, `gh[pousr]_` tokens), aborts naming file and line on any hit; otherwise tars, hashes (SHA-256), commits the archive to a local clone of `webarkit/artoolkit-nft-bench-results`, optionally uploads it to an immutable release `results/<name>`, and appends the entry to `results/manifest.json` (name, sha256, size, code commit, results-repo commit, release tag or null).

- [ ] **Step A: Failing tests** in `test_publish.py`: `test_scan_flags_absolute_windows_path`, `test_scan_flags_username_and_hostname`, `test_scan_flags_email_and_token`, `test_scrub_rewrites_repo_paths_relative`, `test_manifest_entry_fields`. Run pytest, expect FAIL; implement; run, expect PASS. Commit `feat(scorer): add results publisher with sensitive-data scan`.
- [ ] **Step B: Confirm with the user, then create the results repository** `webarkit/artoolkit-nft-bench-results` (private, same visibility as this repo) with a ruleset forbidding force push and deletion of its default branch. Publish `phase-1`. Commit `results/manifest.json`: `docs(scorer): publish phase 1 results`.

- [ ] **Step 1:** Update the docs so every command in them was run in this phase; delete the obsolete `nft_eval` references. Verify with `grep -rn "nft_eval" README.md AGENTS.md CONTRIBUTING.md` — expected no output.
- [ ] **Step 2:** Run the full gate: build (`cmake --build build/win-vs2022 --config Release`), `ctest --test-dir build/win-vs2022 -C Release`, `.venv/Scripts/python -m pytest python/tests -q` — all green.
- [ ] **Step 3:** Ask the user to confirm opening a pull request `feat/phase-1-baseline` into `dev` (title `feat(runner): phase 1 native baseline and scorer`). After an explicit yes: `git push -u origin feat/phase-1-baseline` and `gh pr create --base dev`. The PR body states what was and was not done (below).

---

## Scope notes (decisions the executor must not reverse)

- **Deferred from spec section 6 to a later phase:** native "detection in a background thread" (as `nftSimple`) is not part of Phase 1; it only means something once the jsartoolkitNFT blocked-time comparison exists. Phase 1 reports native at 1 thread and at default threads, synchronous.
- **`threads=-1`** means `AR2_TRACKING_DEFAULT_THREAD_NUM`; whether KPM matching itself uses extra threads is verified by reading `kpmMatching` during Task 5 and written into `results/phase1/README.md`, not assumed.
- **leveli:** earlier exploratory runs used `leveli=3`; the bench standard is the genTexData default `leveli=1`, so numbers differ from the earlier 150-dpi table by design. The 150-dpi/leveli-3 dataset is kept only for the Task 6 equivalence check.

## Self-review

- **Spec coverage:** repo/agent files and branches (Task 1, spec 10-11); frame banks synthetic + real (Tasks 4, 7); ground-truth segmentation with spot check and exclusion reporting (Task 8); runner contract and result header (Tasks 2, 5); metrics incl. webarkit `TRACK`/`trackTimeShare`, blocked time, jitter (Task 3); fairness items 1, 2, 4, 5 (Tasks 5, 9; build flags in the result header); `native` baseline on both banks at 220 dpi (Task 9). Phases 2-5 and the background-thread mode are explicitly out of scope above.
- **Type consistency:** `Camera`, `Pose`, `Marker`, `PoseSpec`, `Degrade`, `BankFrame`, `readBank`/`writeBank`, `Engine::detect/track/setInitPose`, and the Python dataclasses use one name each across tasks; bank/result JSON keys are fixed in Tasks 2 and 4 and consumed unchanged in 3, 5, 7, 8.
- **Proportion:** the plan fixes names, signatures, tests and verification commands and leaves bodies to the implementer.
