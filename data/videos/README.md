# Test clips

## pinball-bench.mp4

* Source: [webarkit/webarkit](https://github.com/webarkit/webarkit), `examples/videos/pinball-bench.mp4`, copied from commit
  `9e24dabe623acf5bc239cf85038a94ac32e7980c`. It is the clip the webarkit benchmarks call the "wall" clip, so native results can be set beside them.
* Content: real footage of the printed `pinball.jpg` poster on a wall, moving camera.
* Format: H.264, 1280x720, 298 frames, about 11.96 s (container frame rate 299/12, about 24.9 fps). Size about 0.9 MB.
* License: LGPL-3.0-or-later, as the source repository.
* Ground truth: none in the file. Poster corners are extracted per frame by `python/nftbench/segment.py`.
