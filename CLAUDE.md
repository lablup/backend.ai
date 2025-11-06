# Coding guidelines for AI Coding Agents

This file provides guidance to AI coding agents when working with code in this repository.


## Project Overview

Read `README.md` for overall architecture and purpose of directories.

This project uses a monorepo structure containing multiple Python pacakges under `ai.backend` namespace.
Consult `src/ai/backend/{package}/README.md` for package-specific descriptions.


## README-First Development

**Always read the component README before making changes.**

Key README locations:
- Component: `src/ai/backend/{component}/README.md`
- Manager sub-components: `manager/sokovan/`, `manager/services/`, `manager/repositories/`

Update README when:
- Adding new components, services, repositories, or APIs
- Changing architecture or component dependencies
- Adding new directories or significant structural changes

Example: Adding a new service → Read `services/README.md` → Follow patterns → Update service index


## General

### Tidy First Approach

* Separate all changes into two distinct types:
  - STRUCTURAL CHANGES: Rearranging code without changing behavior (renaming, extracting methods, moving code)
  - BEHAVIORAL CHANGES: Adding or modifying actual functionality
* Never mix structural and behavioral changes in the same commit
* Always make structural changes first when both are needed
* Validate structural changes do not alter behavior by running tests before and after

### Code Quality

* Maintain high code quality throughout development
* Eliminate duplication ruthlessly
* Keep methods small and focused on a single responsibility
* Minimize state and side effects
* Use the simplest solution that could possibly work
* Make dependencies explicit
  - Use relative imports when referring to modules in a subtree under `src` sharing a single BUILD file
  - Use absolute imports when referring to modules in other subtrees under `src`, 3rd-party packages, and Python intrinsic packages
* Express intent clearly through naming and structure
* Name things with meaningful, predictable, and explicit but concise tones
  - When reading codes, variable names should align with what intermediate-level developers could expect from them.
  - The words in names should follow adjectives/descriptives and nouns in a meaningful order.
    - Example: `container_user_info` vs. `user_container_info` means completely different things.
      The former represents container-specific "user" information,
      while the latter represents user-specific "container" information.
  - Legacy stuffs should have distinguishable names
  - Be cautious when naming similar but different stuffs to avoid reader's confusion
* Avoid replicating legacy patterns when writing new codes
  - Stick to the user prompts about the new code patterns

### Working with Long Contexts

* Store and consult the user request, your analysis and plans in `.claude/tasks/{job-slug}.md`
  when the user request is expected to require a long context
  - Example: `./claude/tasks/refactor-sokovan-scheduler.md`
* Split large work into step by step sprints
* Update the current design and next plans in `{job-slug}.md` when completing a sprint
* Do not make changes beyond those originally asked for but explicitly proceed with user confirmation

### Python Specifics

* **Latest Syntax and Patterns**: No need to add branches or fallbacks for Python 3.11 or older
  - Use the pattern matching syntax when there are self-repeating if-elif statements
* **Async-first**: All I/O operations use async/await
* **Type Hints**: Comprehensive type annotations required
  - Put `from __future__ import annotations` if not exists and do not stringify type annotations
  - Use `typing.TYPE_CHECKING` to import annotation-only references to avoid circular imports and break deep dependency chains between Python modules
  - Use `typing.cast()` sparingly but explicitly specify the types in the LHS of assignments when the RHS expression is `Any` or has unknown types
  - DO NOT forget adding return type annotations of all functions and methods
  - Use `collections.abc` when referring to generic collection/container types such as `Mapping`, `Sequence`, `Iterable`, `Awaitable`, etc.
* **Structured Logging**: Use `ai.backend.logging.BraceStyleAdapter` for consistent logging
* **Configuration**: Use Pydantic models for validation and serilization for configurations and DTOs
* **Error Handling**: Comprehensive exception handling with proper logging

### Directory Conventions

- Packages in `src/ai/backend/{package}` directories
- Database schema in `src/ai/backend/{package}/models`
- Data access and manipulation models in `src/ai/backend/{package}/repositories`
- Connectors and client wrappers to external services and other packages in `src/ai/backend/{package}/clients`
- Reusable business logic for individual features in `src/ai/backend/{package}/services`
- API handlers and endpoints in `src/ai/backend/{pacakge}/api`
- Component-specific local CLI commands based on Click in `src/ai/backend/{package}/cli`
- Client SDK and CLI as the server-side API counterpart in `src/ai/backend/client`
- Unit tests in `tests/{package}` subdirectories and written in pytest
- Integration tests in `src/ai/backend/test`
- Reusable helper utilities for testing in `src/ai/backend/testutils`

### Python Module Conventions

- `types.py`: Reusable type definitions such as pydantic models, dataclasses, enums, and constants annotated with `typing.Final`.
- `abc.py`: Abstract base classes (ABCs) providing pure interfaces
- `base.py`: Base classes providing shared, partial, reusable implementation for subclasses
- `utils.py`: Reusable helper functions that are out of scope of the core logic or minor details
- If the types or utilities could be shared with other `ai.backend` namespace packages, put them in the `ai.backend.common` package.

### Writing Tests

* Write the simplest failing test first
  - Let tests verify the intention rather than direct inputs and outputs
  - Avoid duplicating the original logic in tests
* Implement the minimum code needed to make tests pass while preserving the design intention
  - Avoid making simple branches just to satisfy test input combinations, but think about the fundamental fix
* Refactor only after tests are passing
* Use the tester subagent to run and write tests considering the general guides in this document
  - `integration`: for tests requiring externally provisioned resources
  - `asyncio`: for tests using async/await codes
* Always add type annotations to test codes
  - Add argument type annotations to the fixture references in test functions
  - Add return type annotations to the fixture functions
  - Add return type annotation (`-> None`) to the test functions
* Utilize `typing.Protocol` and `typing.TypedDict` when typing mocked objects and functions if applicable
  - When using partial data structures, use `typing.cast()` to minimal scopes.
* Add BUILD files including `python_tests()` and `python_test_utils()` appropriately depending on the directory contents
* Prefer pytest-style module-level test functions rather than unittest-style test classes

## Build System & Development Commands

This project uses **Pantsbuild** (version 2) and Python as specified in the `pants.toml` configuration.
All development commands use `pants` instead of `pip`, `poetry`, or `uv` commands.

### Predefined sub-agents

There are predefined sub-agents for this project: linter, typechecker, and tester.
Use them proactively as their description specifies.

### Running generic pants commands

Most pants command accepts a special target argument which can indicate a set of files or the files
changed for a specific revision range with optional transitive dependent files of the changed files.

**Basic structure of pants commands:**
```bash
pants {global-options} {subcommand} {subcommand-options} {targets}
pants {global-options} {subcommand} {subcommand-options} {targets} -- {arguments-and-options-passed-to-spawned-processes}
```

**Global options:**
- `--no-colors`: Recommended to ensure non-colored output for reading console output via pipes
- `--no-dynamic-ui`: Recommended to remove progress outputs for reading console output via pipes

**Targets:**
- All files: `::`
- All files under specific directory of the dependency tree: `path/to/subpkg::`
- Files changed after the last commit: `--changed-since=HEAD~1` (here, the revision range syntax is that used by Git)
- Files changed after the last commit and their dependent files as inferred: `--changed-dependents=transitive` (this option must be used with `--changed-since`)

### Adding new packages and modules

When adding new packages and modules, ensure that `BUILD` files are present in their directories so that the Pantsbuild system could detect them.

- Under the `src` directory, generate or update the top-level `BUILD` files in each package (e.g., `src/ai/backend/manager/BUILD`, `src/ai/backend/appproxy/coordinator/BUILD`, `src/ai/backend/agent/BUILD`) referring to sibling package's `BUILD` files.
- Under the `tests` directory, use `python_tests()` and/or `python_testutils()`.

The `BUILD` files must be created or updated BEFORE running linting, typecheck, and tests via the `pants` command.

### Dependency Management using Lock files

The project uses separate lock files for different tool resolves:
- `python.lock` - Main source tree dependencies (python-default)
- `tools/*.lock` - Tool-specific dependencies (mypy, ruff, black, pytest, etc.)

Regenerate lock files when dependencies change:
```bash
# Populating the virtual environment from a specific resolve set
pants export --resolve=python-default   # Export Python virtual environment for the main source tree

# Updating the package dependencies after updating requirements.txt
# After this command, you need to re-run `pants export` with the same resolve name to refresh the virtualenv.
pants generate-lockfiles --resolve=python-default
```

### Running Project Entrypoints

Use the special entrypoint script `./backend.ai` to execute project-specific CLI commands like:
```bash
./backend.ai mgr ...           # Run manager CLI
./backend.ai ag ...            # Run agent CLI
./backend.ai storage ...       # Run storage-proxy CLI
./backend.ai web ...           # Run webserver CLI
./backend.ai app-proxy-coordiantor ...  # Run app-proxy coordinator CLI
./backend.ai app-proxy-worker ...       # Run app-proxy worker CLI
```

Use the generic entrypoint script `./py` to execute modules inside the virtualenv of the main source tree (python-default) like:
```bash
./py -m {python-package-or-module} ...
```

### Database Schema Management

When working with SQLAlchemy schema migrations, we use Alembic to generate and run migrations.
Always specify the appropriate alembic configuration path depending on the target pacakge.

```bash
./py -m alembic -c {alembic-ini-path} ...
```

Replace `...` with appropriate subcommands, options, and arguments as specified in the help message
available via `--help` or using your knowledge.

There are multiple `alembic.ini` files, namely:

- `alembic.ini`: The alembic config for manager
- `alembic-accountmgr.ini`: The alembic config for account manager
- `alembic-appproxy.ini`: The alembic config for app proxy

Alembic migrations are located in `src/ai/backend/appproxy/coordinator/models/alembic/`:

```bash
# Run migrations for the main database
./py -m alembic upgrade head

# Run migrations for the app proxy database
./py -m alembic -c alembic-appproxy.ini upgrade head

# Create new migration
./py -m alembic revision --autogenerate -m "Description"

# Check for multiple heads (CI validation)
python scripts/check-multiple-alembic-heads.py

# Rebase the migration history
./py -m scripts/alembic-rebase.py {base_head} {top_head}
```

When you observe migration failures due to multiple heads, do the followings:
- Check `./py -m alembic heads` and `./py -m alembic history --verbose` to inspect the branched out
  change history.
- Inspect the migrations to see if there are potential conflicts like modifying the same column of
  the same table, duplicate table or column names to be created, etc.
- If there are no conflicts, run `./py scripts/alembic-rebase.py {base_head} {top_head}` command to
  rebase the alembic history, where base_head is the topmost revision ID of the migrations from the Git
  base branch like main and top_head is the topmost revision ID of the migrations added in the current working
  branch.

## Hooks and Code Quality

Backend.AI uses Claude Code hooks and Git pre-commit hooks for code quality:

**Claude Code Hooks** (configured in `.claude/settings.local.json`, gitignored):
- **PostToolUse**: Runs `pants fmt` after Edit/Write operations
  - Formats code immediately but does NOT run `pants fix` to avoid removing imports prematurely
- **Stop**: Runs `pants fix` on all modified Python files when Claude finishes
  - Removes unused imports and fixes auto-fixable lint issues

**Git Pre-commit Hook** (`scripts/pre-commit.sh`):
- Runs on every `git commit`
- Validates: `pants lint`, `pants check` on changed files only
- Tests run in CI for comprehensive coverage
- Bypass with `git commit --no-verify` for WIP commits (never on main/master/release/merge commits)

**Manual execution:**
```bash
pants lint --changed-since=HEAD~1
pants check --changed-since=HEAD~1
```
