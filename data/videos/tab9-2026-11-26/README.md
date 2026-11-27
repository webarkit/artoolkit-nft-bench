# Tab 9 session of 2026-11-26

Three clips recorded for [#13](https://github.com/webarkit/artoolkit-nft-bench/issues/13) and for webarkit's
[webarkit#279](https://github.com/webarkit/webarkit/issues/279) (the fast clip): `fast.mp4`, `static-tripod.mp4` and
`calib-chessboard.mp4`. They follow [docs/recording-guide.md](../../../docs/recording-guide.md), except for the order and the
clips not recorded (below).

## Device, app and settings

* **Device:** the Tab 9 used for webarkit's M9 (Android 15; M9's exports label it `Tab_9_WiFi`).
* **App:** Open Camera 1.56.2.
* **Settings:** 1280×720, fixed 30 fps, every setting the same for the three clips (the maintainer's statement).
  Open Camera's settings as read by the maintainer on 2026-11-27, unchanged since the session (his statement):
  * **video stabilisation:** off (this Open Camera on the Tab 9 offers no stabilisation option in its video settings);
  * **zoom:** 1×, never changed;
  * **focus:** mode "Continuous", not locked;
  * **exposure:** not locked (no exposure lock used).

  HDR and the guide's other settings were not written down beyond "the same for the three clips".
* **Date and order:** 2026-11-26, local time 23:08 (`fast`), 23:19 (`static-tripod`), 23:20 (`calib-chessboard`); not the
  guide's order (calibration first). Only these three of the guide's clips were recorded.
* **Scene:** the poster taped to a plain white wall.

## Measurements

* **Poster print:** 127 × 159 mm (width × height, printed image area). `pinball.jpg` is 1637 × 2048 px, so 327.4 dpi from the
  width and 327.2 dpi from the height: **327 dpi** (`scripts/check_recording.py dpi --mm 127 159`: consistent; the matching
  dataset would be `data/markers/pinball-d327-l2-i1`, not generated here).
* **Chessboard:** 9×6 inner corners, 25 mm squares (`scripts/make_chessboard.py`); the printed 100 mm ruler measures 100 mm.

## The originals

Kept outside every repository, on the maintainer's desktop in a `media-originals/tab9-2026-11-26/` folder beside the
repository clones, and never committed. Copied unchanged; the SHA-256 were checked before and after the copy.

| committed name | original file | local time | bytes | SHA-256 |
|---|---|---|---|---|
| `fast.mp4` | `VID_20261126_230851.mp4` | 23:08 | 30,658,280 | `37f376e1584beda80b048e79df677863da448a13e0fbac98d746b9c00928e29f` |
| `static-tripod.mp4` | `VID_20261126_231929.mp4` | 23:19 | 14,332,450 | `bd5d4176bf5c4c90c099bd847296396399c39023a42dc7bd9ac6b8581a5d7519` |
| `calib-chessboard.mp4` | `VID_20261126_232056.mp4` | 23:20 | 57,281,381 | `a98d5be4a10aee986a5607ad0d46a5ef6d0ead23dd938f14ccd249a67e61a809` |

All three: H.264 Baseline 1280×720 at about 8 Mb/s, 90 kHz timescale, and an AAC track (dropped in the committed files).

**Checks on the originals** (made in the chat that verified the session, before the import):

* all three: 30 fps, no dropped frame, no rotation tag, no location tag, an AAC audio track (to be stripped);
* `fast`: 29.9 s, 898 frames; frame-to-frame motion p90 10.5 px at 1280×720; poster segmented in 98% of frames
  (`check_recording.py quality`, PR #25's head);
* `static-tripod`: 13.8 s, 414 frames, largest frame-to-frame shift 0.5 px, so not trimmed; segmented in 100%;
* `calib-chessboard`: 56.2 s, 1,686 frames; board found in every sampled frame; inner corners over x 108–1191, y 92–622, all 9
  cells of the 3×3 grid; tilt up to 44°; a trial OpenCV calibration gave RMS 0.52 px, fx ≈ 1040 (not committed: the calibration
  is [#10](https://github.com/webarkit/artoolkit-nft-bench/issues/10)).

**Dropped frames:** none.

## The committed files

Made from the originals by [`scripts/encode_session.sh`](../../../scripts/encode_session.sh) (ffmpeg 9.0.2, libx264):

```bash
scripts/encode_session.sh <originals_dir> data/videos/tab9-2026-11-26 \
    fast.mp4=VID_20261126_230851.mp4:18 static-tripod.mp4=VID_20261126_231929.mp4:18 \
    calib-chessboard.mp4=VID_20261126_232056.mp4:22
```

The script checks every spec before the first encode and refuses an existing output; re-making the committed files needs
`--force` as its first argument.

Video only, the camera's container and stream metadata removed (only the muxer's and x264's own encoder tags remain), H.264 High (`libx264 -preset slow`), yuv420p, 1280×720, `+faststart`.
The encodes are deterministic: a second run gave byte-identical files.

| file | CRF | bytes | SHA-256 | frames | duration |
|---|---|---|---|---|---|
| `fast.mp4` | 18 | 10,299,957 | `6120c7a35bb3bf37ab2677f9fb449e3cb4e7cb8abdc47edd6b8e84aaf8141915` | 898 | 29.9 s |
| `static-tripod.mp4` | 18 | 5,316,300 | `7df4e1a57ee39025ffc93fb211c2d0bf3d522d9c483531d98d1b05f89c2f271d` | 414 | 13.8 s |
| `calib-chessboard.mp4` | 22 | 13,061,396 | `1805823bd12dc2f9e025ecf551ddcb2ba9bf180e5b6248f3069014f1d575458c` | 1,686 | 56.2 s |
| total | | 28,677,653 (28.7 MB, limit 40 MB) | | | |

**Lengths.** The guide's and webarkit#279's lengths ("about 20 s", "10 s") are what a clip needs at least. `fast` runs 29.9 s
and `static-tripod` 13.8 s as recorded, and both are kept whole: a longer `fast` holds more lock starts, and `static-tripod`
has no motion to trim (largest frame-to-frame shift 0.5 px). No clip is trimmed.

Two encoder settings matter, both found before any measurement was read:

* **Timestamps.** `-fps_mode passthrough` alone is not enough: the encoder then runs on a 1/30 s clock, re-quantising every
  timestamp and moving the first one to zero (the originals start at 189 and 846 ticks of 90 kHz for `fast` and
  `static-tripod`). The script adds `-copyts`, `-enc_time_base:v demux` and `-video_track_timescale 90000`, and every frame
  keeps its original timestamp exactly.
* **Colour.** The Tab 9 files contradict themselves: the MP4 `colr` atom says full range, BT.601 (`smpte170m`, `bt470bg`), the
  H.264 VUI says limited range, BT.709. Decoders, OpenCV included, follow the VUI. Writing the container's tags into the
  encode would change how it decodes; the script declares limited range and BT.709 in both places, so the encode decodes as
  the original does.

## Re-encode criteria and results

Checked by [`scripts/verify_encode.py`](../../../scripts/verify_encode.py) on each committed file against its original
(OpenCV 5.1.0, ffmpeg 9.0.2):

```bash
<venv-python> scripts/verify_encode.py chessboard <originals_dir>/VID_20261126_232056.mp4 data/videos/tab9-2026-11-26/calib-chessboard.mp4
<venv-python> scripts/verify_encode.py poster <originals_dir>/VID_20261126_231929.mp4 data/videos/tab9-2026-11-26/static-tripod.mp4 --still
<venv-python> scripts/verify_encode.py poster <originals_dir>/VID_20261126_230851.mp4 data/videos/tab9-2026-11-26/fast.mp4
```

### The criteria, and when they were set

Fixed before any encode was read, in the import brief:

* every clip: the same frame count and the same frame timestamps as its original, exactly;
* `calib-chessboard`: on every 5th frame, the chessboard found in the same frames, and a calibration from the encode against
  one from the original: |Δfx|, |Δfy|, |Δcx|, |Δcy| ≤ 0.5 px and |ΔRMS| ≤ 0.05 px;
* `static-tripod` and `fast`: `segment.py` accepts the same frames ±1% of the clip, and on frames both accept, the per-frame
  corner difference at 1280×720 has median ≤ 0.3 px and 99th percentile ≤ 1.0 px. Start at CRF 18, go down by 2 until it passes.

The corner criterion failed at every CRF tried, and the import stopped there. **On 2026-11-27, after the CRF 18–12 results
below had been read, the maintainer replaced it** for `static-tripod` and `fast`:

1. frame count and timestamps identical to the original's (unchanged);
2. `segment.py` accepts the same frames ±1% of the clip (unchanged);
3. **image fidelity, new:** per frame, against the original decoded the same way, luma PSNR median ≥ 42 dB and minimum ≥ 38 dB,
   and SSIM median ≥ 0.98 (ffmpeg's `psnr` and `ssim` filters, frames paired by index);
4. **the corners: reported, not a criterion,** per corner, beside the original's own frame-to-frame jitter on `static-tripod`.

Why: on `static-tripod`'s original, a still clip, `segment.py`'s bottom-right corner moves by up to about 8 px between
consecutive frames (p99), and the encode-against-original corner differences barely moved from CRF 18 to CRF 12. The
criterion measured `segment.py`'s instability on this footage, not what re-encoding loses. The ruling concerns the encode's
fidelity only. The `calib-chessboard` criteria were kept; since CRF 18 had passed with a wide margin, the same ruling asked for
CRF 20 and 22 to be tried as well and the highest passing one kept, to leave room under the size limit: CRF 22 (24 was not
tried).

### The tries that led to the ruling (first corner criterion)

Per-frame difference = the largest of the four corner distances; OpenCV 5.0.0. Timestamps identical in every try. These
figures come from a first version of the comparison script, which reported that per-frame maximum; the committed
`verify_encode.py` reports each corner instead (the tables below), from which the same maximum can be taken.

| clip | CRF | bytes | acceptance differs (limit) | corners median / p99 (px) | first criterion |
|---|---|---|---|---|---|
| `static-tripod` | 18 | 5,316,300 | 0 (4) | 0.76 / 7.81 | fail |
| | 16 | 7,202,329 | 0 | 0.76 / 8.31 | fail |
| | 14 | 9,698,181 | 0 | 0.60 / 8.04 | fail |
| | 12 | 12,825,900 | 0 | 0.63 / 7.45 | fail |
| `fast` | 18 | 10,299,957 | 2 (8) | 1.82 / 14.30 | fail |
| | 16 | 14,578,280 | 3 | 1.65 / 14.74 | fail |
| | 14 | 20,566,764 | 2 | 1.41 / 13.77 | fail |
| | 12 | 28,165,504 | 3 | 1.33 / 12.82 | fail |

### Results under the criteria as they stand

| clip | CRF | frames, timestamps | acceptance (orig / encode, differs, limit) | luma PSNR median / min | SSIM median (min) | result |
|---|---|---|---|---|---|---|
| `static-tripod` | 18 | 414 = 414, identical | 414 / 414, 0, 4 | 45.54 / 44.31 dB | 0.9947 (0.9933) | pass |
| `fast` | 18 | 898 = 898, identical | 879 / 879, 0, 8 | 47.24 / 45.35 dB | 0.9937 (0.9851) | pass |

| `calib-chessboard` | CRF | bytes | found (orig / encode, same frames) | \|Δfx\| | \|Δfy\| | \|Δcx\| | \|Δcy\| | \|ΔRMS\| | result |
|---|---|---|---|---|---|---|---|---|---|
| | 18 | 23,782,903 | 338 / 338, yes | 0.07 | 0.08 | 0.04 | 0.04 | 0.0005 | pass |
| | 20 | 17,581,805 | 338 / 338, yes | 0.01 | 0.01 | 0.06 | 0.03 | 0.0019 | pass |
| | **22** | 13,061,396 | 338 / 338, yes | 0.21 | 0.20 | 0.07 | 0.03 | 0.0024 | **pass, kept** |

338 of 338 sampled frames (every 5th); calibration from the original: RMS 0.505 px, fx 1041.6, fy 1041.5, cx 655.0, cy 373.7 px
(a check of the encode only; the camera calibration itself is #10). CRF 18 was measured with OpenCV 5.0.0, CRF 20 and 22 with 5.1.0.

### Corners, reported (not a criterion)

Encode against original, on frames both accept (px at 1280×720):

| clip | frames | TL median / p99 | TR median / p99 | BR median / p99 | BL median / p99 |
|---|---|---|---|---|---|
| `static-tripod` | 414 | 0.10 / 0.46 | 0.07 / 0.29 | 0.71 / 7.28 | 0.32 / 2.03 |
| `fast` | 879 | 0.18 / 4.19 | 0.10 / 0.39 | 1.34 / 11.68 | 0.82 / 13.71 |

### `segment.py`'s noise floor on this session's footage

The original `static-tripod.mp4`'s own frame-to-frame corner movement (consecutive frames both accepted; the camera does not
move: the largest frame-to-frame image shift is 0.5 px), per corner, px at 1280×720:

| pairs | TL median / p99 | TR median / p99 | BR median / p99 | BL median / p99 |
|---|---|---|---|---|
| 413 | 0.34 / 1.28 | 0.25 / 1.20 | 1.29 / 8.16 | 0.57 / 2.28 |

### Sharpness, reported (not a criterion)

`scripts/verify_encode.py` (added 2026-11-27, after the maintainer asked for an explanation of the quality check's sharpness
drop on `fast`): the sharpness of the encode divided by the original's, the variance of the Laplacian inside the original's
segmented poster (`nftbench.quality.sharpness`, as in `check_recording.py quality`), on every third frame the original
accepts. At full size and at 480×270, the processing size webarkit's bench uses for 1280×720 clips (`cv2.INTER_AREA`, the
quad scaled with the frame). The last two columns: share of those frames with sharpness ≥ 60 (`SHARPNESS_MIN`) at 1280×720.

| clip | frames | ratio at 1280×720: median / p10 / p90 | ratio at 480×270: median / p10 / p90 | sharp, original | sharp, encode |
|---|---|---|---|---|---|
| `static-tripod` | 138 | 0.923 / 0.892 / 0.976 | 0.994 / 0.986 / 1.000 | 100% | 100% |
| `fast` | 293 | 0.742 / 0.675 / 0.885 | 0.994 / 0.975 / 1.014 | 40% | 6% |

`check_recording.py quality`, which analyses every second frame and counts a frame it cannot segment as not sharp, reports
`fast`'s sharp share as 40% on the original and 11% on the encode; `static-tripod` stays at 100%.

## Checks on the committed files

From this branch, based on `dev` at PR #25's merge commit `5f2fa0f1d5e9544742e4e24b630089a15aec221a`:

```
$ <venv-python> scripts/check_recording.py videos data/videos/tab9-2026-11-26
ok    calib-chessboard.mp4: 1280x720 30.01 fps, 1686 frames, 56.2 s
ok    fast.mp4: 1280x720 30.01 fps, 898 frames, 29.9 s
ok    static-tripod.mp4: 1280x720 30.01 fps, 414 frames, 13.8 s

$ <venv-python> scripts/check_recording.py quality data/videos/tab9-2026-11-26
ok    calib-chessboard.mp4: found 338, cells 9/9, tilted 64%
ok    fast.mp4: ground truth 98%, sharp 11%, KPM not checked (pass --marker/--dpi)
ok    static-tripod.mp4: ground truth 100%, sharp 100%, KPM not checked (pass --marker/--dpi)
```

`fast` is exempt from the sharpness rule (motion blur is what it tests). KPM was not checked: the 327 dpi dataset does not
exist yet. ffprobe shows no audio stream, no rotation or location tag and no device tag in any committed file.

## Limits

* Focus (Continuous) and exposure were not locked, although the guide asks for both locked if possible: focus and exposure
  may have changed within and between clips. A calibration from `calib-chessboard.mp4` therefore holds for the other clips
  only as far as the continuous focus kept the same focal distance; stabilisation was off and the zoom 1× throughout.
* The encode removes fine detail at 1280×720 (median Laplacian-variance ratio 0.74 inside the poster on `fast`, mostly sensor
  grain), but not at 480×270, webarkit's bench processing size (0.99); `segment.py`'s acceptance and the calibration are
  unchanged. The quality check's sharpness share for `fast` drops from 40% to 11% for that reason; `fast` is exempt from that
  rule.
* The camera calibration is not computed here (#10); the calibrations above only compare the encode with its original.
* Only three of the guide's clips; no photos.
* The originals carry contradictory colour tags (see above); the committed files declare what decoders actually use.
