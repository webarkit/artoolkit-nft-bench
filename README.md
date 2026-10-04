# artoolkit-nft-bench

Benchmark of ARToolKit-family NFT engines on identical inputs: is the native ARToolKit5 C/C++ code faster, more responsive and
more precise than jsartoolkitNFT (WebARKitLib in WASM)? Engines are compared in the order native, same sources in WASM,
jsartoolkitNFT in Node, jsartoolkitNFT in Chromium. A secondary goal compares NFT markers from different generators.

* Design: [spec](docs/superpowers/specs/2026-10-03-artoolkit-nft-bench-design.md), [plans](docs/superpowers/plans/), [ADRs](docs/adr/).
* Results: [phase 1 — native baseline](results/phase1/README.md).
* Contributing: [CONTRIBUTING.md](CONTRIBUTING.md); agents: [AGENTS.md](AGENTS.md).
* License: LGPL-3.0-or-later ([LICENSE](LICENSE), [COPYING](COPYING)).

## How it works

Engines never see ground truth. A **frame bank** (8-bit grey PNG frames + `bank.json`) is produced once, either synthetically
with the exact pose of every frame (`nft_export`) or from a real video, with the poster corners segmented as ground truth
(`python/nftbench`). Each engine has a **runner** that reads a bank and writes a `result.json`. The **scorer** reads only a bank
and result files and prints the tables, refusing results produced with a different marker or camera than the bank.

## Layout

* `extern/artoolkit5` — git submodule ([webarkit/artoolkit5](https://github.com/webarkit/artoolkit5), pinned). **Never modified.**
* `CMakeLists.txt`, `cmake/` — builds `ARUtil`, `AR`, `ARICP`, `AR2`, `KPM` (static) and the upstream `genTexData` tool. Source lists
  come from the upstream `VisualStudio/vs2017/*.vcxproj` files; `config.h` is generated in the build tree. GL / GLUT / video / OSG
  and the examples are not built.
* `native/` — synthetic bank exporter `nft_export`, native runner `nft_run`, unit tests.
* `python/nftbench/` — bank/result schemas, scorer, real-video bank builder, corner segmentation, results publisher.
* `data/markers/<name>-d<dpi>-l<level>-i<leveli>/` — NFT datasets; `data/videos/` — the test clip and its provenance.
* `scripts/` — `make_marker.sh`, `make_video_bank.py`, `segment_bank.py`, `run_phase1.sh`, `publish_results.py`, `license_headers.py`.
* `banks/`, `results/local/` — generated, git-ignored.

## Setup (Windows)

```bash
git submodule update --init
cmake -S . -B build/win-vs2022 -G "Visual Studio 17 2022" -A x64      # fetches zlib, libjpeg-turbo, nlohmann/json, stb
cmake --build build/win-vs2022 --config Release
python -m venv .venv
.venv/Scripts/python -m pip install --use-feature=truststore -r requirements-dev.txt
.venv/Scripts/python -m pip install --use-feature=truststore --no-build-isolation -e .
```

`--use-feature=truststore` makes pip use the Windows certificate store; drop it where Python's own CA bundle works. On Windows,
`ARUTIL_DISABLE_PTHREADS` is defined so the native Win32 threading path is used. Linux/gcc: `tools/docker_build.sh` in an
`ubuntu:24.04` container (`ARX_FETCH_DEPS=OFF` uses the system zlib/libjpeg).

## Tests

```bash
ctest --test-dir build/win-vs2022 -C Release
.venv/Scripts/python -m pytest -q
```

`pytest` drives the built `nft_export`/`nft_run` binaries and also checks the LGPL header of every source file.

## Reproduce phase 1

```bash
scripts/run_phase1.sh
```

It generates the marker if missing (`scripts/make_marker.sh data/markers/pinball.jpg 220 30 220 2 1 data/markers/pinball-d220-l2-i1`),
exports the synthetic bank, builds and segments the real-clip bank, and runs `nft_run` at 1 thread and at default threads
(`REPEATS=5` passes, the first discarded). Score with:

```bash
.venv/Scripts/python -m nftbench.score --bank banks/synthetic-d220 --result results/local/phase1/native-synthetic-d220-t1.json
.venv/Scripts/python -m nftbench.score --bank banks/pinball-bench --result results/local/phase1/native-pinball-bench-t1.json
```

`dpi` must be the value passed to `genTexData -dpi=` (it fixes the marker's physical size, in which poses are expressed).
`nft_run` writes only allow-listed host fields; set your machine label in a git-ignored `bench.local.json`
(`{"host_label": "desktop-1"}`).

## Publishing results

Raw results are published only when a written conclusion rests on them, to `webarkit/artoolkit-nft-bench-results`, with
`scripts/publish_results.py` (scrubs paths, refuses to publish host names, user names, emails, absolute paths, tokens, IP/MAC
addresses), indexed by `results/manifest.json`. See [ADR-0001](docs/adr/0001-results-storage.md).
