---
name: changes-pr-title-changelog-mapping
type: decision-table
description: category-to-PR-title-prefix/changelog-type mapping, the rule for marking same-release-cycle bug fixes as chore/misc instead of fix and why, why a fragment can be named without a PR number, and why epic files exist
scope: changes
keywords: [fix, chore, misc, backport, towncrier, changelog, PR title, maintained-versions, changelog fragment, PR number, epic]
sources:
  - changes/README.md
  - .github/maintained-versions.yml
  - scripts/new-changelog.py
  - scripts/rename-changelog-fragments.py
  - scripts/changelog_fragments.py
generated:
  by: claude-code/sonnet-5
  at: 2026-09-04
status: draft
---

# changes/ — Knowledge

> Rules: `changes/README.md` (filename convention, writing style)

## Why this directory exists

A PR title and its news fragment (`changes/<...>.<type>.md`) live in different places but share the same classification. This document holds that classification, and the exception it creates because `fix:` triggers an automatic backport (same-release fixes).

## Category-to-PR-title-prefix/changelog-type mapping

| Category | PR title prefix | Changelog type | Note |
|---|---|---|---|
| New functionality | `feat` | `feature` | |
| Bug fix — already on a maintained release branch | `fix` | `fix` | Auto-backports to every maintained version |
| Bug fix — code introduced this same, still-unreleased cycle | `chore` | `misc` | Never shipped, so not a backport target |
| Performance/refactoring | `refactor`/`perf` | `enhance` | |
| Breaking API change | keeps the underlying commit type (`feat`/`refactor`/...) | `breaking` | No dedicated prefix — the type stays as-is, only the changelog classifies it as breaking |
| Test-only change | `test` | `test` | |
| Documentation | `doc` | `doc` | |
| Dependency update | `deps` | `deps` | |
| Deprecating existing functionality | keeps the underlying commit type (`chore`/`feat`/...) | `deprecation` | No dedicated prefix |

## Why a same-release fix isn't `fix`

- A `fix:` PR backports automatically to every maintained version listed in `.github/maintained-versions.yml`.
- That only makes sense when the bug already exists on a maintained branch.
- If the buggy code exists only on `main` — introduced earlier in this same, unreleased cycle — tagging it `fix` backports code that was never released.
- So the PR title uses `chore` and the news fragment uses `misc`.

## Why a fragment can be named without a PR number

- A fragment named `<PR-number>.<type>.md` can only be added after the PR is opened, as a second push that restarts the PR's CI.
- A fragment named `<YYYYMMDD>-<HHMMSS>-<6 chars>.<type>.md` goes into the first push with the code. This name is recommended with or without an issue key.
- The release gives it the PR number from git history: the first-parent commit that added the file carries `(#N)` in its subject, from the squash merge or the backport.
- The rename drops the front matter, so towncrier still reads only `<PR-number>.<type>.md` names.

## Why epic files exist

- To group an epic's work in the release notes, the fragment records the epic of its issue when it is written (`epic`).
- The epic's title and summary are written once in `changes/epics/` and reviewed in the PR. The release does not query the issue tracker.
- An epic spans releases, so a release does not consume epic files.
- `changes/epics` is in the towncrier `ignore` of `pyproject.toml`: towncrier stops on a name without a dot as an invalid fragment name.
- When towncrier is dropped, the numbered names and the towncrier settings go with it.
