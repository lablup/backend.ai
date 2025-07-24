# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.


## Project Overview

Read `README.md` for overall architecture and purpose of directories.


## General

### Tidy First Approach

* Separate all changes into two distinct types:
  - STRUCTURAL CHANGES: Rearranging code without changing behavior (renaming, extracting methods, moving code)
  - BEHAVIORAL CHANGES: Adding or modifying actual functionality
* Never mix structural and behavioral changes in the same commit
* Always make structural changes first when both are needed
* Validate structural changes do not alter behavior by running tests before and after

### Code Quality

* Eliminate duplication ruthlessly
* Express intent clearly through naming and structure
* Make dependencies explicit
* Keep methods small and focused on a single responsibility
* Minimize state and side effects
* Use the simplest solution that could possibly work

### Working with Long Contexts

* Split large work into step by step sprints
* Write or update your original plan in SPEC.md in such cases
* Do not make changes beyond those originally asked for but explicitly proceed user confirmation

### Python Specifics

- **Async-first**: All I/O operations use async/await
- **Type Hints**: Comprehensive type annotations required
- **Structured Logging**: Use BraceStyleAdapter for consistent logging
- **Configuration**: Pydantic models for validation
- **Error Handling**: Comprehensive exception handling with proper logging

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


## Build System & Development Commands

This project uses **Pants Build System** (version 2) and Python as specified in the `pants.toml` configuration.
All development commands use `pants` instead of `pip`, `poetry`, or `uv` commands.

### Essential Commands

Most pants command accepts a special target argument which can indicate a set of files or the files
changed for a specific revision range with optional transitive dependent files of the changed files.

- All files: `::`
- All files under specific directory of the dependency tree: `path/to/subpkg::`
- Files changed after the last commit: `--changed-since=HEAD~1` (here, the revision range syntax is that used by Git)
- Files changed after the last commit and their dependent files as inferred: `--changed-dependents=transitive` (this option must be used with `--changed-since`)

Here are the practical examples (where `{targets}` is a placeholder for an arbitrary target argument):

```bash
# Linting and formatting
pants lint ::                      # Lint all files
pants lint --changed-since=HEAD~1 --changed-dependents=transitive  # Lint changed files and their dependent files
pants fmt ::                       # Format all files
pants fmt --changed-since=HEAD~1   # Format only changed files

# Type checking
pants check ::                     # Run MyPy type checking for all files
pants check --changed-since=HEAD~1 --changed-dependents=transitive  # Run mypy on changed files and their dependent files

# Testing
pants test ::                      # Run all tests
pants test --changed-since=HEAD~1 --changed-dependents=transitive  # Test changed files and their dependent files
pants test src/ai/backend/appproxy/coordinator/tests::  # Run specific test directory inside the main source tree (python-default)
pants test tests/common::                               # Run specific test directory inside the test suite
pants test --debug {targets}       # Run the target tests with interactive, non-retrying, interruptible mode for debugging

# Building
pants package                                      # Build packages
```

## Dependency Management using Lock files

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
./backend.ai worker ...        # Run app-proxy coordinator CLI
./backend.ai coordinator ...   # Run app-proxy worker CLI
```

Use the generic entrypoint script `./py` to execute modules inside the virtualenv of the main source tree (python-default) like:
```bash
./py -m {python-package-or-module} ...
```

### Databases

When working with SQLAlchemy schema migrations, we use Alembic to generate and run migrations.

```bash
./py -m alembic -c {alembic-ini-path} ...
```

Replace `...` with appropriate subcommands, options, and arguments as specified in the help message
available via `--help` or using your knowledge.

There are multiple `alembic.ini` files, namely:

- `alembic.ini`: The alembic config for manager
- `alembic-accountmgr.ini`: The alembic config for account manager
- `alembic-appproxy.ini`: The alembic config for app proxy

### Verifying Changes

Once you finish or want to validate a job requested by the user after changing multiple files,
use the following commands to automatically format, lint, and do type checks:

```bash
pants fmt --changed-since=HEAD~1   # Auto-format changed files
pants fix --changed-since=HEAD~1   # Auto-fix lint issues changed files
pants lint --changed-since=HEAD~1 --changed-dependents=transitive  # Run full linting on changed and their dependent files
pants check --changed-since=HEAD~1 --changed-dependents=transitive  # Run typecheck on changed and their dependent files
```

and fix any Ruff and Mypy errors displayed after running them.

### Pre-commit Hooks

The project uses pre-commit hooks that automatically run `pants lint --changed-since="HEAD~1"` on changed files.


## Architecture Overview

### Core Components

1. **Common Module** (`src/ai/backend/appproxy/common/`)
   - Shared utilities, configuration, logging, types
   - Database utilities and distributed locking mechanisms
   - Configuration validation with Pydantic

2. **Coordinator** (`src/ai/backend/appproxy/coordinator/`)
   - REST API endpoints for circuit/worker management
   - PostgreSQL database models with SQLAlchemy 2.0
   - Alembic database migrations
   - CLI interface for server management

3. **Worker** (`src/ai/backend/appproxy/worker/`)
   - Multiple proxy backends: HTTP, H2, TCP, Traefik
   - Port-based and subdomain-based proxy frontends
   - Health check API
   - CLI interface for worker management

### Key Technologies

- **Web Framework**: aiohttp (fully async)
- **Database**: PostgreSQL with asyncpg and SQLAlchemy 2.0
- **Migrations**: Alembic
- **Configuration**: TOML with Pydantic validation
- **Service Discovery**: etcd integration
- **Caching**: Redis with sentinel support
- **Type Checking**: MyPy with Pydantic plugin

## Configuration

Configuration files are located in `configs/` with separate files for coordinator and worker:
- `configs/proxy-coordinator/example.toml` - Coordinator configuration template
- `configs/proxy-worker/example.toml` - Worker configuration template
- `configs/proxy-coordinator/halfstack.toml` - Development setup
- `configs/proxy-worker/halfstack.toml` - Development setup

## Database Migrations

Alembic migrations are located in `src/ai/backend/appproxy/coordinator/models/alembic/`:

```bash
# Run migrations
./py -m alembic upgrade head

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

## Code Quality Tools

- **Ruff**: Primary linter with line length 100, preview features and formatter enabled
- **MyPy**: Type checking with strict settings
- **Pre-commit**: Automated linting on commit

## Testing

- **Framework**: pytest with asyncio support
- **Markers**: `integration` for tests requiring Dockerized kernel sessions
- **Async Mode**: Automatic asyncio test detection
