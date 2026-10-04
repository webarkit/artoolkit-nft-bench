<!-- Target branch must be `dev` (never `main`). Title: Conventional Commits, e.g. `feat(runner): add native nft_run`. -->

## What and why

## Checklist

- [ ] Base branch is `dev`
- [ ] Title follows Conventional Commits
- [ ] Assigned to the milestone of its phase
- [ ] `CHANGELOG.md` updated under `[Unreleased]` if behaviour or results change
- [ ] Build, `ctest` and `pytest` run locally and pass (commands in `AGENTS.md`)
- [ ] `extern/artoolkit5` untouched
- [ ] No raw results, frame banks or build trees committed; published results go through the publish script
- [ ] No host names, user names, emails, absolute paths, tokens, IP/MAC or serials in committed or published files
