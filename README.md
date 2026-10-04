# artoolkit-nft-bench

Benchmark of ARToolKit-family NFT engines on identical inputs: is the native ARToolKit5 C/C++ code faster, more responsive and
more precise than jsartoolkitNFT (WebARKitLib in WASM)? Engines are compared in the order native, same sources in WASM,
jsartoolkitNFT in Node, jsartoolkitNFT in Chromium. A secondary goal compares NFT markers from different generators.

* Design: [spec](docs/superpowers/specs/2026-10-03-artoolkit-nft-bench-design.md), [plans](docs/superpowers/plans/), [ADRs](docs/adr/).
* Contributing: [CONTRIBUTING.md](CONTRIBUTING.md); agents: [AGENTS.md](AGENTS.md).
* License: LGPL-3.0-or-later ([LICENSE](LICENSE), [COPYING](COPYING)).

## Layout

* `extern/artoolkit5` — git submodule ([webarkit/artoolkit5](https://github.com/webarkit/artoolkit5), pinned). **Never modified.**
* `CMakeLists.txt`, `cmake/` — builds `ARUtil`, `AR`, `ARICP`, `AR2`, `KPM` (static) and the upstream `genTexData` tool.
  Source lists come from the upstream `VisualStudio/vs2017/*.vcxproj` files; `config.h` is generated in the build tree.
  GL / GLUT / video / OSG / examples are not built.
* `native/` — synthetic bank exporter (`nft_export`), native runner (`nft_run`), unit tests. `python/nftbench/` — schemas and scorer.
* `data/markers/` — `pinball.jpg` (from upstream `doc/Marker images`) and the NFT dataset generated from it.
* `tools/docker_build.sh` — Linux/gcc cross-check inside an `ubuntu:24.04` container.

## Build (Windows, MSVC 2022)

```bash
git submodule update --init
cmake -S . -B build/win-vs2022 -G "Visual Studio 17 2022" -A x64      # fetches zlib + libjpeg-turbo
cmake --build build/win-vs2022 --config Release
```

`ARX_FETCH_DEPS=OFF` uses system zlib/libjpeg instead (Linux). On Windows, `ARUTIL_DISABLE_PTHREADS` is defined so the
native Win32 threading path is used and pthreads-win32 is not needed.

## Generate an NFT dataset

```bash
scripts/make_marker.sh data/markers/pinball.jpg 220 30 220 2 1 data/markers/pinball-d220-l2-i1
```

Arguments: image, dpi, min dpi, max dpi, level, leveli, output directory (named after the parameters).

## Run a benchmark

```bash
B=build/win-vs2022/native/Release
$B/nft_export.exe out=banks/synthetic-d220 image=data/markers/pinball.jpg dpi=220 dataset=pinball-d220-l2-i1
$B/nft_run.exe bank=banks/synthetic-d220 dataset=data/markers/pinball-d220-l2-i1/pinball dpi=220     out=results/local/native.json threads=1 repeats=5
.venv/Scripts/python -m nftbench.score --bank banks/synthetic-d220 --result results/local/native.json
```

`dpi` must be the value passed to `genTexData -dpi=` (it fixes the marker's physical size, in which poses are expressed);
`nft_run` refuses a bank rendered for another dpi, and the scorer refuses a result whose marker or camera differ from the bank.

### What it measures

Frames are rendered from the marker image with a known pose (pinhole camera, 640x480, fovy 45°, mip-mapped + 2x2 supersampled,
random smooth background). `found` = KPM returned a pose; `ok` = found **and** mean 2D corner reprojection error < `ok_px` (5 px).
Detection sweeps one nuisance at a time (distance, tilt, in-plane roll, blur, noise, illumination, occlusion) with the others
jittered around a nominal pose. Tracking runs KPM init + `ar2Tracking` on sequences with increasing motion speed (with motion blur).

### Limits of this evaluation

Synthetic frames are rendered from the very image the dataset was built from, with no lens distortion, rolling shutter, colour
or JPEG artefacts. Treat the numbers as an **upper bound** and as a regression/comparison baseline between builds, not as an
absolute field-performance figure. Real footage (no ground truth) is the next step.

## Results so far (pinball.jpg, 640x480, 10 trials/level; synthetic ground truth)

Full tables: `results/win-msvc/pinball_full.txt` (Windows, MSVC 2022) and `results/linux-gcc/pinball_full.txt` (Ubuntu 24.04, gcc 13).

* Detection is reliable up to ~4x the "marker fills 80% of frame height" distance, tilt ≤ 55°, any in-plane roll, noise σ ≤ 30,
  illumination down to 25% contrast, blur σ ≤ 3 px, and ≤ 40% occlusion. Median corner error is 0.2–0.5 px when it works.
* Tracking (KPM init + AR2) holds 100% of frames up to 20 px/frame; at 35 px/frame (with motion blur) it fails.
* Windows and Linux agree to within the 10-trial noise. `genTexData` output is **byte-identical** across platforms for
  `.iset` and `.fset`; `.fset3` (FREAK) differs bit-wise (floating-point differences) but is interchangeable for matching.
* One KPM detection takes ~30–70 ms at 640x480 (single thread); one `ar2Tracking` call ~1.2 ms.
