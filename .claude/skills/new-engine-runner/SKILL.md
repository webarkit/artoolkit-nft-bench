---
name: new-engine-runner
description: What a new engine runner (WASM build of artoolkit5, jsartoolkitNFT in Node or Chromium, others) must do to be scored fairly. Use before writing or reviewing a runner, or when a runner's results fail check_compatible or look inconsistent.
---

# new-engine-runner

A runner reads a frame bank and writes one `result.json`. The scorer then compares engines; it needs no change for a new engine.

## Input: the bank

`banks/<name>/bank.json` + `frames/NNNNNN.png` (8-bit grey). Use `camera` (`fx fy cx cy`, no distortion), `marker.dpi`,
`marker.dataset`. Process frames in order; a new `seq` value starts a new sequence: **reset tracking state**.
**Never read `gt_pose` or `gt_corners`.** Engines that need RGBA get R=G=B=grey.

## Output: result.json (schema in `python/nftbench/schema.py`)

```json
{"schema": 1,
 "header": {"engine": "...", "engine_version": "...", "build": "...", "host": {allow-listed fields only},
            "marker_dataset": "<dataset dir name>", "marker_dpi": 220, "bank": "<bank name>",
            "camera": {"fx":..., "fy":..., "cx":..., "cy":...},
            "params": {"threads": 1, "repeats": 5, "mode": "sync|async", ...}},
 "init": {"load_marker_ms": ..., "startup_ms": ...},
 "frames": [{"seq": 0, "i": 0, "state": "detected|tracked|lost", "pose": [12 floats row-major] or null,
             "t_detect_ms": ..., "t_track_ms": ..., "t_total_ms": ..., "blocked_ms": ...}]}
```

* `pose`: 3x4 `[R|t]` marker → camera, millimetres, ARToolKit camera (x right, y down, z forward). Convert if the engine differs,
  and add a test that a frontal synthetic frame gives depth within 2% of truth.
* `state`: `detected` = KPM found the marker this frame; `tracked` = tracker succeeded this frame; `lost` otherwise.
* `blocked_ms`: wall time during which the engine could not take the next frame (equals `t_total_ms` when synchronous).
* `host`: exactly `host_label os cpu cores threads_hw ram_gb compiler build_flags runtime`; label from `bench.local.json`.
* Timings: library calls only; `repeats>1` discards the first pass and reports medians.

## Check before reporting

1. Run on a 1-trial synthetic bank and score it: frontal groups must be `detected` with sub-pixel error.
2. `python -m nftbench.score --bank ... --result ...` must accept the file (it refuses other dpi, dataset or camera).
3. Run `publish_results.py --dry-run` on the output: no sensitive data.
4. Same marker files, camera and parameters as the native runner; document any parameter the engine cannot match.
