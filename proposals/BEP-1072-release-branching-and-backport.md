---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-07-28
Created-Version: 26.8.0
Target-Version:
Implemented-Version:
---

# Release Branch Isolation and Backport Automation

## Related Issues

- Epic **BA-7049**, this BEP **BA-7050**
- Reference (not expanded): `src/ai/backend/manager/models/alembic/README.md` — migration backport strategy

## 1. Goal

`main` doubles as the development branch and the active release version, so a release version cannot be stabilized apart from feature merges. Backport targets depend on a hand-applied milestone, and when a backport fails no PR is created at all, so there is no way to tell what was dropped.

This BEP redefines the release procedure as **three actions** — the rc release and version branch cut, fix backports and verification during the rc period, and the final release with its changelog reflected into `main`.

**Terminology.** A **version branch** is the `YY.S` unit that becomes a branch (`26.8`); it is written `<version>`, and the next one `<next>`. A **release heading block** is one `## <version>.<patch> (<date>)` block in a changelog file, down to the next `##` — exactly what one towncrier run produces.

**Non-goals**

- Defining version grades (Edge/LTS) and support periods — that belongs to the support policy document. Here we deal only with the **list of maintained versions**.
- Automatic conflict resolution for backports, `Fixes:` trailers, and deterministic backport scope inference in CI — see 3.(b) for the advisory split.
- Moving **code** backward from a version branch to `main`. Branch-only code commits measured zero, so we state the principle only and build no workflow.
- Taking the WebUI bundle out of the release artifact. It has to ship inside the artifact for now, so 3.(d) only decouples **when** the bundle is pinned, not where it lives.
- Alembic backport policy and changes to the version numbering scheme. Milestones stay for release planning; they are dropped only from the backport decision.

## 2. Current State & Scope, by Area

For each area, separate **✅ what already exists** from **➕ what to add**. Measured (2026-07-28): `.0` intervals 17–31 days, `rc1`→`.0` 1–5 days, 52 branch commits in the 6 weeks after the 26.4 cut = 42 automated backports + 6 manual + 4 release, **0 branch-only code commits**.

### 2.1 Branch cut and rc

| | Item |
|---|---|
| ✅ | The branch is cut only when the next version starts — the 26.4 fork point is the `release: 26.4.4` commit |
| ✅ | rc releases go out as tags on `main` without a version branch (`26.4.0rc1` and so on) |
| ✅ | Tagging and branching are manual — `daily-workflows.rst` documents them as hand-run git commands |
| ➕ | **Release rc1 from `main` at feature completion, and tag that merge commit while cutting the version branch from it — one action.** The branch has 0 commits at cut time |
| ➕ | Automate that action on release-PR merge, keyed on `merge_commit_sha` |

### 2.2 Version values

| | Item |
|---|---|
| ✅ | `VERSION` (at the root, symlinked into 10 packages) determines both the wheel metadata and the displayed version |
| ✅ | `release.sh` freezes `NEXT_RELEASE_VERSION` (`meta.py`, 154 references) at the final release and bumps it afterwards — both on `main` |
| ➕ | `VERSION` = **the version that tree released last**. Only release commits update it, so it **always matches the tag** |
| ➕ | Fold the freeze and the NEXT bump into the **cut (rc release) PR**, driven by a script rather than by hand. The branch inherits the frozen result |

### 2.3 Backport target decision

| | Item |
|---|---|
| ✅ | `backport.yml` reads the PR **milestone**, keeps only those with a branch of the same name, and fans out to every version at or above it |
| ✅ | Current milestones are `Backlog/26.5/26.4/25.15` while `main` develops 26.8 — so `26.5` works as an accidental opt-out |
| ➕ | Drop the milestone. Decide from the **PR title prefix + labels** and check against the version list in `.github/maintained-versions.yml` |
| ➕ | Silently exclude a target when the PR touched none of its files |
| ➕ | Keep CI's decision deterministic; put scope *suggestion* in an advisory skill (3.(b)) |

### 2.4 Backport failure handling

| | Item |
|---|---|
| ✅ | The cherry-pick uses `--strategy-option=theirs`, so conflicting hunks are silently overwritten |
| ✅ | On failure it leaves a one-line comment on the original PR and ends the job — **no PR is created, so it cannot be tracked** |
| ✅ | `Backported-from/to/of` trailers are absent from the actual merge commits (1 case across all of 26.4) |
| ➕ | Remove `-X theirs`. On conflict, **commit the conflict markers as-is and open a draft PR** + `pending:backport` |
| ➕ | Fix the trailers so they land in the merge commit body |

### 2.5 Changelog

| | Item |
|---|---|
| ✅ | A single 4267-line `CHANGELOG.md`. towncrier always inserts at the same point, so two versions releasing means a guaranteed conflict |
| ✅ | Even with no fragments an **empty release heading block is produced**, and `extract-release-changelog.py` matches it and emits **empty release notes** without failing |
| ✅ | rc heading blocks are consolidated into the final block at release time — `CHANGELOG.md` holds 0 `## ...rc` headings although `26.4.4rc1`–`rc9` were tagged |
| ➕ | **Per-version-branch files** (`CHANGELOG-<version>.md`). `release.sh` runs with a temporary config that copies `[tool.towncrier]` and overrides only `filename` |
| ➕ | Skip towncrier when there are no fragments to consume. For a prerelease, strip the rc suffix before searching for the block |
| ➕ | The file must read as a complete release note from the rc onward; the final release consolidates it; a patch release records **only the fixes backported into it** |

### 2.6 WebUI bundle and the GraphQL schema

| | Item |
|---|---|
| ✅ | The built WebUI bundle is committed into this repo (`src/ai/backend/web/static/`, 4718 files) and ships in the wheel via `resources(sources=["static/**/*"])` |
| ✅ | `release.sh <version> [webui_version]` pins the bundle **inside the release commit** — every recent commit touching `static/` is a `release:` commit |
| ✅ | WebUI builds against `docs/manager/graphql-reference/`, and every tag (rc included) already publishes `supergraph.graphql` as a GitHub Release asset |
| ✅ | The schema does not move on a version branch in practice — 55 commits on `26.4` since its fork point, **0 touching `docs/manager/graphql-reference/`** |
| ➕ | Make that a **rule**: from the rc1 tag onward the version branch does not change the GraphQL schema, enforced in CI |
| ➕ | Pin the bundle in an **independent PR**, not in the release commit — drop `webui_version` from `release.sh` |

## 3. Implementation Design

**Core flow**: feature completion → rc1 release on `main` (freeze + NEXT bump + towncrier) → tag and cut the version branch at that same commit → backport fixes during the rc period → release `.0` from the branch → copy the version changelog into `main`.

### (a) rc release and version branch cut

| # | Where | Action |
|---|---|---|
| 1 | `main` PR `release: <version>.0rc1` | `VERSION` → `<version>.0rc1` / freeze(`<version>.0`) + `pants fix/fmt` / **NEXT → `<next>.0`** / regenerate samples and schemas / consume towncrier (`--version <version>.0`) → create `CHANGELOG-<version>.md` / register `<version>` in `maintained-versions.yml` |
| 2 | `main` | On merge, tag the merge commit `<version>.0rc1` **and** create branch `<version>` at that same commit — **one action, no commits on the branch** |

**The cut is the act of releasing rc1 from `main`, and it takes exactly one PR.** The branch inherits a state where both `VERSION` and the fragment pool are already correct, so there is nothing to touch. The rc1 tag is a common ancestor of both `main` and the version branch, and rc1 is never tagged again from the branch.

Row 1 is produced by a script (`cut-release-branch.sh`), not by hand: it runs `freeze_release_version.py` → `pants fix/fmt` → `bump_next_release_version.py` → sample/schema regeneration → towncrier → registration, then opens the PR. Row 2 is a workflow on release-PR merge that reads `merge_commit_sha`, so the tag and the branch point at the same commit by construction.

> The tag must be pushed with the PAT already used for backport PRs. Refs created with the default `GITHUB_TOKEN` do not trigger other workflows, and `ci.yml`'s `make-final-release` — build, GitHub Release, PyPI upload — runs on tag push.

There are two reasons to freeze in the cut PR rather than on the branch. `freeze_release_version.py` deletes imports and runs `pants fix/fmt`, so doing it on the branch diverges the two trees and increases later cherry-pick conflicts. And the `main` code at cut time first ships in `<version>.0`, so `added_version=<version>.0` is semantically correct.

The NEXT bump happens in the same PR. The branch inherits `<next>.0`, but new GQL fields are `feat:` and therefore not automated backport targets, so this does not surface in practice. It is checked in review only when something is explicitly backported.

The version changelog file is not pre-seeded as a stub; rc1's towncrier creates it, and it must already read as a complete release note at that point.

### (b) Fix backports and verification during the rc period

The rc period is nominally **one week** (enough for feature verification and test reinforcement).

| # | Action |
|---|---|
| 1 | Decide targets — `fix:` → every version in `maintained-versions.yml` / a `backport:<version>` label or `/backport` comment → additional targets / `no-backport` → none / any other prefix → none |
| 2 | Silently exclude a target when the PR touched none of its files |
| 3 | Cherry-pick — on success open a PR with auto-merge, on conflict open a **draft PR** + `pending:backport` |

A fix that lands in an older version applies to every newer live version as well (so the bug does not come back on upgrade).

**How far back a fix should go is not decided in CI.** Step 1 uses only what CI knows for certain — prefix, labels, changed files. Which releases actually contain the bug can only be inferred (blame the changed hunks → find the introducing commit → `git tag --contains`), and that inference is unreliable across refactors and file moves. So it lives in an advisory skill that comments a suggested target set on the PR; a human confirms with a label. The skill never gates the merge.

**Failures are recorded as results too.** Left as draft PRs, the per-version outstanding list is visible as a PR list, and the same skill classifies and cleans it up. Put a required-checks ruleset on the version branches so auto-merge cannot skip CI — `ci.yml`'s push filter already carries the release branch patterns, so no workflow change is needed.

If further verification is needed, cut `<version>.0rc2` from the branch.

### (c) Final release and changelog reflection into `main`

| # | Where | Action |
|---|---|---|
| 1 | Branch PR `release: <version>.0` | `VERSION` → `<version>.0`, run towncrier if there are fragments to consume, consolidate the rc content into the final release heading block |
| 2 | Branch | Tag `<version>.0` |
| 3 | `main` PR (automated) | `git checkout origin/<version> -- CHANGELOG-<version>.md` — **one file copied** |

Patch releases (`<version>.1` onward) take the same path, and their heading blocks record **only the fixes backported into that release** — a patch release ships nothing else. The copy in row 3 runs for every final tag and never for a prerelease.

Why copying suffices: the version file is owned solely by that branch, and `main` never touches it after creating it at the cut, so there is nothing to merge against. It is idempotent, so re-running is safe, and because the files are per version branch, simultaneous releases of several versions cannot conflict. The prefix is `release:`, so it is not itself a target of (b) — no loop.

This PR does not touch `changes/`. **Each tree drains its own fragment pool with its own release** — the `main` pool is drained by the cut (rc1), the branch pool by that branch's releases. Fragments the branch consumed remain in the `main` pool and are consumed again into `<next>`'s notes at the next cut; the same fix appearing in two versions' notes is expected.

### (d) WebUI bundle and the schema freeze contract

The bundle must ship inside the release artifact, so the two repos cannot be decoupled by packaging. They are decoupled in time instead: WebUI needs the schema **early** (at the cut) and this repo needs the bundle **late** (at the final release), and the rc period is exactly that gap.

| Party | Commitment |
|---|---|
| backend.ai | Publish `supergraph.graphql` as a release asset at the rc1 tag, and **do not change the GraphQL schema on that version branch afterwards** |
| WebUI | Build against that asset and release its bundle |
| backend.ai | Take the resulting bundle in an **independent PR**, not in the release commit |

**The freeze is a rule, not an observation.** A version branch only takes `fix:` backports, which is why the schema has not moved in practice, but nothing prevents a fix from touching a GraphQL field. CI fails any change under `docs/manager/graphql-reference/` on a version-branch PR, with the existing `graphql-inspector` job as the breaking-change backstop. Only then can WebUI treat the rc1 asset as that version's final schema.

**Pinning the bundle is separate from releasing.** `release.sh` drops its `webui_version` argument; the bundle arrives as `chore: update webui to <x>` whenever WebUI ships, and a release commit simply carries whatever bundle the branch holds. If WebUI misses the rc window, `.0` still goes out on schedule with the current bundle and the update rides the next patch release — so a patch release may exist solely to advance the bundle, which is the one carve-out to "a patch release records only backported fixes" (3.(c)).

**Each tree owns its own bundle**, exactly like the fragment pool: `main` carries the bundle for the version under development, a version branch carries its own, and each is updated by its own PR. 4718 files are never cherry-picked between them.

Pinning an rc bundle during the rc period is already the established practice (past pins include `25.18.0-rc.1`, `25.13.0-rc.2`, `25.12.0-rc.1`), which lets an rc2 verify the UI before the final release.

### (e) Release procedure

Who does what, once this is in place.

| Step | Actor | Action |
|---|---|---|
| Cut 1 | Human | Run `cut-release-branch.sh <version>` → opens PR `release: <version>.0rc1` |
| Cut 2 | CI | `check-version-change` confirms the release prefix; full test suite |
| Cut 3 | Human | Squash-merge |
| Cut 4 | **Automated** | Tag `<version>.0rc1` (PAT) and create branch `<version>` at the merge commit |
| Cut 5 | **Automated** | Tag push → `ci.yml make-final-release` → wheels/scies, GitHub Release (prerelease), PyPI |
| rc period | **Automated** | fix PRs merged to `main` → `backport.yml` opens cherry-pick PRs on `<version>`; success auto-merges, conflict lands as a draft PR + `pending:backport` |
| rc period | Human | Resolve conflicted draft PRs. For more verification, `release.sh <version>.0rc2` on the branch |
| rc period | WebUI | Build against the rc1 `supergraph.graphql` asset and ship a bundle; it lands here as its own `chore: update webui to <x>` PR |
| Final 1 | Human | `release.sh <version>.0` on the branch → PR → merge |
| Final 2 | **Automated** | Tag `<version>.0` → GitHub Release + PyPI |
| Final 3 | **Automated** | `changelog-sync.yml` opens a `main` PR copying `CHANGELOG-<version>.md` |
| Patch | — | `<version>.1` onward takes the same path as Final |

Humans run two scripts, merge two PRs, and resolve backport conflicts. Tagging, branching, and the changelog copy are automated.

rc releases are published to PyPI like any other tag; `make-final-release` already uploads on every tag, so this needs no change beyond confirming the `deploy-to-pypi` environment gate.

### (f) Work scope

| Work | Content |
|---|---|
| **Version management in CI** | New `cut-release-branch.sh` (the whole cut PR procedure, absorbing freeze/bump out of `release.sh`), a workflow that tags and branches from `merge_commit_sha` on release-PR merge, align `VERSION` on `main` |
| **Label-based backport + advisory skill** | Introduce `maintained-versions.yml`, replace target decision in `backport.yml` (keep the matrix JSON shape → downstream jobs unchanged), pre-filter, remove `-X theirs`, draft PR on conflict, fix trailers, `backport:<version>` and `no-backport` labels, a Claude skill that suggests target scope on a PR and that lists, classifies, and cleans up `pending:backport` PRs |
| **WebUI decoupling** | Drop `webui_version` from `release.sh` so the bundle is pinned by its own PR, add a CI check that rejects `docs/manager/graphql-reference/` changes on version-branch PRs, and optionally warn when `static/version.json` lags the release version |
| **Changelog split and script cleanup** | Per-version-branch files via a temporary towncrier config (written at the repo root so its relative `directory`/`template` paths resolve), towncrier skip guard, hardcoding and prerelease handling in `extract-release-changelog.py`, new `changelog-sync.yml`, 2 CI bugs (the edge-release regex `[0-9]{2}\.[0-9]{2}` never matches a `YY.S` branch, `X.Y.0rc1` in `check-backport-commits.py`), update `daily-workflows.rst` |

## 4. Decision Summary

| Decision | Content |
|---|---|
| Cut point | The **rc1 release on `main`** at feature completion |
| Cut action | Tagging rc1 and creating the version branch are **one action on the same merge commit**, automated from `merge_commit_sha`. The branch starts with 0 commits, and rc1 is never re-tagged from it |
| Cut procedure | Done in **one PR**, generated by `cut-release-branch.sh` — `VERSION`, freeze, NEXT bump, regeneration, towncrier, version registration |
| Script split | `cut-release-branch.sh` (on `main`, cut only) and `release.sh` (on a version branch, no freeze/bump) are separate; they share only the regeneration helpers |
| `VERSION` | The version that tree **released last**. Only release commits update it, so it always matches the tag, there is no need to overwrite it at build time, and an rc claiming a final version on PyPI becomes structurally impossible |
| `NEXT_RELEASE_VERSION` | Frozen and then bumped to the next target in the cut PR. The branch inherits `<next>.0`, but new fields are `feat:` and thus not automated backport targets |
| Backport targets | Milestone dropped. Prefix + labels + `maintained-versions.yml`. Grades and support periods are outside this BEP |
| Backport scope | CI decides deterministically; how far back a fix belongs is **suggested by an advisory skill**, confirmed by a human label, and never gates a merge |
| Backport failure | Not silently overwritten (`-X theirs` removed); left as a draft PR |
| Changelog file | **Per version branch**. Splitting per release would leave the `.0` file holding only the post-rc delta, so the final content would never reach `main` |
| Changelog content | Complete release note from the rc onward, consolidated at the final release; a patch release records only the fixes backported into it |
| Fragment ownership | Each tree drains its own pool with its own release. No backward movement |
| Reflection into `main` | **One version file copied** per final tag. Not a cherry-pick |
| rc on PyPI | Published like any other tag. No workflow change needed |
| Schema freeze | From the rc1 tag onward the version branch **does not change the GraphQL schema**, enforced in CI. The rc1 release asset is that version's final schema, and WebUI builds against it |
| WebUI bundle pin | Pinned by its own PR, never inside a release commit. A release carries whatever bundle the branch holds, so WebUI never blocks `.0`; a patch release may exist solely to advance the bundle |
| Bundle ownership | Each tree owns its own bundle, like the fragment pool. Never cherry-picked between trees |

## 5. Open Questions

- **Whether rc releases keep their own release heading block** until the final release consolidates them, or write into the final block from the start. Today's `CHANGELOG.md` shows the former as the existing practice (0 rc headings survive, 9 rc tags exist).
- **Permissions for the `/backport` comment trigger** — write access versus maintainers only.
- **Which versions stay in `maintained-versions.yml`, and for how long** — follows from the support policy decision.
- **Whether the WebUI bundle can eventually leave the release artifact** (a separate bundle wheel or an install-time download, both compatible with the webserver's existing `static_path`). Out of scope while the artifact must contain it, but it is the only change that removes the coupling rather than scheduling around it.

## 6. References

- `.github/workflows/{backport,ci,check-version-change,timeline-check}.yml`, `.github/actions/{pr-title-prefix,detect-release-pr}`
- `scripts/{release.sh,build-wheels.sh,freeze_release_version.py,bump_next_release_version.py,check-backport-commits.py,extract-release-changelog.py,determine-release-type.py}`
- `src/ai/backend/common/meta/meta.py`
- `src/ai/backend/manager/models/alembic/README.md`
- `docs/dev/daily-workflows.rst` — "Making a new release", "Making a new release branch"
- Prior art: CPython PEP 101 / `Misc/NEWS.d` (`main` up to b1, branch-only afterwards), Kubernetes `CHANGELOG/CHANGELOG-1.xx.md` (per-version files)
