---
name: changes-pr-title-changelog-mapping
type: decision-table
description: category-to-PR-title-prefix/changelog-type mapping, the rule for marking same-release-cycle bug fixes as chore/misc instead of fix, and why
scope: changes
keywords: [fix, chore, misc, backport, towncrier, changelog, PR title, maintained-versions]
sources:
  - changes/README.md
  - .github/maintained-versions.yml
generated:
  by: claude-code/sonnet-5
  at: 2026-09-04
status: draft
---

# changes/ — Knowledge

> Rules: `changes/README.md` (filename convention, writing style)

## Why this directory exists

A PR title and its news fragment (`changes/<PR-number>.<type>.md`) live in different places but share the same classification. This document holds that classification, and the exception it creates because `fix:` triggers an automatic backport (same-release fixes).

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
