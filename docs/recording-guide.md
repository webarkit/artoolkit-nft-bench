# Recording guide

How to record benchmark footage, the calibration video and still photos so that they can be measured: same camera settings
throughout, a flat marker of known size, and a calibrated camera. Do everything in **one session**, without changing any setting
between the calibration video and the footage: a calibration only describes the camera mode it was recorded in.

Tracked in [#13](https://github.com/webarkit/artoolkit-nft-bench/issues/13); the material feeds camera calibration
([#10](https://github.com/webarkit/artoolkit-nft-bench/issues/10)), manual annotations
([#11](https://github.com/webarkit/artoolkit-nft-bench/issues/11)) and the static photo bank
([#12](https://github.com/webarkit/artoolkit-nft-bench/issues/12)).

## 1. Before the session

### The marker (the print you have)

* Any print of `data/markers/pinball.jpg` works; there is no need for a particular size. What matters is that it is **flat**
  and that its size is **known**.
* Glue it on a rigid board (foam board or thick cardboard), with no bubbles or curled corners. A bent corner shows up as
  several pixels of error (phase 1's real clip had one).
* Measure the **image area** (not the sheet, not any white border) with a ruler, to half a millimetre: width and height.
* Compute the effective dpi and the marker to generate:

  ```bash
  <venv-python> scripts/check_recording.py dpi --mm <width_mm> <height_mm>
  ```

  It refuses measurements that disagree by more than 2% (re-measure) and prints the `make_marker.sh` command. Example: a
  12.8 × 15.9 cm print gives 326 dpi and `data/markers/pinball-d326-l2-i1`.
* Prints without a white border are best: the paper corners are the image corners, which is what the segmentation finds.

### The calibration chessboard

```bash
<venv-python> scripts/make_chessboard.py     # writes results/local/print/chessboard-9x6-25mm.pdf (git-ignored)
```

* Print at **100% / "actual size"** — never "fit to page". Check the 100 mm ruler printed under the board, then measure one
  square: if it is not 25.0 mm, write down the real value.
* Glue it on a rigid board as well. A wavy chessboard gives a wrong calibration without any warning.

### The tablet (camera app settings)

Use the same app and the same settings for everything; write them down (or take a screenshot of the settings screen).

| setting | value | why |
|---|---|---|
| resolution | 1280×720 (16:9) | the benchmark resolution; photo and video modes crop the sensor differently |
| frame rate | 30 fps, constant | timing metrics assume it; `check_recording.py` flags variable frame rates |
| **video stabilisation** | **off** | it moves and crops each frame, changing the camera model frame by frame |
| HDR, beauty, scene modes | off | they alter the image non-uniformly |
| focus | locked (tap and hold), if the app allows it | refocusing changes the focal length slightly |
| exposure | locked, if the app allows it | avoids flicker between frames |
| zoom | 1×, never touched | any zoom invalidates the calibration |
| location / geotagging | **off** | location ends up in the file's metadata |

### The scene

* A plain, matte wall or table around the marker, contrasting with it; diffuse light, no reflections on the print.
* Keep the whole marker inside the frame unless a sequence asks otherwise: frames where it touches the border get no ground
  truth.

## 2. The session

Record in this order, without changing settings. Each clip starts and ends with the whole marker visible.

| # | file name | content | length |
|---|---|---|---|
| 1 | `calib-chessboard.mp4` | the chessboard filling the frame at different distances and angles (up to ~45°), slowly, covering the corners and edges of the image too | 45–60 s |
| 2 | `static-tripod.mp4` | marker still, tablet on a tripod or propped up, not touched | 10 s |
| 3 | `approach.mp4` | slow approach and retreat, from ~4× to ~1× the distance where the marker fills the frame height | 15 s |
| 4 | `tilt.mp4` | progressive tilt up to 60–70°, both directions | 15 s |
| 5 | `roll.mp4` | rotation in the image plane, a full turn | 15 s |
| 6 | `fast.mp4` | quick movements | 10 s |
| 7 | `occlusion.mp4` | a hand partially covering the marker, never more than half | 10 s |
| 8 | `low-light.mp4` | the same scene with reduced light | 10 s |
| 9 | `photo-01.jpg` … `photo-10.jpg` | still photos from different positions and angles, **with the same camera mode as the videos** (or frames grabbed from a video) | — |

Slow, smooth movements beat fast ones for everything except `fast.mp4`: motion blur is a separate test.

## 3. After the session

1. Copy the files into `data/videos/tab9-<yyyy-mm-dd>/` with the names above.
2. Check them:

   ```bash
   <venv-python> scripts/check_recording.py videos data/videos/tab9-<yyyy-mm-dd>
   ```

   It reports resolution, frame rate, variable frame rate, duration and **personal metadata** (location, device make and
   model, author). Strip metadata before committing:

   ```bash
   ffmpeg -i in.mp4 -map_metadata -1 -c copy out.mp4
   ```

3. Add a `README.md` in the session directory: device and app, the settings table above as used, marker print size and the dpi
   computed, chessboard square size as measured, date, and anything unusual (light changes, a frame where the marker left the
   view). Add the session to `data/videos/README.md`.
4. Size: keep each clip small (the existing clip is about 1 MB). Media stays in git history forever; if a session grows beyond
   a few tens of MB, discuss it before committing (see `data/AGENTS.md`).

## `<venv-python>`

`.venv/Scripts/python` on Windows, `.venv/bin/python` on Linux.
