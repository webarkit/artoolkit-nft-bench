# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project uses [Semantic Versioning](https://semver.org/). Each pull request that changes behaviour or results adds its own
line under `[Unreleased]`.

## [Unreleased]

## [0.2.0] - 2026-10-04

M2: project infrastructure.

### Added

- Linux build: CMake presets `windows-msvc` and `linux-gcc` (one `build/<preset>` convention, replacing `build/win-vs2022`),
  `nftbench.tools.find_tool` to locate native binaries on both platforms, Ubuntu/WSL setup in the README.
- CI (GitHub Actions): Linux build, `ctest` and `pytest` on every push and PR to `dev`/`main`; Windows (MSVC) on PRs to `main`,
  manual runs, and PRs to `dev` that change the build.
- Agent tooling: per-folder `AGENTS.md` in `native/`, `python/`, `data/`, `results/`; skills `run-benchmark`, `publish-results`,
  `new-engine-runner`; Claude Code hooks that block edits inside `extern/` and add the LGPL header to new sources.
- `publish_results.py`: updates the publications table of the results repository, and `--release` creates the immutable data
  release there.
- README rewritten for newcomers (results summary, diagram, three-command reproduction, roadmap); README of the results repository.

### Changed

- ADR-0002 accepted: one milestone per spec phase or declared work block, each closed by a release. Spec gains a Roadmap section.

### Fixed

- `license_headers.py` wrote CRLF line endings on Windows; it now keeps LF.
- Hooks called `python`, absent on stock Ubuntu; they now run through a launcher that uses `python3` or `python`.

## [0.1.0] - 2026-10-04

Phase 1: native baseline.

### Added

- Out-of-tree CMake build of the ARToolKit5 NFT libraries (`ARUtil`, `AR`, `ARICP`, `AR2`, `KPM`) and `genTexData` from the pinned
  webarkit fork (`extern/artoolkit5`, never modified), on Windows (MSVC 2022) and Linux (gcc 13, Docker).
- Frame-bank and result formats, and the `nftbench` scorer: detection and tracking rates, corner/pose error, loss events,
  time to lock, jitter, per-phase timings, `track_share` and `trackTimeShare`.
- `nft_export` (synthetic banks with exact ground truth) and `nft_run`, the native runner (synchronous KPM + AR2, as `nftSimple`).
- Real-clip bank from `pinball-bench.mp4` with automatic poster-corner segmentation as ground truth.
- First native results at 220 dpi ([results/phase1](results/phase1/README.md)); raw results published to
  `webarkit/artoolkit-nft-bench-results` and indexed in `results/manifest.json`.
- Results publisher with a sensitive-data scan; ADR-0001 (results storage).
- Contributor and agent guidance (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, Copilot, Antigravity), LGPL header checker and the
  `license-header` skill.

[Unreleased]: https://github.com/webarkit/artoolkit-nft-bench/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/webarkit/artoolkit-nft-bench/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/webarkit/artoolkit-nft-bench/releases/tag/v0.1.0
