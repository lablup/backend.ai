# GitHub Actions: Guardrails

> A workflow and the script it calls sit side by side: `workflows/*.yml`, `scripts/*.sh`, `actions/*/action.yml`.
> The script rules below hold for the repository's `scripts/` too, wherever a workflow calls into it.

## Rules

- **Write a script as a function: arguments in, printed value out.** It must not reach for anything it was not given: no CI variable, no ambient file, no "whatever revision happens to be checked out". A caller that has to arrange the surroundings before the script will behave correctly is the shape to avoid.
- **A script reads no `GITHUB_*` variable.** `$GITHUB_ENV`, `$GITHUB_OUTPUT` and `::notice::` are the workflow's business: the script prints the value, the workflow turns it into whatever CI wants.
- **Keep the deciding half free of effects.** Decide from the arguments, print the decision, and only then act. Anything with side effects takes `--dry-run`, and no script leaves the caller's HEAD, index or worktree moved.
- **A workflow translates its event into arguments: nothing more.** Triggers, permissions, concurrency and wiring belong in the YAML. Once a `run:` grows past a line or two, it belongs in `scripts/<verb>-<object>.sh`.
- **One job per outcome.** Split into separate jobs only where the runner, the permissions or a matrix genuinely differ.
- **Do not re-implement a rule that a script already owns**: version parsing, changelog file names, the maintained-version registry. Call it.
- **Do not interpolate `${{ }}` into a shell command.** `env:` carries the value safely as far as the shell: from there hand it to the script as a quoted argument (`env: TAG: ${{ github.ref_name }}` → `run: scripts/foo.py "$TAG"`), so the script never learns the variable's name. A tag name, a branch name and a comment body are all written by someone else.
- **Pin a third-party action to a commit SHA with a `# vN` comment beside it.** `actions/*` may use a major tag.

## Typecheck

- `ci-typecheck.yml` runs `mypy` from the `python-venv` action on the `.py` and `.pyi` files of `typecheck.txt`. It restores `.mypy_cache` and never saves it.
- `mypy-cache.yml` saves `.mypy_cache` as `mypy-main-<sha>` after a full `mypy src tests` on each push to main, and deletes the older `mypy-main-*` entries. Only a push to main saves it.
- A Pants source root `mypy` needs goes in `mypy_path` of `pyproject.toml`.

## Where a decision goes

| In the workflow | In the script |
|-----------------|---------------|
| Which event runs it, and the filters on that event | What to do about it |
| Permissions, `concurrency`, secrets, runner | Every branch, comparison and early exit |
| Event context → arguments (`${{ github.ref_name }}` → `"$TAG"`) | Reading the repository, calling `git` / `gh` / `scripts/*` |
| Turning a printed value into `$GITHUB_ENV` / `$GITHUB_OUTPUT` | Printing that value |

A script whose decision cannot be reproduced by running it by hand is in the wrong shape.

Worked examples: `scripts/sync-changelog-to-main.sh` (arguments, `--dry-run`, plain output) and `scripts/update-maintained-versions.sh` (arguments, in-place rewrite, `TODAY=` to pin the clock).

## CI target plan

`scripts/plan-ci-targets.py` (job `plan-targets` of `ci.yml`) plans the targets of typecheck and each test suite without Pants. Its docstring holds the selection rules.

- The changed files are `git diff --name-only <base-ref>`; the dependents come from `ruff analyze graph --direction dependents` (`RUFF_GRAPH_VERSION`) over `src`, `tests` and `stubs`; the `.pyi` files of `stubs/` are graph nodes. ruff runs with `--isolated` so the `extend-exclude` of `pyproject.toml` does not drop directories; the script fails when the graph nodes differ from `git ls-files src tests stubs` (`.py`, `.pyi`), and a full typecheck lists those files.
- The graph gets three edges Pants adds to import inference: a non-empty `__init__.py` to the modules under it, a `conftest.py` to the tests under it, and a `src/` or `tests/` BUILD `dependencies` entry (also one in an `overrides` entry, for the files it names) to the files of the target listing it. An entry naming a target by address reaches the target's files in two steps, as it does in Pants.
- `python.lock`, `python.lock.metadata`, a `BUILD` under `src/` changed: full run. `pyproject.toml`, `pants.toml`, `stubs/` changed: typecheck of every `.py`. Any other file under `src/` or `tests/` that is not `.py`, `.md` or `.rst` changed (a `BUILD` under `tests/` included): the `.py` files of its directory count as changed.
- The script reads the `python_tests`, `python_test_utils` and `python_sources` calls of the `src/` and `tests/` BUILD files itself and fails on a BUILD it cannot read or on a test file two `python_tests` own.
- `typecheck.txt` lists file paths for mypy (`ci-typecheck.yml`), `unit.<k>.txt` and `component.<k>.txt` the file paths of shard `k` for pytest (`ci-pytest.yml`); `integration.txt` and `scenario.txt` list Pants addresses (`ci-test.yml`, `ci-test-scenario.yml`).
- `unit` and `component` have at most 3 shards (one per 40 and 20 tests). With `--durations` (`test-durations.json`, restored by `plan-targets`) the files are assigned longest first, each to the shard with the smallest total; a file the record lacks counts as the suite's mean, and without a record every file counts as 1 second. The files of shard `k` go to `<suite>.<k>.txt`. `integration` and `scenario` use `crc32(address) % N`.
- A run is a full run (every target) for a tag, a release PR, a push to a version branch (`YY.S`) and a PR whose base is one. `detect-changes` decides it as its output `full-run`.

## Pytest suites

`ci-pytest.yml` runs `unit` and `component` with `scripts/run-pytest-shard.py` in the venv of `actions/python-venv`, without Pants.

- The script runs the files of `--list` (`<suite>.<k>.txt`) with `--workers` pytest processes side by side, each with its own `BACKEND_TEST_EXEC_SLOT`. Both suites run batches of files (`workers` * 2 of them).
- `PYTHONPATH` is the `[tool.mypy] mypy_path` entries of `pyproject.toml` except `stubs`, then the repository root. A source root is added in `pants.toml` and `mypy_path` only.
- The pytest options follow `[test]` in `pants.toml`: `--timeout=180`, `--reruns=1`.
- Each process writes a junit report, uploaded as the artifact `junit-<suite>-<job index>`. The script writes the totals and the failed tests to the job summary and prints an `::error` annotation for each failed test.

## Test durations

- `test-record.yml` runs every `unit` and `component` test on each push to main (`plan-ci-targets.py --full-run`, then `ci-pytest.yml`), sums the testcase `time` of each file from the junit reports with `scripts/compute-test-durations.py`, and saves `test-durations.json` (`{"<suite>": {"<path>": <seconds>}}`) as `test-durations-main-<sha>`. The older `test-durations-main-*` entries are deleted. A failed test fails the run after the save.
- `plan-targets` of `ci.yml` restores the newest `test-durations-main-*` and passes it to `plan-ci-targets.py --durations`. Only a push to main saves it.

## Go (`v2`)

- `ci-go.yml` runs on pull requests into and pushes to `v2`. The Python workflows (`ci.yml`, `timeline-check.yml`, `check-version-change.yml`, `update-api-schema.yml`, `docs-preview.yml`, `knowledge-check.yml`) list `branches-ignore: [v2]`. A new workflow that assumes Python does the same.
- `go-ci-gate` collects `go-fmt`, `go-lint` and `go-build` on a pull request. `go-test-short` and `go-generate-diff` report without being in the gate. `go-test` (with `-race` and Postgres) runs on a push only.
- The Go caches (`GOCACHE`, `GOMODCACHE`) are restored by `actions/go-setup` and saved by each job on a push only: key `go-<job>-<os>-<sha>`, restored by the prefix.
- A push to `v2` where `go generate ./...` changes files opens the pull request `go-generate/v2` with `.github/scripts/open-go-generate-pr.sh`.
