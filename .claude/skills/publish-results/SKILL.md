---
name: publish-results
description: Publish raw results to webarkit/artoolkit-nft-bench-results following ADR-0001, with the sensitive-data scan, the publications table and results/manifest.json. Use when a milestone's results are final, or when asked to publish, archive or release benchmark data. Publishing is an outward action - always get the user's explicit confirmation first.
---

# publish-results

**Ask the user before running anything that pushes.** Publication pushes to a public repository and creates an immutable release;
neither can be undone.

## 1. Dry run (no side effects)

```bash
<venv-python> scripts/publish_results.py <name> --from results/local/<dir> --dry-run
```

It scrubs absolute repository paths and scans every file (also inside `.gz`) for host names, user names, emails, absolute paths,
tokens, IP and MAC addresses. Any hit aborts with file and line: fix the producer (runner, script) and regenerate, do not hand-edit.
Files that are not `.json .md .txt .log .csv` (optionally `.gz`) are refused.

## 2. Publish (after the user confirms)

```bash
git -C ../artoolkit-nft-bench-results pull
<venv-python> scripts/publish_results.py <name> --from results/local/<dir> \
    --results-repo ../artoolkit-nft-bench-results --milestone "M<n> — <name>" --code-release v<x.y.z> --release
```

One commit in the results repository (archive + publications-table row), pushed; with `--release`, an annotated tag `<name>` and
an immutable GitHub Release there; then `results/manifest.json` gains the entry. Commit the manifest in a PR to `dev`.

## Rules

* Names are never reused; a wrong result is superseded by a new publication, never deleted or overwritten.
* Publish when a written conclusion rests on the data, normally at the end of a milestone (ADR-0002), not per commit.
