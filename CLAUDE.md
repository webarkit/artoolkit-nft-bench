# CLAUDE.md

The canonical, tool-agnostic guidance for this repo lives in **AGENTS.md**. It is imported below — treat it as the source of truth.

@AGENTS.md

## Claude-specific notes

- On Windows, prefer the Bash tool's POSIX shell for git, CMake and Python commands; the commands in the docs assume bash-style quoting.
- Never round-trip a source file through PowerShell (`Get-Content -Raw` then `Set-Content`): it re-encodes text and prepends a BOM. Edit files with the Edit/Write tools; use PowerShell to run things, not to rewrite them.
- Long runs (`genTexData`, benchmark suites) belong in the background, with output redirected to `results/local/`.
