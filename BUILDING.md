# Build System and Development Commands

This project uses **Pants** (version 2) for build automation and dependency management.
All development commands use `pants` instead of `pip`, `poetry`, or `uv`.

## BUILD Files Policy

**Critical rules:**

### Source Code (`src/` directory)
- **Do not add BUILD files for new Python modules or packages**
- Pants automatically detects Python files without explicit BUILD declarations
- Only top-level component BUILD files exist (for example, `src/ai/backend/manager/BUILD`)
- Maintainers own these files and rarely update them

### Test Code (`tests/` directory)
- **Must add BUILD files for new test directories**
- Use `python_tests()` for test modules
- Use `python_testutils()` for shared test utilities
- Do not list dependencies explicitly; Pants infers them from imports

**When to Update BUILD Files:**
- Creating new test directories → Add `BUILD` with `python_tests()`
- Adding test utilities → Add `BUILD` with `python_testutils()`
- Do not add them for source code changes

## Quality Enforcement

**Fix all quality issues immediately, without exception.**

* **Do not suppress linter and type checker errors**
  - Do not use `# noqa` comments to suppress linter warnings
  - Do not use `# type: ignore` comments to suppress type checker errors
  - Fix the root cause instead:
    - Restructure code to avoid the issue
    - Add proper type annotations
    - Refactor to eliminate circular dependencies
  - Use suppression comments only as a last resort with clear justification

* **Fix all quality issues discovered during development**
  - Fix lint, type check, or test errors as soon as you find them
  - This applies even when the errors are unrelated to your current work
  - Do not skip quality issues because they are not part of your change
  - Maintaining codebase quality is a shared responsibility

## Automated Quality Checks

### Claude Code Hooks (`.claude/settings.local.json`, gitignored)
- **PostToolUse**: Runs `pants fmt` after Edit/Write operations
- **Stop**: Runs `pants fix` on modified Python files when Claude finishes

### Git Pre-commit Hook (`scripts/pre-commit.sh`)
- Runs on every `git commit`
- Runs `ruff format` and `ruff check` on staged Python files through `uvx`, with the ruff version from `pants.toml`
- Shell lint and visibility rules run only in CI (`pants lint`)
- CI handles type checking and tests (`ci.yml` lint-and-typecheck and test jobs)
- Bypass with `git commit --no-verify` for work-in-progress commits, but not on main or release branches

## Running Pants Commands

**Basic Structure:**
```bash
pants {global-options} {subcommand} {subcommand-options} {targets}
pants {subcommand} {targets} -- {arguments-passed-to-spawned-processes}
```

**Global Options:**
- `--no-colors`: Remove color codes (useful for piped output)
- `--no-dynamic-ui`: Remove progress bars (useful for piped output)

**Target Patterns:**
- All files: `::`
- Directory subtree: `path/to/subpkg::`
- Changed files: `--changed-since=HEAD~1`
- Changed and dependents: `--changed-dependents=transitive --changed-since=HEAD~1`

## Common Commands

### Code Quality
```bash
# Format code
pants fmt ::

# Fix auto-fixable issues (removes unused imports, etc.)
pants fix ::

# Lint code
pants lint --changed-since=HEAD~1

# Type check
pants check --changed-since=HEAD~1

# Run tests
pants test tests/manager::
```

### Dependency Management

**Lock Files:**
- `python.lock` - Main source tree dependencies (python-default)
- `tools/*.lock` - Tool-specific dependencies (mypy, ruff, black, pytest)

**Commands:**
```bash
# Export Python virtualenv for development
pants export --resolve=python-default

# Update lock files after requirements.txt changes
pants generate-lockfiles --resolve=python-default

# Re-export virtualenv after lock file update
pants export --resolve=python-default
```

### Running Project Entrypoints

**Using skills** (recommended):
- `/cli-executor` - Interactive guide with pre-flight checks

**Manual execution:**
```bash
# Run component CLI
./backend.ai {component} {subcommand}

# Execute Python module in project virtualenv
./py -m {module}
```

See `.claude/skills/cli-executor/SKILL.md` for detailed operations.

## Database Schema Management

This project uses Alembic for three separate databases.

**Using skills** (recommended):
- `/db-status` - Check schema version and migration status
- `/db-migrate` - Apply pending migrations

**Manual execution:**
```bash
./py -m alembic -c {alembic-ini-path} {command}
```

**Available Configs:**
- `alembic.ini` - Manager database
- `alembic-accountmgr.ini` - Account manager database
- `alembic-appproxy.ini` - App proxy database

See `.claude/skills/db-status/SKILL.md` and `.claude/skills/db-migrate/SKILL.md` for details.

## Troubleshooting

### "No BUILD file found"
- Check whether you are in the `tests/` directory → Add a BUILD file with `python_tests()`
- Check whether you are in the `src/` directory → Do not add a BUILD file

### "Import cannot be inferred"
- Ensure the imported module exists
- Check for typos in the import path
- Check whether the module has a proper `__init__.py` if needed

### Lock File Conflicts
- Run `pants generate-lockfiles --resolve=python-default`
- Then run `pants export --resolve=python-default`

### Type Check Errors
- Fix the root cause; do not use `# type: ignore`
- Add proper type annotations
- Use `typing.cast()` for unavoidable cases with justification

For component-specific guidance, see:
- `/cli-executor` - Component CLI operations
- `/db-status`, `/db-migrate` - Database operations
- `tests/AGENTS.md` - Testing guidelines
