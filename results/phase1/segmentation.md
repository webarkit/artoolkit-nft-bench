# Ground truth for `pinball-bench.mp4`: poster corner segmentation

Tool: `python/nftbench/segment.py`, run as
`scripts/segment_bank.py --bank banks/pinball-bench --video data/videos/pinball-bench.mp4`.

## Counts

| frames | accepted | rejected: truncated by the frame border | rejected: low confidence |
|---|---|---|---|
| 298 | 291 | 7 | 0 |

## Spot check (by eye)

`banks/pinball-bench/spotcheck.png`, 24 frames chosen with seed 0 (frames 0, 4, 11, 21, 49, 75, 81, 85, 141, 144, 158, 164,
174, 175, 183, 185, 199, 211, 230, 233, 241, 261, 274, 280).

* 23 accepted: every quad lies on the poster edges, and the TL marker is always on the poster's top-left corner.
* 1 rejected (frame 199): the poster touches the top edge of the frame, so rejecting it is correct.
* Wrong quads among accepted tiles: **0** (gate: at most 2).

Corners checked at full resolution on frames 0 (small poster) and 211 (motion blur): sharp frames are within about 1-2 px of
the visible paper corner; on blurred frames the corner is plausible but less certain.

## Findings that matter for the metrics

* **The print has a thin white margin.** The segmentation finds the outer edge of the paper, which is a few pixels outside the
  corners of the image content. A systematic offset between the projected marker corners and these corners is therefore
  expected; Task 9 estimates it from the engine poses and applies it as a documented correction.
* **Colour is required.** On the grey bank frames the poster's light areas merge with the wall and most frames were rejected
  (51 accepted). Segmentation therefore reads the colour frames from the source video.
* Ground truth is approximate (about 1-2 px on sharp frames, worse under blur). Real-clip accuracy numbers are reported with
  that caveat; exact accuracy comes from the synthetic bank.
