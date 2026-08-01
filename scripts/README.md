# `scripts/`

An index of the top-level scripts, grouped by **when they run** rather than by what
they are about. Each row names its **caller**: a person, or the workflow / hook that
runs it automatically.

`.github/scripts/` holds the scripts that only GitHub Actions and the release
script call; they are listed in the same tables.

Subdirectories are summarized at the end. For the rules on keeping this index
current, see `AGENTS.md` in this directory.

## Setting up a dev environment

| Script | What it does | Called by |
|---|---|---|
| `install-dev.sh` | Bootstraps a full source installation: pants, halfstack, configs, git hooks | person; `integration.yml` |
| `check-docker.py` | Verifies the Docker / Compose setup and reports the preferred pants exec root | auto — `install-dev.sh` |
| `configure-minio.sh` | Configures the MinIO bucket used by the `storage` halfstack profile | auto — sourced by `install-dev.sh` |
| `delete-dev.sh` | Tears down what `install-dev.sh` created | person |
| `install-plugin.sh` | Clones a plugin repository into `./plugins` | person (`docs/dev/daily-workflows.rst`) |
| `setup-dev-completion.sh` | Shell completion for the dev CLI — must be **sourced**, not executed | person |
| `update-to-latest-repo.sh` | Pulls the latest `main` in the legacy `./backend.ai-dev` layout | person |

## During development

| Script | What it does | Called by |
|---|---|---|
| `start-dev.sh` / `stop-dev.sh` | Start / stop every component server in tmux sessions | person |
| `generate-graphql-schema.sh` | Dumps the GraphQL v1/v2 schemas and composes the supergraph | person; `install-dev.sh`, `release.sh`, `refresh-graphql-gateway.sh` |
| `refresh-graphql-gateway.sh` | Regenerates the schema, copies it to the root, restarts the Apollo Router | person |
| `alembic-rebase.py` | Rebases a migration branch when alembic heads have diverged | person (`src/ai/backend/README.md`) |
| `generate-rbac-fixture-permissions.py` | Re-emits the managed permission rows of `fixtures/manager/example-roles.json` | person |
| `download-webui-release.sh` | Downloads and unpacks a WebUI bundle into `src/ai/backend/web` | person; `release.sh` |

## Commit and push

| Script | What it does | Called by |
|---|---|---|
| `pre-commit` | Hook stub copied into `.git/hooks/` — calls `pre-commit.sh` | auto — git, installed by `install-dev.sh` |
| `pre-commit.sh` | `pants fmt` + `pants lint` over the changed files | auto — `pre-commit` |
| `pre-push` | Hook stub copied into `.git/hooks/` — calls `pre-push.sh` | auto — git, installed by `install-dev.sh` |
| `pre-push.sh` | `pants lint/check/test` against the PR's base branch | auto — `pre-push` |
| `hooks/auto-format.sh` | Runs `pants fmt` on the files an AI agent touched | auto — Claude Code hook (per-user settings) |
| `hooks/auto-fix.sh` | Runs `pants fix` on the files an AI agent touched | auto — Claude Code hook (per-user settings) |

## Pull-request CI

| Script | What it does | Called by |
|---|---|---|
| `assign-pr-number.py` | Renames news fragments to the assigned PR number | auto — `assign-pr-number.yml` (via `timeline-check.yml`) |
| `check-multiple-alembic-heads.py` | Fails the build when the migration graph has more than one head | auto — `ci.yml` |
| `check-alembic-revision.py` | Rejects a migration whose `upgrade()` / `downgrade()` is empty | auto — `ci.yml` |
| `get-platform-suffix.py` | Prints the `<os>-<arch>` suffix used in artifact names | auto — `ci.yml`, `build-test.yml` |
| `.github/scripts/decide-backport-targets.sh` | Reads `.github/maintained-versions.yml` and the `Backport:` trailer to decide the target branches | auto — `backport.yml` |
| `update-default-seccomp.sh` | Refreshes `default-seccomp.json` from the upstream moby profile | auto — `update-seccomp-profile.yml` (monthly); person |
| `check-docs-label.sh` | Skips a Read the Docs PR preview build unless the PR carries `area:docs`. **Currently unreferenced** — `.readthedocs.yaml` does the same check inline | — |

## Release

`release.sh` is the entry point; everything under it runs automatically.

| Script | What it does | Called by |
|---|---|---|
| `release.sh` | Cuts a release branch and produces the whole release commit | person |
| `download-external-tools.sh` | Refreshes the bundled external binaries (bssh, all-smi, …) | auto — `release.sh` |
| `freeze_release_version.py` | Replaces `NEXT_RELEASE_VERSION` placeholders with the version being released (skipped for pre-releases) | auto — `release.sh` |
| `run-towncrier.py` | Runs towncrier against the version-branch changelog file | auto — `release.sh` |
| `changelog_files.py` | Module, not a command: maps a version to its `CHANGELOG/<version>.md` | auto — imported by `run-towncrier.py`, `extract-release-changelog.py` |
| `bump_next_release_version.py` | Advances `NEXT_RELEASE_VERSION` to the next sprint after a sprint release | auto — `release.sh` |
| `.github/scripts/update-maintained-versions.sh` | Registers a newly cut line in `.github/maintained-versions.yml` and retires the due ones | auto — `release.sh` |
| `.github/scripts/create-version-branch.sh` | Tags the `X.Y.0rc1` a release commit made and cuts the `X.Y` branch at that same commit | auto — `create-version-branch.yml` |
| `.github/scripts/sync-changelog-to-main.sh` | Opens the pull request carrying a final release's `CHANGELOG/X.Y.md` back to `main` | auto — `changelog-sync.yml` |
| `extract-release-changelog.py` | Extracts the tagged version's block for the GitHub release body | auto — `ci.yml` (release job) |
| `determine-release-type.py` | Sets `IS_PRERELEASE` from the `VERSION` file | auto — `ci.yml` (release job) |
| `build-wheels.sh` | Builds the platform-specific and generic wheels | auto — `ci.yml` (release job) |
| `build-scies.sh` | Builds the scie executables locally (CI runs the equivalent pants commands inline) | person |
| `diff-release.py` | Lists the commits between two refs with their original / backport PR numbers | person |

## Whenever needed

| Script | What it does | Called by |
|---|---|---|
| `pyscript.sh` | Runs a PEP 723 script with uv-managed dependencies | person; `install-dev.sh`, `pre-commit.sh` |
| `python.sh` | Runs a plain Python command through the uv-managed interpreter | person; `install-dev.sh` |
| `tomltool.py` | Gets / sets a key in a TOML file or stream | person; `pre-commit.sh` |
| `add_future_annotations.py` | Adds the missing `from __future__ import annotations` imports | person |
| `validate_ann_compliance.py` | Reports the ANN (flake8-annotations) violations of a path | person |
| `run_mypy_subset.sh` | Runs `pants check` over a subset of paths | person |
| `install.sh` | Downloads the installer binary for the current platform (end-user entry point behind `bnd.ai`) | person |
| `scie-shell.sh` | Opens a Python REPL inside a built scie's pex environment | person |
| `list-all-public-images.py` / `.sh` | Lists the public `lablup/*` images and their tags on Docker Hub | person |
| `monitor-gpu.py` | Watches for missing GPUs on a node and mails an alert | person (ops) |
| `monitor-session-events.py` | Watches session events and mails an alert | person (ops) |

## Subdirectories

| Directory | Contents |
|---|---|
| `agent/` | Cross-build recipes for the static binaries bundled into the kernel runner (dropbear, ttyd, tmux, sftp-server, socket-relay, suexec) plus agent-side deployment helpers |
| `e2e-model-store/` | Numbered end-to-end model-store scenarios, run in order by `run-all.sh` against a live local stack |
| `storage-proxy/` | `upgrade.sh` (storage migration entry point) and the Ceph test-cluster provisioning under `ceph/` |
| `hooks/` | AI-agent hooks; see the "Commit and push" table |
