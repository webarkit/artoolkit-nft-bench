# Contributing to artoolkit-nft-bench

Thanks for helping. This repository benchmarks ARToolKit-family NFT engines (native artoolkit5, the same code in WASM,
jsartoolkitNFT) on identical inputs. Read the [design spec](docs/superpowers/specs/2026-10-03-artoolkit-nft-bench-design.md)
and the [ADRs](docs/adr/) before larger changes.

## Pull request workflow

1. Start from an up-to-date `dev`:
   ```bash
   git checkout dev
   git pull origin dev
   ```
2. Create one branch per task or issue, named `type/short-description` (e.g. `feat/wasm-runner`, `docs/spec-update`).
3. Run the checks below.
4. Open the pull request **against `dev`**. `main` is reserved for stable releases; the release pull request is the only one
   that goes from `dev` into `main`.

## Commit messages and PR titles

[Conventional Commits](https://www.conventionalcommits.org/): `type(scope): summary`, imperative and concise.

* **Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`.
* **Scopes:** `native`, `wasm`, `jsartoolkitnft`, `frames` (frame banks and ground truth), `scorer`, `markers`, `runner`,
  `docs`, `ci`. Omit the scope for repository-wide changes.
* Breaking changes: `!` after type/scope, or a `BREAKING CHANGE:` footer.

Examples: `feat(runner): add native nft_run`, `fix(scorer): exclude frames without ground truth`, `docs: update README`.

Every repository artifact (code, comments, commits, PR titles and bodies, issues, docs) is written in English.

## Before opening a pull request

```bash
python -m venv .venv
.venv/Scripts/python -m pip install --use-feature=truststore -r requirements-dev.txt
.venv/Scripts/python -m pip install --use-feature=truststore --no-build-isolation -e .
cmake -S . -B build/win-vs2022 -G "Visual Studio 17 2022" -A x64
cmake --build build/win-vs2022 --config Release
ctest --test-dir build/win-vs2022 -C Release
.venv/Scripts/python -m pytest python/tests -q
```

Do not claim a change is verified without running them. `AGENTS.md` keeps the authoritative command list.

## Benchmark results

* Development runs write to `results/local/` (git-ignored). Results are published only when they support a written conclusion,
  through the publish script, to `webarkit/artoolkit-nft-bench-results`; `results/manifest.json` indexes them
  ([ADR-0001](docs/adr/0001-results-storage.md)). Never commit raw results, decoded frame banks (`banks/`) or build trees here.
* Every published number carries its configuration header (engine and version, build flags, threads, dpi, camera, host).
* `extern/artoolkit5` is a pinned submodule and is never modified; fix portability in this repository's CMake.

## Sensitive data in published files

Allowed host fields, and only these: `host_label` (a name you choose, set in the git-ignored `bench.local.json`), `os`, `cpu`,
`cores`, `threads_hw`, `ram_gb`, `compiler`, `build_flags`, `runtime`.

Never allowed: host names, user names, emails, absolute paths (use repository-relative paths), environment variables, tokens or
keys, IP or MAC addresses, device serials (e.g. `adb` serials). Device *models* are fine. The publish script scrubs logs and
refuses to publish if any of these remains.

## License

LGPL-3.0-or-later. Every source file starts with the same LGPL header template as webarkit/webarkit (file name, project,
`SPDX-License-Identifier: LGPL-3.0-or-later`, the LGPL notice, `Copyright 2026 WebARKit.`, author). Add it with
`.venv/Scripts/python scripts/license_headers.py --fix`; `pytest` fails if a file lacks it.
