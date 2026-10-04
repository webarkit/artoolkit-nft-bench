# Phase 1 — native baseline

Engine `native`: artoolkit5 (webarkit fork) @ `66aa1cc`, built with MSVC 19.44 `/O2 /Ob2 /DNDEBUG`, synchronous KPM + AR2 loop
(as `nftSimple`). Host `unlabelled`: Windows build 26200, Intel Core i7-9700 (8 cores / 8 threads), 31.8 GB RAM.
Marker `pinball-d220-l2-i1` (pinball.jpg at 220 dpi, min/max dpi 30/220, `genTexData` defaults level 2 / leveli 1).
Every run: 5 passes over the bank, first discarded as warm-up, frame timings = median of the other 4.

Full tables: [synthetic.md](synthetic.md) (2010 frames, 640x480, exact ground truth) and [real.md](real.md)
(`pinball-bench.mp4`, 298 frames, 1280x720, segmented ground truth). Raw results stay in `results/local/phase1/` until they are
published to the results repository (ADR-0001). Supporting notes: [equivalence.md](equivalence.md), [segmentation.md](segmentation.md).

## Synthetic bank (threads = 1)

Detection (KPM), 10 frames per level. Errors are medians over every frame with a valid pose; `ok` = mean corner error < 5 px.

| condition | detected | median error | KPM time p50 |
|---|---|---|---|
| distance up to 4x (marker ~100 px tall) | 100% | 0.2–0.5 px | 33–69 ms (falls with marker size) |
| distance 5x | 60% | 0.4 px | 26 ms |
| tilt up to 55° | 100% | 0.3–0.4 px | 54–73 ms |
| tilt 65° / ≥72° | 10% / 0% | — | 23–29 ms |
| any in-plane roll | 100% | 0.3 px | 58–70 ms |
| blur σ ≤ 3 px / σ 4 | 100% / 70% | ≤1.1 px | 35–66 ms |
| noise σ ≤ 30, contrast down to 25% | 100% | 0.3–0.4 px | 58–75 ms |
| occlusion ≤ 40% / 60% | 100% / 60% | 0.3–0.5 px | 35–70 ms |

Tracking (KPM init + AR2), 3 sequences × 90 frames per speed:

| speed (px/frame) | valid | ok | median error | lost events | AR2 time p50 |
|---|---|---|---|---|---|
| 0 – 20 | 100% | 100% | 0.6–0.9 px | 0 | 0.9–1.0 ms |
| 35 (with motion blur) | 14% | 4% | 25 px (the few poses AR2 still returns are mostly wrong) | 16 | 1.2 ms |

## Real clip `pinball-bench.mp4` (threads = 1)

* One KPM detection on the first frame (73 ms), then **AR2 tracks all 297 remaining frames without a single loss**
  (track share 99.7%, trackTimeShare 99.6%).
* AR2 time p50 / p95: 1.2 / 1.5 ms per frame at 1280x720.
* Corner error against segmented ground truth, over all 291 frames with ground truth (7 excluded): median **5.1 px**,
  p90 9.3 px, max 16 px. It grows through the clip (median 3.8 → 5.1 → 8.0 px over successive thirds) as the poster gets closer
  and larger. `ok%` (49%) at the 5 px threshold measures the ground truth as much as the tracker; see the next section.

## Threads

* `threads=-1` (AR2 default) halves AR2 time: synthetic 0.9–1.0 → 0.5–0.6 ms, real clip 1.2 → 0.6 ms. Accuracy is unchanged.
* **KPM detection does not use threads.** With FREAK features (`BINARY_FEATURE`), `kpmSetSurfThreadNum` is a no-op
  (`lib/SRC/KPM/kpmHandle.cpp`), so detection costs the same at any thread setting. Native's only threading advantage today is in
  AR2 tracking, and in running detection off the frame loop (the background-thread mode, deferred to a later phase).

## Ground truth on the real clip: what the 4 px means

The plan expected a uniform white print border. The estimate says otherwise: the best uniform margin is **−1.7 mm**
(first 50 tracked frames; −1.9 mm over all), and the per-corner offsets point in different directions — three corners
1–2 px inward, the bottom-left corner about 8 px off in a mixed direction. A uniform correction is therefore **not applied**.
Likely causes, not yet separated:

* the camera intrinsics are unknown (fovy 45° is an assumption): a wrong focal length makes the corners, which are extrapolated
  from interior features, drift from the paper edge;
* the poster is not perfectly flat (its bottom-left corner appears slightly bent in the footage);
* segmentation accuracy is about 1–2 px on sharp frames and worse under blur.

Real-clip accuracy therefore mixes tracker error with ground-truth and camera-model error: it is useful for comparing engines on
identical ground truth, not as an absolute figure. The growth of the error with poster size points to the camera model rather than
the tracker. Exact accuracy comes from the synthetic bank.

## Caveats

* An earlier draft of these tables computed error medians only over frames already under 5 px; the final review caught it
  and the tables were regenerated (synthetic detection rows were unaffected, since every valid pose there is under 5 px).

* Jitter follows the spec (second difference of projected corners) and includes real camera motion, so it grows with speed
  even when tracking is exact; on synthetic banks a residual jitter would isolate tracker noise.
* Synthetic frames are rendered from the image the dataset was built from: an upper bound, best used as a comparison baseline.
