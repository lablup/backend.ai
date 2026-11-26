# GitHub Actions: Guardrails

> A workflow and the script it calls sit side by side: `workflows/*.yml`, `scripts/*.sh`, `actions/*/action.yml`.
> The script rules below hold for the repository's `scripts/` too, wherever a workflow calls into it.

## Rules

- **Write a script as a function: arguments in, printed value out.** It must not reach for anything it was not given: no CI variable, no ambient file, no "whatever revision happens to be checked out". A caller that has to arrange the surroundings before the script will behave correctly is the shape to avoid.
- **A script reads no `GITHUB_*` variable.** `$GITHUB_ENV`, `$GITHUB_OUTPUT` and `::notice::` are the workflow's business: the script prints the value, the workflow turns it into whatever CI wants.
- **Keep the deciding half free of effects.** Decide from the arguments, print the decision, and only then act. Anything with side effects takes `--dry-run`, and no script leaves the caller's HEAD, index or worktree moved.
- **A workflow translates its event into arguments: nothing more.** Triggers, permissions, concurrency and wiring belong in the YAML. Once a `run:` grows past a line or two, it belongs in `scripts/<verb>-<object>.sh`.
- **Write a script with decision logic, HTTP calls or JSON processing in Go as `tools/<name>`.** A script that only chains a few commands is `scripts/<verb>-<object>.sh`. Move a shell script to Go once it grows long or takes on a decision.
- **One job per outcome.** Split into separate jobs only where the runner, the permissions or a matrix genuinely differ.
- **Do not re-implement a rule that a script already owns.** Call it.
- **Do not interpolate `${{ }}` into a shell command.** `env:` carries the value safely as far as the shell: from there hand it to the script as a quoted argument (`env: TAG: ${{ github.ref_name }}` → `run: scripts/foo.sh "$TAG"`), so the script never learns the variable's name. A tag name, a branch name and a comment body are all written by someone else.
- **Pin a third-party action to a commit SHA with a `# vN` comment beside it.** `actions/*` may use a major tag.

## Where a decision goes

| In the workflow | In the script |
|-----------------|---------------|
| Which event runs it, and the filters on that event | What to do about it |
| Permissions, `concurrency`, secrets, runner | Every branch, comparison and early exit |
| Event context → arguments (`${{ github.ref_name }}` → `"$TAG"`) | Reading the repository, calling `git` / `gh` / `scripts/*` |
| Turning a printed value into `$GITHUB_ENV` / `$GITHUB_OUTPUT` | Printing that value |

A script whose decision cannot be reproduced by running it by hand is in the wrong shape.

## CI (`v2`)

- `ci.yml` runs on pull requests into and pushes to `v2`. The Python workflows are deleted on `v2`; a `pull_request` event runs the workflow files of the merge commit, so `main` keeps its own.
- Put the jobs of one trigger and purpose in one workflow file: the checks of a pull request and a push to `v2` in `ci.yml`, a tag release in `release.yml`.
- The required check is one status-collecting job, `ci-gate` (`if: always()`). Do not put a `paths` filter on a workflow that holds a required check.
- When two workflows need the same job, move it to a reusable workflow (`workflow_call`). `test.yml` (the full test) is called by `ci.yml` on a push to `v2` and by `release.yml`.
- The Go setup is the composite action `go-setup`. The decision on the event and the branch stays in the workflow YAML.
- The pull request gate is `fmt`, `lint` and `build`. `test-short` and `generate-diff` report on a pull request without being in the gate. The full test (`test`, with `-race` and Postgres) runs on a push to `v2` and on a release.
- `release.yml` runs on a release tag push (the pattern is a placeholder until the transition). Its `build` job needs `test`, builds each `main` package under `cmd/` for linux amd64 and arm64 with `.github/scripts/build-release.sh`, and uploads them as the `binaries` artifact. It does not publish images, create a GitHub release or publish packages.
- The `build` job runs `.github/scripts/check-removed-files.sh` with the file name patterns `ci.yml` passes: it fails when a matching file is in the repository.
- On a pull request the `build` job runs `go run ./tools/doclint check`. The label `allow:one-side-doc` passes `--allow-one-side`: a change to one document of a `.md`/`.ko.md` pair is reported for review instead of failing. Adding or removing a label reruns `ci.yml`.
- The `build` job runs `go run ./tools/changelog check`. A release batches `changes/unreleased/` with `go run ./tools/changelog batch <version> --allow-empty` in the `changelog` job and uploads `changes/<version>.md` as the `changelog` artifact. Fragments: `changes/README.md`.
- The `build` job runs `.github/scripts/check-build-tag.sh './tests/integration/...'`: it fails when a Go file under `tests/integration/` lacks the `integration` build tag.
- The Go caches (`GOCACHE`, `GOMODCACHE`) are restored by `actions/go-setup` and saved by each job on a push only: key `<job>-<os>-<sha>`, restored by the prefix.
- A push to `v2` where `go generate ./...` changes files opens the pull request `go-generate/v2` with `.github/scripts/open-go-generate-pr.sh`.
- Read the Docs skips the docs build on `v2`: the root `.readthedocs.yaml` exits `183` in `build.commands`, which cancels the build (BAI-1162 restores it).
- `nvd-cve-watch.yml` runs `go run ./tools/cvewatch find` and `notify`. The script rules above hold for that tool. Its run log is public: `notify` prints only the number of CVEs sent, and its errors do not carry the webhook URL.
- The other workflows: `pr-prefix.yml`, `auto-author-assign.yml`, `cancel-superseded.yml` (cancels superseded `ci.yml` runs), `cleanup-pr-caches.yml`, `stale-pr.yml`, `devskim.yml`, `osv-scanner.yml`, `nvd-cve-watch.yml`.
- `osv-scanner.yml` scans `go.mod` for vulnerabilities on a schedule and on pushes to `main` and `v2`. It scans no container image.
- `devskim.yml` runs on a schedule and on pushes to `main` and `v2`.
