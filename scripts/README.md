# `scripts/`

An index of the top-level scripts, arranged by **when they run** rather than by what
they are about. Each row names its **caller**: a person, or the workflow / hook that
runs it automatically.

`.github/scripts/` holds the scripts that only GitHub Actions calls; they are listed
in the same tables. For the rules on keeping this index current, see `AGENTS.md` in
this directory.

## Installing the git hook

Run one of these once per clone, from the repository root.

| Method | Command | Effect |
|---|---|---|
| Hooks path | `git config core.hooksPath scripts` | git runs the hooks in `scripts/` in place of the ones in `.git/hooks/` |
| Symlink | `ln -s "$PWD/scripts/pre-commit" "$(git rev-parse --git-path hooks)/pre-commit"` | The other hooks in `.git/hooks/` keep running |

## Commit

| Script | What it does | Called by |
|---|---|---|
| `pre-commit` | The git hook: calls `pre-commit.sh` | auto: git, once installed |
| `pre-commit.sh` | Runs `go tool golangci-lint fmt` and `run --fast-only --new-from-rev HEAD` when a `.go` file is staged, `go run ./tools/changelog check` when a file in `changes/unreleased/` is staged, and `go run ./tools/doclint check --staged` when a `.md` file, a file in `glossary/registry/` or `doclint.yaml` is staged | auto: `pre-commit` |

On a merge commit `pre-commit.sh` skips the document check: the pull request CI of each parent checks its documents.

## Pull-request CI

| Script | What it does | Called by |
|---|---|---|
| `.github/scripts/check-removed-files.sh` | Fails when a file matching one of the given name patterns is in the repository | auto: `ci.yml` |
| `.github/scripts/check-build-tag.sh` | Fails when a Go file of the given packages is in the default build, that is, lacks the build tag | auto: `ci.yml` |
| `.github/scripts/open-go-generate-pr.sh` | Opens a `skip:changelog` pull request with the files `go generate ./...` changed on a push to `v2` | auto: `ci.yml` |
| `.github/scripts/cancel-superseded-runs.sh` | Cancels the workflow runs that a newer push to the same branch superseded | auto: `cancel-superseded.yml` |
| `.github/scripts/delete-ref-caches.sh` | Deletes every cache entry under a ref, such as a closed pull request's | auto: `cleanup-pr-caches.yml` |

## Release

| Script | What it does | Called by |
|---|---|---|
| `.github/scripts/build-release.sh` | Builds every `main` package under `cmd/` for linux amd64 and arm64 | auto: `release.yml` |
