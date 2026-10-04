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

## Milestones and releases

Each phase of the spec, or declared work block, is a GitHub milestone `M<n> — <name>`; assign every pull request and issue to its
milestone. The release is the last step of a milestone ([ADR-0002](docs/adr/0002-milestones-and-releases.md)): close the
`[Unreleased]` section of `CHANGELOG.md` in a PR into `dev`, open the release PR `dev` → `main` (merge commit), tag `vX.Y.Z`
(annotated) on its merge commit, create the GitHub Release with the changelog entry, then close the milestone. Before 1.0, each
milestone bumps the minor version. Pull requests that change behaviour or results add a line under `[Unreleased]`.

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
<venv-python> -m pip install --use-feature=truststore -r requirements-dev.txt
<venv-python> -m pip install --use-feature=truststore --no-build-isolation -e .
cmake --preset windows-msvc            # Linux: linux-gcc
cmake --build --preset windows-msvc
ctest --preset windows-msvc
<venv-python> -m pytest python/tests -q
```

`<venv-python>` is `.venv/Scripts/python` on Windows and `.venv/bin/python` on Linux. Presets: `windows-msvc` (Visual Studio 2022)
and `linux-gcc` (Ninja, system zlib/libjpeg: `apt install build-essential cmake ninja-build libjpeg-dev zlib1g-dev python3-venv`).
`--use-feature=truststore` is only needed where Python's CA bundle fails (it does on the maintainer's Windows machine).
CI (`.github/workflows/ci.yml`) runs the Linux sequence on every push and PR to `dev`/`main`, and Windows on PRs to `main`.

Do not claim a change is verified without running them. CI must be green before a PR is merged. `AGENTS.md` keeps the authoritative command list.

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
`<venv-python> scripts/license_headers.py --fix`; `pytest` fails if a file lacks it.
