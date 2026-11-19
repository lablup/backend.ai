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

- The changed files are `git diff --name-only <base-ref>`; the dependents come from `ruff analyze graph --direction dependents` (`RUFF_GRAPH_VERSION`).
- The graph gets three edges Pants adds to import inference: a non-empty `__init__.py` to the modules under it, a `conftest.py` to the tests under it, and a `tests/` BUILD `dependencies` entry to the files of the target listing it. An entry naming a target by address reaches the target's files in two steps, as it does in Pants.
- `python.lock`, `python.lock.metadata` changed: full run. `pyproject.toml`, `pants.toml`, `stubs/` changed: typecheck of every `.py`. A non-`.py` file under `src/` or `tests/` changed: the `.py` files of its directory count as changed.
- The script reads the `python_tests` calls of the `tests/` BUILD files itself and fails on a BUILD it cannot read or on a test file two `python_tests` own.
- The spec files keep Pants addresses (tests) and file paths (typecheck), so `ci-typecheck.yml`, `ci-test.yml` and `ci-test-scenario.yml` stay the same.
