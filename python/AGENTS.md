# AGENTS.md — python/

Adds to the root [AGENTS.md](../AGENTS.md); never overrides it.

* `nftbench` is installed editable (`pip install --no-build-isolation -e .`); tests live in `python/tests/` and run with
  `.venv/Scripts/python -m pytest -q` from the repository root.
* Write the failing test first. Tests that drive `nft_export`/`nft_run` need the native build; they fail (never skip) without it.
* **The scorer depends on no engine.** `schema.py`, `geometry.py`, `metrics.py`, `score.py` read only banks and results. A new
  engine needs a runner, not scorer changes.
* Metric definitions are part of the published results: changing one (e.g. what `median_px` covers) changes every table. Say so
  in the PR and the changelog, and regenerate the tables.
* `segment.py` produces ground truth for real footage: it must return no corners rather than wrong ones. Read colour frames from
  the source video, not the grey bank.
* `publish.py` holds the sensitive-data scan; extend its patterns rather than bypassing it.
