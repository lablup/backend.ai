---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-11-26
Created-Version: 26.10.0
Target-Version:
Implemented-Version:
---

# v2 Development

## Goals

Develop the Go replacements of the manager, agent and storage proxy on the long-lived development branch `v2`, and land them on `main` at once when the replacement is complete.

| Goal | Current | Done when | Related issue |
|---|---|---|---|
| `v2` split and `main` freeze | No `v2` branch and no `main` freeze rule | `v2` exists, CI rejects new alembic migration files, and AGENTS.md rules stop Python feature development | BAI-1110 |
| Directories | No `go.mod` or Go directory at the repository root | The replaced Python is removed, and `go.mod`, `cmd/`, `internal/`, `api/` and `migrations/` exist | BAI-1114 (skeleton), BAI-1112 (removal) |
| Commands, tests and DB schema | No go tool commands and no DB test environment | Lint and tests run with go tools, and the alembic head schema at `v2` creation is the first migration | BAI-1113 |
| `v2` Go CI | No Go CI for PRs whose base is `v2` | `v2` has only the Go CI workflow (`ci.yml`), and the one required check is `ci-gate` | BAI-1114 |
| Same-standard check | No language-independent API contract test | The same contract test passes on both the Python and Go versions | BAI-1115 |
| Go working rules | AGENTS.md on `v2` is not the Go working rules | AGENTS.md on `v2` holds the Go working rules | BAI-1116 |
| Transition and release | No `v2` → `main` transition procedure or preview release procedure | `v2` lands as one merge commit, and the stable version is released after the preview runs. The tag release workflow (`release.yml`) builds only after the full tests pass | BAI-1148 |

## Non-goals

- Go replacement of the client, CLI, webserver and app proxy: they remain on `v2`.
- Go replacement of the account manager, kernel runner and accelerator plugins: they remain on `v2`.

## Design

### Branch and `main` freeze

`main` accepts only bug fixes and is not synchronized to `v2`. `v2` lands on `main` as one merge commit when the replacement is complete. A bug fix PR that changes the manager, agent or storage proxy carries the label `require:v2-port`, and the same fix is applied to the Go code on `v2`.

| Item | Rule |
|---|---|
| Python feature development | Stopped |
| alembic migration | Stopped. CI rejects a new alembic migration file in a PR to `main` |
| Bug fix | Allowed. The label `require:v2-port` when it changes the manager, agent or storage proxy |
| Bug fix that needs a schema change | The label `allow:alembic-migration` after user approval. The same change is added to the `v2` migrations |

### `v2` scope, module and DB schema

On `v2`, only the Python that Go replaces is removed: the manager (including sokovan), agent and storage proxy. Build, lint and tests use go tools. Pants does not handle Go code.

| Item | Content |
|---|---|
| Removed | The Python of `src/ai/backend/manager` (including sokovan), `src/ai/backend/agent` and `src/ai/backend/storage` |
| Kept | Client, CLI, webserver, app proxy, account manager, kernel runner, accelerator plugins |
| Module | One root module `github.com/lablup/backend.ai`. Each binary is built separately from `cmd/<name>/` |
| Repository root | `go.mod`, `cmd/`, `internal/`, `api/`, `migrations/` |
| Development tools | Pinned by the `tool` directive of the root `go.mod` (Go 1.24). Only golangci-lint for now. Code generation and migration tools are decided in the API rewrite BEP |
| DB schema | The first migration is the alembic head schema at `v2` creation. Later schema changes are only `v2` migrations |

### Transition procedure

The `v2` → `main` transition follows the order below. When `main` is merged into the transition branch, modify/delete conflicts are resolved as deletions.

| Order | Work |
|---|---|
| 1 | Freeze `main` briefly |
| 2 | Merge `main` into the transition branch. Resolve modify/delete conflicts as deletions, and delete again the removed directories that reappeared through files `main` newly added. `.github/workflows/ci.yml` is the same path on `main` (Python) and `v2` (Go), so it gets a content conflict and is resolved to the `v2` side |
| 3 | Cross-check the Go ports of bug fixes (`require:v2-port`) against the conflict list |
| 4 | Create the `v2` → `main` PR and merge it with a merge commit. The `main` ruleset (linear history, squash merge only) now blocks the transition merge commit, so change the ruleset at transition or merge with a bypass permission |

### CI, release and verification

A PR whose base is `v2` uses the workflows of the PR's merge commit, so `v2` deletes the existing Python CI workflows and keeps only the Go CI. There are two workflow files, `ci.yml` (PRs and `v2` pushes) and `release.yml` (tag releases), and the one required check is `ci-gate`. Merge and release are separate: the stable version is released after the preview (LTS stays with the Python release branches), and a language-independent API contract test checks the Python and Go versions against the same standard.

| When | Check | Effect |
|---|---|---|
| pre-commit | `golangci-lint fmt`, `run --fast-only`. `v2` has no pre-push hook | Pre-commit check |
| PR | Format, lint (golangci-lint), build (including the `go mod tidy` diff) | Blocks the merge |
| PR | `go test -short`, generated-file diff (`go generate`, then diff) | Result shown only |
| `v2` push | Full tests (DB, `-race`) and generated-file diff check per commit. A diff opens a PR with the regenerated files | After-the-fact check |
| Tag release | Builds only after the full tests pass | Build condition |

## Evidence

A 3-month history simulation and Bun's Zig → Rust transition.

| 3-month history simulation | Result | Design it supports |
|---|---|---|
| Modify/delete conflicts | 2,314 | Transition step 2: resolve modify/delete conflicts as deletions |
| Content conflicts | 0 | Transition step 2: resolve modify/delete conflicts as deletions |
| Files `main` newly added | Reappear in the removed directories | Transition step 2: delete the removed directories again |

| Bun PR (oven-sh/bun) | Fact | Design it supports |
|---|---|---|
| #30412 `Rewrite Bun in Rust` | Created 2026-05-08, merged 2026-05-14. Squash merge | Contrast |
| #32621 `Remove the .zig porting-reference sources` | Merged 2026-06-25, 6 weeks after #30412. Deleted 1,270 old Zig source files | Contrast |
| #30733 `http: port fetch TCP keepalive to on_open in lib.rs` | Merged 2026-05-14. #30412 branched before #30627 merged, so the TCP keepalive call was not ported to Rust, and `fetch-tcp-keepalive.test.ts` failed in the Linux test job | Transition step 3: cross-check the conflict list, and `require:v2-port` |

Contrast: Bun squash-merged and deleted the old code separately 6 weeks later. This BEP removes it on `v2` beforehand and lands with a merge commit.

## Impact

- `main` contributors: CI rejects a new alembic migration file.
- `main` contributors: AGENTS.md rules stop Python feature development.
- `main` contributors: a bug fix that changes the manager, agent or storage proxy carries `require:v2-port`.
- CI: `v2` has only the Go CI, and in a PR only format, lint and build block the merge.
- CI: a PR to `main` rejects a new alembic migration file.
- DB schema: After the transition, schema changes use only `v2` migrations.
- Release: The stable version is released after the preview. LTS stays with the Python release branches.

## Implementation Order

1. `main` freeze rules and `v2` creation (BAI-1110): two labels, CI that rejects a new alembic migration file
2. Go module skeleton and Go CI (BAI-1114): `go.mod`, the top-level directories, `ci.yml`
3. Removal of the replaced Python (BAI-1112)
4. Commands and DB test environment (BAI-1113)
5. API contract test frame (BAI-1115), Go working rules in `v2` AGENTS.md (BAI-1116): in parallel
6. Release CI (BAI-1148): `release.yml`
7. Transition and release: the `v2` → `main` merge commit, then the stable version after the preview

## References

- Bun: oven-sh/bun #30412, #32621, #30733
