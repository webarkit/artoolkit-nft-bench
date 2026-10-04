# Agent instructions

The canonical instructions for this repository live in **[AGENTS.md](../AGENTS.md)**. Read it first.

@../AGENTS.md

Critical rules, inlined:

- Never modify the `extern/artoolkit5` submodule; fix portability in this repo's CMake.
- PRs target `dev`, never `main`. Conventional Commits (`type(scope): summary`). Everything in English.
- Results: development runs in `results/local/`; publications only via the publish script to `webarkit/artoolkit-nft-bench-results` (ADR-0001). No raw results, frame banks or build trees in this repo.
- Published files never contain host names, user names, emails, absolute paths, environment variables, tokens, IP/MAC addresses or device serials.
