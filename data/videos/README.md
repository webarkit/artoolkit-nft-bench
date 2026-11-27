# Test clips

## pinball-bench.mp4

* Source: [webarkit/webarkit](https://github.com/webarkit/webarkit), `examples/videos/pinball-bench.mp4`, copied from commit
  `9e24dabe623acf5bc239cf85038a94ac32e7980c`. It is the clip the webarkit benchmarks call the "wall" clip, so native results can be set beside them.
* Content: real footage of the printed `pinball.jpg` poster on a wall, moving camera.
* Format: H.264, 1280x720, 298 frames, about 11.96 s (container frame rate 299/12, about 24.9 fps). Size about 0.9 MB.
* License: LGPL-3.0-or-later, as the source repository.
* Ground truth: none in the file. Poster corners are extracted per frame by `python/nftbench/segment.py`.

## tab9-2026-11-26/

* Source: recorded by the maintainer on 2026-11-26 on the Tab 9 (Android 15) with Open Camera 1.56.2, 1280x720 at 30 fps,
  following [docs/recording-guide.md](../../docs/recording-guide.md): `fast.mp4` (29.9 s, 898 frames), `static-tripod.mp4`
  (13.8 s, 414 frames) and `calib-chessboard.mp4` (56.2 s, 1,686 frames, 9x6 chessboard with 25 mm squares). The poster print is
  127 x 159 mm (327 dpi), on a plain white wall.
* Format: H.264, 1280x720, the originals' timestamps kept, no audio and no metadata, re-encoded from the camera originals by
  `scripts/encode_session.sh` (CRF 18, 18 and 22; 28.7 MB together) and checked against them by `scripts/verify_encode.py`.
  The originals (SHA-256, sizes), settings, re-encode criteria and checks are in
  [tab9-2026-11-26/README.md](tab9-2026-11-26/README.md).
* License: LGPL-3.0-or-later, as this repository.
* Ground truth: none in the files. Poster corners are extracted per frame by `python/nftbench/segment.py`; the session README
  gives its frame-to-frame noise on `static-tripod.mp4`.
