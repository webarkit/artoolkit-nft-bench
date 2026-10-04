# ADR-0002: One milestone per phase; a release closes it

Status: Accepted · Date: 2026-10-04

## Context

The spec splits the work into phases (native baseline, WASM control, jsartoolkitNFT, marker generators, optional extensions).
Pull requests and issues need a visible grouping that says which phase they belong to, and releases need a clear trigger: a
release that is cut "when it feels ready" ends up either too frequent or mixing unfinished phases.

Options considered:

1. **Releases on demand.** Simple, but nothing ties a version to a finished, documented result.
2. **Time-based releases.** Predictable, but phases do not finish on a calendar, and a benchmark release half-way through a
   phase publishes numbers nobody has reviewed.
3. **One GitHub milestone per phase, released when the milestone is complete.**
4. **One milestone per phase or per declared work block** (infrastructure, ground-truth quality) that is not a spec phase but is
   large enough to deserve its own release.

## Decision

* Every phase of the spec, and every work block declared as a milestone, is a GitHub milestone named `M<n> — <name>`, numbered
  in the order the work is done (e.g. `M1 — Native baseline`, `M2 — Project infrastructure`, `M3 — Real-footage ground truth`,
  then the remaining spec phases). Milestone numbers therefore need not equal spec phase numbers. Every pull request and issue
  belonging to a milestone is assigned to it.
* A work block is declared by creating its milestone with a one-line scope in its description and listing it in the spec's
  Roadmap section. Option 3 alone was not enough: infrastructure and ground-truth work would have been folded into the next spec
  phase, mixing unrelated changes in one release.
* A milestone is complete when its deliverables are merged into `dev`: code, tests and, for milestones that produce results, the
  results summary in `results/phase<n>/` and the raw results published per [ADR-0001](0001-results-storage.md).
* **The release is the last step of the milestone.** In order:
  1. a pull request into `dev` closes the `[Unreleased]` changelog section as the new version;
  2. the release pull request goes from `dev` into `main` and is merged with a merge commit; it is assigned to the milestone;
  3. an annotated tag `vX.Y.Z` is put on that merge commit;
  4. a GitHub Release (immutable) is created on the tag, with the changelog entry as its notes;
  5. the milestone is closed.
* Versions: before 1.0, each completed milestone bumps the minor version (`M1` → `v0.1.0`, `M2` → `v0.2.0`, ...). A fix to a
  released milestone's results or code is a patch release (`v0.1.1`) and does not reopen the milestone.
* Small work that belongs to no milestone (a fix, a dependency bump) is assigned to the open milestone it lands in, or to none.

## Consequences

* Each version corresponds to one finished phase with reviewed results, so a version number is enough to cite a set of numbers.
* The milestone page shows what is left in a phase at any time.
* A long phase means a long gap between releases; patch releases cover fixes in between.

## To revisit

* If phases grow large, split a phase into several milestones (`M2a`, `M2b`) rather than releasing mid-milestone.
