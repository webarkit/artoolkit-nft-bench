# GitHub Copilot instructions — artoolkit-nft-bench

The full guidance is in **[`AGENTS.md`](../AGENTS.md)** (source of truth). Critical points, inlined because Copilot injects this file directly:

- Benchmark of ARToolKit-family NFT engines (native artoolkit5, same code in WASM, jsartoolkitNFT) on identical frame banks; no tracker of its own.
- `extern/artoolkit5` is a pinned submodule and is never modified.
- Build: `cmake -S . -B build/win-vs2022 -G "Visual Studio 17 2022" -A x64` then `cmake --build build/win-vs2022 --config Release`.
- Git workflow: branch from `dev`, PR against **`dev`**, never `main`. Conventional Commits with scopes `native`, `wasm`, `jsartoolkitnft`, `frames`, `scorer`, `markers`, `runner`, `docs`, `ci`.
- Results storage per `docs/adr/0001-results-storage.md`; never commit raw results, `banks/` or build trees.
- Sensitive data: only allow-listed host fields in results; never host names, user names, emails, absolute paths, env vars, tokens, IP/MAC, serials.
- License LGPL-3.0-or-later. Every repository artifact is in English.
