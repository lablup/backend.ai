# Build System & Development Commands

This project uses **Pantsbuild** (version 2) for build automation and dependency management.
All development commands use `pants` instead of `pip`, `poetry`, or `uv`.

## BUILD Files Policy

**CRITICAL RULES:**

### Source Code (`src/` directory)
- ❌ **NEVER add BUILD files for new Python modules or packages**
- Pants automatically detects Python files without explicit BUILD declarations
- Only top-level component BUILD files exist (e.g., `src/ai/backend/manager/BUILD`)
- These are maintained by maintainers and rarely need updates

### Test Code (`tests/` directory)
- ✅ **MUST add BUILD files for new test directories**
- Use `python_tests()` for test modules
- Use `python_testutils()` for shared test utilities
- Do NOT explicitly list dependencies - Pants infers them from imports

**When to Update BUILD Files:**
- Creating new test directories → Add `BUILD` with `python_tests()`
- Adding test utilities → Add `BUILD` with `python_testutils()`
- Never for source code changes

## Quality Enforcement

**Absolute Rule: Fix all quality issues immediately**

* **Never suppress linter and type checker errors**
  - Do NOT use `# noqa` comments to suppress linter warnings
  - Do NOT use `# type: ignore` comments to suppress type checker errors
  - Fix the root cause instead:
    - Restructure code to avoid the issue
    - Add proper type annotations
    - Refactor to eliminate circular dependencies
  - Only use suppression comments as a last resort with clear justification

* **Fix all quality issues discovered during development**
  - When lint, type check, or test errors are discovered, fix them immediately
  - This applies even if the errors are unrelated to your current work
  - Do not skip or ignore quality issues with reasoning "it's not part of my change"
  - Maintaining codebase quality is a shared responsibility

## Automated Quality Checks

### Claude Code Hooks (`.claude/settings.local.json`, gitignored)
- **PostToolUse**: Runs `pants fmt` after Edit/Write operations
- **Stop**: Runs `pants fix` on modified Python files when Claude finishes

### Git Pre-commit Hook (`scripts/pre-commit.sh`)
- Runs on every `git commit`
- Validates: `pants lint`, `pants check` on changed files
- Bypass with `git commit --no-verify` for WIP commits (never on main/release branches)

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
- Changed + dependents: `--changed-dependents=transitive --changed-since=HEAD~1`

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

**Using Skills** (Recommended):
- `/cli-executor` - Interactive guide with pre-flight checks

**Manual Execution:**
```bash
# Run component CLI
./backend.ai {component} {subcommand}

# Execute Python module in project virtualenv
./py -m {module}
```

See `.claude/skills/cli-executor/SKILL.md` for detailed operations.

## Database Schema Management

This project uses Alembic for three separate databases.

**Using Skills** (Recommended):
- `/db-status` - Check schema version and migration status
- `/db-migrate` - Apply pending migrations

**Manual Execution:**
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
- Check if you're in `tests/` directory → Add BUILD file with `python_tests()`
- Check if you're in `src/` directory → Do NOT add BUILD file

### "Import cannot be inferred"
- Ensure imported module exists
- Check for typos in import path
- Verify the module has proper `__init__.py` if needed

### Lock File Conflicts
- Run `pants generate-lockfiles --resolve=python-default`
- Then `pants export --resolve=python-default`

### Type Check Errors
- Fix the root cause - do NOT use `# type: ignore`
- Add proper type annotations
- Use `typing.cast()` for unavoidable cases with justification

For component-specific guidance, see:
- `/cli-executor` - Component CLI operations
- `/db-status`, `/db-migrate` - Database operations
- `tests/CLAUDE.md` - Testing guidelines
