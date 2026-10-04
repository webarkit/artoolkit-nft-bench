# AGENTS.md — artoolkit-nft-bench

> Canonical instructions for AI coding agents (Claude Code, GitHub Copilot, Gemini, Antigravity, Codex, Cursor, ...).
> This is the **single source of truth**; `CLAUDE.md`, `GEMINI.md`, `.agents/instructions.md` and `.github/copilot-instructions.md`
> point here. Change rules here (and in `CONTRIBUTING.md`), never only in a pointer file.

## What this project is

A benchmark answering: is the native ARToolKit5 C/C++ NFT code faster, more responsive and more precise than jsartoolkitNFT
(WebARKitLib in WASM)? Engines are compared in order `native` -> `wasm-same-src` -> `jsartoolkitnft-node` -> `jsartoolkitnft-browser`.
It contains no tracker of its own and is unrelated to the `nft-tracker` package of `webarkit/webarkit`.
Read the [spec](docs/superpowers/specs/2026-10-03-artoolkit-nft-bench-design.md), the current
[plan](docs/superpowers/plans/) and the [ADRs](docs/adr/).

## Layout

* `extern/artoolkit5` — webarkit fork of artoolkit5, pinned submodule. **Never modify it.**
* `CMakeLists.txt`, `cmake/` — builds the NFT libraries (`ARUtil`, `AR`, `ARICP`, `AR2`, `KPM`) and `genTexData`.
* `native/` — synthetic frame exporter and native runner. `python/nftbench/` — schemas, scorer, video bank, segmentation.
* `data/markers/<name>-d<dpi>-l<level>-i<leveli>/` — NFT datasets; `data/videos/` — the test clip with provenance.
* `banks/` (git-ignored) — decoded frame banks. `results/local/` (git-ignored) — development results.
* `docs/adr/`, `docs/superpowers/specs/`, `docs/superpowers/plans/` — design records.

## Commands

```bash
git submodule update --init
cmake -S . -B build/win-vs2022 -G "Visual Studio 17 2022" -A x64
cmake --build build/win-vs2022 --config Release
python -m venv .venv
.venv/Scripts/python -m pip install --use-feature=truststore -r requirements-dev.txt
.venv/Scripts/python -m pip install --use-feature=truststore --no-build-isolation -e .
ctest --test-dir build/win-vs2022 -C Release
.venv/Scripts/python -m pytest -q          # needs the native build: it drives nft_export / nft_run
scripts/run_phase1.sh                       # phase 1 measurements -> results/local/phase1/ (long)
```

This list is the authoritative one, kept in sync with `CONTRIBUTING.md`.
Do not claim a change is verified without running these.

## Hard rules

* Never modify `extern/artoolkit5` or any other upstream submodule; fix portability in this repo's CMake.
* Every published number carries its configuration header (engine and version, build flags, threads, dpi, camera, host). A result
  without it is not committed or published.
* Results storage follows [ADR-0001](docs/adr/0001-results-storage.md): development results in `results/local/`; publications go to
  `webarkit/artoolkit-nft-bench-results`, indexed by `results/manifest.json`. Do not commit build trees, `banks/`, raw results,
  CSV/log output, `.venv` or `node_modules`.
* **Sensitive data:** host fields in results are only `host_label`, `os`, `cpu`, `cores`, `threads_hw`, `ram_gb`, `compiler`,
  `build_flags`, `runtime`. Never host names, user names, emails, absolute paths, environment variables, tokens, IP/MAC
  addresses or device serials.
* Do not describe sibling projects (jsartoolkitNFT, WebARKitLib, webarkitlib-rs, ARnft) from memory; check the repository first
  (`gh repo view`, `gh api repos/<owner>/<repo>/readme`).
* Do not copy code from projects with incompatible licences (e.g. WOFT, CC BY-NC-SA) into this LGPL repository.
* Every source file carries the LGPL header template used across webarkit (file name, project, SPDX `LGPL-3.0-or-later`, LGPL notice,
  `Copyright 2026 WebARKit.`, author). Run `.venv/Scripts/python scripts/license_headers.py --fix` after adding files; the check
  also runs inside `pytest`. Claude Code has the same procedure as the `license-header` skill in `.claude/skills/`.
* An accepted ADR's decision is never edited in place; supersede it with a new ADR.
* Every PR and issue is assigned to the milestone of its phase (`M<n> — <phase name>`). Releases follow
  [ADR-0002](docs/adr/0002-milestones-and-releases.md): the release is the last step of a milestone, and behaviour or result
  changes add a line under `[Unreleased]` in `CHANGELOG.md`.

## Git and contribution workflow

See [CONTRIBUTING.md](CONTRIBUTING.md). In short: branch `type/short-description` from an up-to-date `dev`; PRs target **`dev`**,
never `main` (this repo's release branch is `main`; `webarkit/webarkit` calls its release branch `master` — copy the workflow,
not the name). Conventional Commits with scopes `native`, `wasm`, `jsartoolkitnft`, `frames`, `scorer`, `markers`, `runner`, `docs`,
`ci`. Every repository artifact is in English, whatever language the conversation uses.
