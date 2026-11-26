# AI Coding Agent Guidelines

This file holds the AI coding agent rules, the workflow and the skill index of the `v2` branch. `v2` is the branch that rewrites the manager, the agent and the storage proxy in Go, and it is Go only.

## Workflow

Work in the order below. Move to the next step once the step's exit condition holds.

| Step | Do | Skill | Exit condition |
|---|---|---|---|
| 1. Context | Read the `AGENTS.md` of the directory you work in and find the related `KNOWLEDGE.md` | `/knowledge` | The rules and the background that apply are known |
| 2. Design | Write and agree a BEP for a large feature. Skip it for a small change | `/bep-guide` | The BEP is agreed |
| 3. Test scenario agreement | Propose the success, error and boundary scenarios and fix them with the user | `/test-guide` | The scenario list is fixed |
| 4. Implementation | Implement in a worktree on a branch based on `v2` and write a test for each scenario. A test that needs a database uses a local PostgreSQL | `/test-guide`, `/halfstack` | The test of each scenario passes |
| 5. Documents | Reflect the changed rules and background in the documents | `/writing` | The document lint passes |
| 6. Review | Get a review from another session and check each finding. Always do this before the PR | `/local-review` | The findings are checked and handled |
| 7. Submission | Commit, create the changelog fragment and the PR, and check the CI result | `/submit` | `ci-gate` passes |

## Repository layout

| Path | Content |
|---|---|
| `go.mod` | The single root Go module `github.com/lablup/backend.ai`. The development tools are pinned by the `tool` directive |
| `cmd/<name>/` | One `main` package per deployed binary. No development tool |
| `tools/<name>/` | A development tool. A `main` package of the root module, run with `go run ./tools/<name>` |
| `internal/` | Packages used only inside the module |
| `api/` | API definitions. The existing API contract files are in `api/legacy/{graphql,rest,appproxy}/` |
| `migrations/` | SQL migration files |
| `tests/integration/` | Integration tests |
| `changes/unreleased/` | Changelog fragments (`changes/README.md`) |

- The module is one at the root, so `./...` at the root targets all packages.

## Directory AGENTS.md

Read the `AGENTS.md` of a directory before you work in it.

| Directory | Content |
|---|---|
| `.github/AGENTS.md` | CI workflow and called script rules |
| `migrations/AGENTS.md` | Migration file rules |
| `proposals/AGENTS.md` | BEP writing rules |
| `scripts/AGENTS.md` | Rules for the scripts in `scripts/` |

Where documents go:

- How to work on a component and its layers goes in the checklist of the component's top-level `AGENTS.md`. Name the test or lint that enforces each step.
- A package contract goes in `doc.go`.
- A layer boundary goes in the component `AGENTS.md` and in golangci-lint `depguard`.
- An architecture overview goes in `KNOWLEDGE.md`.

## Rules

- `go test -short ./...` runs only tests with no external dependency. A test that waits for a database, an external service or real time is skipped under `-short`.
- Do not wait with `time.Sleep` in a `-short` test.
- Put an integration test in `tests/integration/` and add `//go:build integration` at the top of every Go file. CI does not run it. `ci-gate` rejects a file without the tag.
- Do not use `SELECT *`, an `INSERT` without a column list or `COPY` in SQL.
- Do not add an alembic migration to main.
- Do not bypass a hook with `--no-verify`.
- Fix a lint warning and a type error; do not suppress it. Do not use `//nolint`. This holds even when the change is unrelated to yours.

## Relation to `main`

- `main` takes only bug fixes. A bug-fix PR on `main` that changes the manager, the agent or the storage proxy carries the label `require:v2-port`, and the same fix is applied to the Go code on `v2`.
- `v2` is not synchronized with `main`.

## Skill index

| Skill | Use when |
|---|---|
| `/knowledge` | Finding or writing background knowledge (`KNOWLEDGE.md`) |
| `/bep-guide` | Designing a feature or writing a BEP |
| `/test-guide` | Agreeing test scenarios and writing or running unit, `-short`, `dbtest.New` and integration tests |
| `/halfstack` | Starting the PostgreSQL for local database tests |
| `/writing` | Writing or changing a document (`AGENTS.md`, `KNOWLEDGE.md`, BEP, skill, README, PR description, long code comment) |
| `/local-review` | A review from another session is needed before opening a PR |
| `/submit` | Committing, creating the changelog fragment and the PR, and checking the CI result |

Skill source: `.claude/skills/{name}/SKILL.md`
