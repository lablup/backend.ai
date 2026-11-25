# `scripts/`

An index of the top-level scripts, arranged by **when they run** rather than by what
they are about. Each row names its **caller**: a person, or the workflow / hook that
runs it automatically.

`.github/scripts/` holds the scripts that only GitHub Actions and the release
script call; they are listed in the same tables.

Subdirectories are summarized at the end. For the rules on keeping this index
current, see `AGENTS.md` in this directory.

## Setting up a dev environment

| Script | What it does | Called by |
|---|---|---|
| `install-dev.sh` | Installs a full source setup: Pants, halfstack, configs, git hooks | person |
| `setup-venv.py` | Builds the python-default virtualenv from `python.lock` without Pants, at the path `pants export` writes (`--venv <dir>` overrides) and fails when a package differs from the lock | person |
| `check-docker.py` | Verifies the Docker and Compose setup and reports the preferred Pants exec root | auto: `install-dev.sh` |
| `configure-minio.sh` | Configures the MinIO bucket used by the `storage` halfstack profile | auto: sourced by `install-dev.sh` |
| `delete-dev.sh` | Tears down what `install-dev.sh` created | person |
| `install-plugin.sh` | Clones a plugin repository into `./plugins` | person (`docs/dev/daily-workflows.rst`) |
| `setup-dev-completion.sh` | Shell completion for the dev CLI. Source it, do not execute it | person |
| `update-to-latest-repo.sh` | Pulls the latest `main` in the legacy `./backend.ai-dev` layout | person |

## During development

| Script | What it does | Called by |
|---|---|---|
| `start-dev.sh` / `stop-dev.sh` | Start or stop every component server in tmux sessions | person |
| `generate-graphql-schema.sh` | Dumps the GraphQL v1 and v2 schemas and composes the supergraph | person; `install-dev.sh`, `release.sh`, `refresh-graphql-gateway.sh` |
| `refresh-graphql-gateway.sh` | Regenerates the schema, copies it to the root and restarts the Apollo Router (`--recreate` recreates the container so config updates apply) | person |
| `alembic-rebase.py` | Rebases a migration branch when alembic heads have diverged | person (`src/ai/backend/README.md`) |
| `download-webui-release.sh` | Downloads and unpacks a WebUI bundle into `src/ai/backend/web` | person; `release.sh` |
| `new-changelog.py` | Writes a changelog fragment named `changes/<YYYYMMDD>-<HHMMSS>-<6 chars>.<type>.md`, with front matter for `--issue` and `--epic`, and prints its path | person; Claude Code (`/submit`) |
| `knowledge/search.py` | Lists or searches `KNOWLEDGE.md` frontmatter across the repository | person; Claude Code (`/knowledge`) |

## Commit and push

| Script | What it does | Called by |
|---|---|---|
| `pre-commit` | Hook stub copied into `.git/hooks/` that calls `pre-commit.sh` | auto: git, installed by `install-dev.sh` |
| `pre-commit.sh` | Runs `ruff format`, `ruff check` and `flake8` over the staged Python and BUILD files with the `lint` group of `pyproject.toml` installed into `dist/lint-venv`, and `golangci-lint fmt` and `run --fast-only --new-from-rev HEAD` when a `.go` file is staged | auto: `pre-commit` |

## Pull-request CI

| Script | What it does | Called by |
|---|---|---|
| `validate-changelog-fragments.py` | Checks the names, types, front matter and epic file pairs in `changes/` | person |
| `check-multiple-alembic-heads.py` | Fails the build when the migration graph has more than one head | person |
| `check-alembic-revision.py` | Rejects a migration whose `upgrade()` / `downgrade()` is empty | person |
| `knowledge/check.py` | Validates `KNOWLEDGE.md` frontmatter, paths, and body links | person |
| `knowledge/check_bilingual.py` | Validates `.md` and `.ko.md` pairs and rejects Korean added to a `.md` file | person |
| `knowledge/check_words.py` | Finds the words the glossary rejects in added document lines or given files | person |
| `knowledge/check_bep_length.py` | Checks the length limits of BEP-1080 and later BEPs: lines, list items, design subsections | person |
| `get-platform-suffix.py` | Prints the `<os>-<arch>` suffix used in artifact names | person |
| `.github/scripts/open-go-generate-pr.sh` | Opens a `skip:changelog` pull request with the files `go generate ./...` changed on a push to `v2` | auto: `ci.yml` |
| `.github/scripts/delete-ref-caches.sh` | Deletes every cache entry under a ref, such as a closed pull request's | auto: `cleanup-pr-caches.yml` |
| `update-default-seccomp.sh` | Refreshes `default-seccomp.json` from the upstream moby profile | person |
| `check-docs-label.sh` | Skips a Read the Docs PR preview build unless the PR carries `area:docs`. **Currently unreferenced**: `.readthedocs.yaml` does the same check inline | none |

## Release

`release.sh` is the entry point; everything under it runs automatically.

| Script | What it does | Called by |
|---|---|---|
| `release.sh` | Cuts a release branch and produces the whole release commit | person |
| `download-external-tools.sh` | Refreshes the bundled external binaries (bssh, all-smi, …) | auto: `release.sh` |
| `freeze_release_version.py` | Replaces `NEXT_RELEASE_VERSION` placeholders with the version being released (skipped for pre-releases) | auto: `release.sh`, `.github/scripts/bump-next-release-on-main.sh` |
| `rename-changelog-fragments.py` | Renames each new-style changelog fragment to `<PR-number>.<type>.md` with `git mv` and drops its front matter, taking the PR number from the commit that added the file; stops the release on a file that breaks the rules or has no PR number | auto: `release.sh` |
| `run-towncrier.py` | Runs towncrier against the version-branch changelog file | auto: `release.sh` |
| `changelog_fragments.py` | Module, not a command: the rules for the files in `changes/` (names, types, front matter, epic files) | auto: imported by `new-changelog.py`, `rename-changelog-fragments.py`, `validate-changelog-fragments.py`, `run-towncrier.py` |
| `changelog_files.py` | Module, not a command: maps a version to its `CHANGELOG/<version>.md` | auto: imported by `run-towncrier.py`, `extract-release-changelog.py` |
| `bump_next_release_version.py` | Rewrites or prints `NEXT_RELEASE_VERSION` in `meta.py` | auto: `.github/scripts/bump-next-release-on-main.sh` |
| `.github/scripts/update-maintained-versions.sh` | Registers a newly cut release line in `.github/maintained-versions.yml` and retires the due ones | auto: `release.sh` |
| `extract-release-changelog.py` | Extracts the tagged version's block for the GitHub release body; fails when it exceeds GitHub's 125,000-character limit | person |
| `list-dockerfiles.sh` | Prints the `docker/` dockerfile build matrix (`--service` / `--infra`) as JSON; a new `backend.ai-*` dockerfile must be registered in its allowlist | auto: `osv-scanner.yml` |
| `check-bake-targets.sh` | Fails when `docker-bake.hcl`'s default group and the `list-dockerfiles.sh --service` registry drift apart | person |
| `determine-release-type.py` | Prints `RELEASE_AUDIENCE` and `IS_PRERELEASE` for the `VERSION` file; rejects a version that is neither an alpha, a release candidate nor a final release | person |
| `test_determine_release_type.py` | Checks `determine-release-type.py` against every classified and rejected version | person |
| `test_freeze_release_version.py` | Checks `freeze_release_version.py` against standalone, one-line and multi-line imports | person |
| `normalize-version.py` | Prints the PEP 440-normalized version used for docker image tags, rejecting local segments (`+` is not a legal docker tag character) | person |
| `build-wheels.sh` | Builds the platform-specific and generic wheels | person |
| `build-scies.sh` | Builds the scie executables locally (CI runs the equivalent pants commands inline) | person |
| `diff-release.py` | Lists the commits between two refs with their original and backport PR numbers | person |

## Whenever needed

| Script | What it does | Called by |
|---|---|---|
| `pyscript.sh` | Runs a PEP 723 script with uv-managed dependencies | person; `install-dev.sh` |
| `python.sh` | Runs a plain Python command through the uv-managed interpreter | person; `install-dev.sh` |
| `tomltool.py` | Gets or sets a key in a TOML file or stream | person; `install-dev.sh` |
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
| `agent/` | Cross-build recipes for the static binaries bundled into the kernel runner (dropbear, ttyd, tmux, sftp-server, socket-relay, suexec), the glibc stub libraries, and agent-side deployment helpers |
| `e2e-model-store/` | Numbered end-to-end model-store scenarios, run in order by `run-all.sh` against a live local stack |
| `storage-proxy/` | `upgrade.sh` (storage migration entry point) and the Ceph test-cluster provisioning under `ceph/` |
| `knowledge/` | `KNOWLEDGE.md` tooling: shared frontmatter parser, `search.py`, `check.py`, `check_bilingual.py`, `check_words.py`, `check_bep_length.py` |
