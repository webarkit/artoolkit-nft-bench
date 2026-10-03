# artoolkit-nft-bench — design

Status: draft for review · Date: 2026-10-03

## 1. Goal

Answer one question with reproducible numbers:

> Is the native application built from the ARToolKit5 C/C++ NFT code faster, more responsive and more
> precise than the same functionality delivered by **jsartoolkitNFT** (WebARKitLib compiled to WASM)?

Secondary goal: compare NFT markers produced by different generators (`genTexData`, NFT-Marker-Creator-App,
`webarkit-nft-forge-rs`) in terms of content and of the detection/tracking quality they give.

Success = a single command per engine produces a result file in a common schema, and one scorer turns any set of
result files into the same set of tables, with the fairness protocol (section 6) documented next to every number.

### Non-goals

* Not a tracker implementation. This repo contains no tracking algorithm of its own, and is unrelated to the
  `nft-tracker` package of `webarkit/webarkit` (TypeScript, jsfeatNext-based). That name is deliberately avoided.
* No GL / video capture / UI. Everything is frame-in, pose-out.
* No absolute "field performance" claims: benchmarks compare engines on identical inputs.

## 2. Engines under test

Compared in this order, because each step changes one thing:

| id | engine | what it isolates |
|---|---|---|
| `native` | webarkit fork of artoolkit5 @ pinned commit, built with the CMake in this repo (MSVC, and gcc in Docker) | baseline |
| `wasm-same-src` | **the same artoolkit5 sources** compiled to WASM with Emscripten (Node and browser) | the effect of compilation target (native vs WASM) |
| `jsartoolkitnft-node` | `@webarkit/jsartoolkit-nft` Node build (`dist/ARToolkitNFT_node.js`), npm version pinned | code differences (WebARKitLib vs artoolkit5 fork) + packaging |
| `jsartoolkitnft-browser` | same package in Chromium via Playwright | real deployment conditions (workers, no threads) |

`native` vs `wasm-same-src` answers "what does WASM cost". `wasm-same-src` vs `jsartoolkitnft-*` answers "what do the code
and packaging differences cost". Optional later: ARnft (end-to-end browser, same engine underneath), `webarkitlib-rs`.

## 3. Inputs

### 3.1 Frame banks (decoded once, shared by every engine)

All engines read the same pre-decoded grey/RGBA frames, so video decoding never differs between them.

1. **Synthetic with exact ground truth** — the existing `tests/nft_eval.cpp` generator, extended to *export* frames
   plus the true pose per frame. Scenarios: scale, tilt, roll, blur, noise, illumination, occlusion, motion speed.
2. **Real footage** — `pinball-bench.mp4` from `webarkit/webarkit` (real, 1280x720, 298 frames @ ~24.9 fps, printed
   poster on a wall, moving camera). Ground truth is *approximate*: the four corners of the printed poster are extracted
   per frame by classical segmentation (threshold, largest quadrilateral contour, sub-pixel corner refinement),
   independent of any NFT code. Frames where the quad is truncated or segmentation confidence is low are excluded and
   reported. A random sample is checked by eye and the exclusion/agreement rate is published with the results.
3. **Optional, public** — a subset of POT-210 (planar object tracking, 1280x720, ground-truth homographies, 30 objects).
   Needs downloading the dataset (user approval required) and generating a marker per reference image. Not on the critical path.
   `pinball.jpg` does not appear in it.

Metrics against the real-footage ground truth are 2D corner distances in pixels, so they do not depend on the unknown
camera intrinsics (each engine gets the same assumed pinhole camera, fovy 45 deg unless stated).

### 3.2 Markers

* Primary: `genTexData` output from this repo. **Resolution parameter:** the canonical `pinball.jpg` is 220 dpi
  (189.0 x 236.5 mm printed); earlier synthetic runs used 150 dpi (277 x 347 mm). The bench standardises on one value per
  run, records it in the result header, and reruns the synthetic suite at 220 dpi so the numbers match the canonical size.
* Secondary (generator comparison, section 7): NFT-Marker-Creator-App, `webarkit-nft-forge-rs` (pure Rust), each with
  the same `dpi`, `level`, `leveli` and DPI range.

## 4. Runner contract

Each engine has a thin runner that takes `--marker <path-without-ext> --frames <dir> --out result.json` plus the shared
camera/parameter set, and writes one JSON document:

```
{ "header": { engine, engine_version, build_flags, host, marker, dpi, camera, params, threads },
  "frames": [ { "i", "state": "lost|detected|tracked", "pose": [12 floats] | null,
                "t_detect_ms", "t_track_ms", "t_total_ms", "blocked_ms" } ],
  "init": { "load_marker_ms", "startup_ms" } }
```

The scorer (Python, no engine dependencies) consumes only these files plus the ground truth, so adding an engine means
writing one runner. `nft_eval` becomes the `native` runner and the synthetic-frame exporter.

## 5. Metrics

* **Speed:** per-phase ms (KPM detect, AR2 track), total ms per frame; p50 / p95 / max; warm-up discarded; marker load
  and startup reported separately.
* **Reactivity:** frame-to-pose latency (p95/max); frames until first lock; share of frames with a valid pose; number of loss
  events; **blocked time** — wall time during which the engine could not accept the next frame (synchronous detection in
  `process()` vs detection in a background thread).
* **Precision:** mean corner reprojection error (px), translation (mm) and rotation (deg) error on synthetic frames; corner
  error against the segmentation ground truth on real footage; jitter (second difference of pose) on both.
* **Webarkit alignment:** report the same `TRACK` share and `trackTimeShare` that `webarkit/webarkit` benchmarks use, so numbers
  can be set beside its device baselines.

## 6. Fairness protocol

* Same frames, same marker files, same camera, same KPM proc mode and AR2 thresholds.
* Native is reported at 1 thread (like-for-like with WASM), at default threads, and with detection in a background thread (as
  `nftSimple` does). Whether KPM itself can use more than one thread is to be verified, not assumed.
* Build parity is documented: native `/O2` / `-O3`; WASM optimisation level and SIMD flag; Node and Chromium versions.
* Several repetitions per configuration, median across repetitions, spread reported; machine idle, power plan fixed.
* Differences in source code between artoolkit5 fork and WebARKitLib are listed, not hidden, wherever they can explain a result.

## 7. Marker-generator comparison

* **File level:** `.iset` / `.fset` byte comparison (already identical across Windows and Linux for `genTexData`); `.fset3` loaded
  through the KPM API and compared statistically — features per level, spatial and scale distribution, fraction of points that match
  within a tolerance. Forge is a pure-Rust reimplementation, so identical output is **not** expected and not required.
* **Functional level:** same engine, same frames, only the marker changes; the delta in detection rate, time-to-lock and precision
  is the generator's effect.
* `genTexData` native vs NFT-Marker-Creator-App is expected to be near-identical (believed to be a WASM build of the same tool; to be verified).

## 8. Phases

1. **Repo and baseline.** Rename/organise, license, README, contributor and agent files (section 11); export synthetic frames; frame bank from `pinball-bench.mp4`;
   corner segmentation + manual spot check; `native` runner on both banks at 220 dpi. Output: first results table.
2. **WASM control.** Build the same sources with Emscripten (`emsdk` image already present); `wasm-same-src` runner in Node and browser.
3. **jsartoolkitNFT.** Node and Chromium runners; comparison tables engine by engine.
4. **Generators.** `fset3` comparison tool; Marker-Creator-App and Forge markers through the `native` runner.
5. **Optional.** POT-210 subset, ARnft, `webarkitlib-rs`.

Each phase ends with committed result files and a short written reading of them.

## 9. Risks and open questions

* Segmentation ground truth may fail on blur or when the poster leaves the frame; mitigated by exclusion, manual sampling, and the
  synthetic bank which has exact truth.
* WebARKitLib diverges from the artoolkit5 fork, so a gap between `wasm-same-src` and jsartoolkitNFT may be code, not compilation. That
  is why the control exists.
* Browser runs are less deterministic than Node; they are reported with spread and are not used for precision claims.
* Whether the Emscripten build of the artoolkit5 sources works unmodified (threads, file loading) is unverified.

## 10. Repository

Name: **`artoolkit-nft-bench`**, owner `webarkit`, private for now (nothing is pushed until the spec is approved and the push is confirmed). Branches: `main` for stable releases, `dev` as the integration branch (section 11). License: LGPL-3.0-or-later, consistent
with artoolkit5 and the webarkit organisation, since the harness links LGPL code. The artoolkit5 fork stays a submodule, never
modified. Committed: sources, markers, the 1 MB test clip (with provenance), result summaries. Not committed: build trees, decoded frame
banks, raw CSV logs.

## 11. Contributor and agent documentation

The repo ships the same set of guidance files as `webarkit/webarkit`, so humans and coding agents (Claude Code, GitHub Copilot,
Gemini, Antigravity, Codex, Cursor, ...) get identical rules. One file is the source of truth; the others are thin pointers, so
rules are written once and cannot drift.

| File | Role |
|---|---|
| `CONTRIBUTING.md` | Human-facing workflow: pull requests, branches, conventional commits, what to run before opening a PR, benchmark-result rules. |
| `AGENTS.md` | **Canonical agent instructions** (read natively by Codex, Cursor and others): project purpose, layout, build/run commands, hard rules (below). Links to `CONTRIBUTING.md` rather than copying it. |
| `CLAUDE.md` | Imports `AGENTS.md` (`@AGENTS.md`), then a short Claude-specific section (Windows shell notes; never round-trip source files through PowerShell `Get-Content`/`Set-Content`, which corrupts encoding). |
| `GEMINI.md` | Points to `AGENTS.md` (with an `@AGENTS.md` import where the Gemini CLI supports it) plus the critical rules inlined. |
| `.github/copilot-instructions.md` | Copilot injects this file directly, so the critical rules are inlined here and it links to `AGENTS.md` for the rest. |
| `.agents/instructions.md` | Pointer for Antigravity, matching the org layout. |
| `.github/pull_request_template.md` | Reminds the author of the target branch, the PR-title format and the pre-PR checklist. |

Any change to the rules is made in `AGENTS.md` / `CONTRIBUTING.md` only. Pointer files may inline the critical rules but never add new ones.

### Workflow rules (stated in `CONTRIBUTING.md`, summarised in every agent file)

* **Pull requests target `dev`, never `main`.** `main` is for stable releases only; the release PR is the single PR from `dev` into `main`.
  One branch per task or issue, created from an up-to-date `dev`, named `type/short-description` (e.g. `feat/wasm-runner`, `docs/spec-update`).
* **Conventional Commits** for both commit messages and PR titles: `type(scope): summary`, imperative and concise. Types: `feat`, `fix`,
  `docs`, `refactor`, `test`, `chore`, `ci`. Breaking changes use `!` after the type/scope or a `BREAKING CHANGE:` footer.
  Scopes: `native`, `wasm`, `jsartoolkitnft`, `frames` (frame banks and ground truth), `scorer`, `markers`, `runner`, `docs`, `ci`;
  omit the scope for repo-wide changes.
* **Language:** every repository artifact (code, comments, commits, PR titles and bodies, issues, docs) is in English, whatever language
  the conversation with the agent uses.
* **Verification before claiming done:** run the commands listed in `AGENTS.md` (CMake configure and build, the native smoke test, the
  scorer on a committed sample result). Do not claim a change is verified without running them.
* The repository's default branch is `main`, matching `webarkit/jsfeatNext` and `webarkit/purecv`. (`webarkit/webarkit` uses `master`;
  the agent files say so to prevent copying the wrong name.)

### Hard rules for agents (in `AGENTS.md`)

* **Never modify `extern/artoolkit5`** (a submodule pinned to a commit) or any other upstream submodule; fix portability problems in
  this repo's CMake instead, as already done for `<limits>` and `_LARGEFILE64_SOURCE`.
* **Every published number carries its configuration header** (engine and version, build flags, threads, dpi, camera, host). A result
  without it is not committed.
* Do not commit build trees, decoded frame banks, raw CSV/log output, `.venv` or `node_modules`. Committed media is limited to small,
  reproducible clips with recorded provenance.
* Do not describe the status of sibling projects (jsartoolkitNFT, WebARKitLib, `webarkitlib-rs`, ARnft) from memory; check the repository
  first (`gh repo view`, `gh api repos/<owner>/<repo>/readme`).
* Do not use or copy code from projects with incompatible licences (e.g. WOFT, CC BY-NC-SA) into this LGPL repository.
* New source files carry the LGPL-3.0-or-later header used by the rest of the repo.

Open item: a CI check that PR titles follow Conventional Commits and that the pointer files still reference `AGENTS.md`. It is left to
review at first, as in `webarkit/webarkit`, and can be added once the repository has CI.

