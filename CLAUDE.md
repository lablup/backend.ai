# Coding Guidelines for AI Coding Agents

This file contains core rules for AI coding agents. For detailed patterns and workflows, use skills and documentation below.

## Documentation Index

**Core Documents (Read directly):**
- `tests/CLAUDE.md` - Testing guidelines and strategies
- `BUILDING.md` - Build system, quality enforcement, BUILD policies
- `src/ai/backend/manager/models/alembic/README.md` - Alembic migration backport strategy
- `README.md` - Project overview and architecture
- `proposals/README.md` - BEP (Backend.AI Enhancement Proposals)

**Skills (Invoke with `/skill-name`):**

When to use:
- Designing features → `/bep-guide`
- Implementing repo/service/API layers → `/repository-guide`, `/service-guide`, `/api-guide`
- Implementing SDK/CLI code → `/cli-sdk-guide`
- Writing tests → `/tdd-guide`
- Restarting services after code changes → `/local-dev`
- **Running any `./bai` command → `/bai-cli` (MUST load before executing)**
- Docker/halfstack issues → `/halfstack`
- Checking/applying DB migrations → `/db-status`, `/db-migrate`
- Running component servers directly → `/cli-executor`
- Submitting PR → `/submit`
- Preparing release → `/release`

Skills source: `.claude/skills/{name}/SKILL.md`

## Absolute Rules

**NEVER bypass quality enforcement:**
- Do NOT use `# noqa` to suppress linter warnings
- Do NOT use `# type: ignore` to suppress type errors
- Fix all quality issues immediately, even if unrelated to your change

**Python critical rules:**
- **Async-first**: All I/O operations MUST use async/await
- **Exceptions**: All exceptions MUST inherit from `BackendAIError` (never raise built-in exceptions in business logic)
- **Imports**: NEVER use parent relative imports (`from ..module`) - use absolute imports instead

**BUILD files:**
- ❌ NEVER add BUILD files to `src/` directory
- ✅ MUST add BUILD files to new test directories
- Use `python_tests()` for test modules, `python_testutils()` for utilities

## Before Committing

Before committing, run these commands and fix all errors:

```bash
pants fmt --changed-since=HEAD~1
pants fix --changed-since=HEAD~1
pants lint --changed-since=HEAD~1
pants check --changed-since=HEAD~1
pants test --changed-since=HEAD~1
```

**Fix all lint, type, and test errors — never suppress or skip.**

**After API/CLI changes, verify with live server using `./bai` CLI.**
**MUST invoke `/bai-cli` skill before running any `./bai` command.** The skill contains the entity-command reference — without it, you will guess wrong commands.
For service restarts, see `/local-dev`. For docker service changes, see `/halfstack` skill.

## Alembic Migration Backport

When backporting migrations to release branches, both the backport and main branch
migrations must be idempotent. See `src/ai/backend/manager/models/alembic/README.md`
for the full strategy and examples.

## Layer Architecture

API Handler → Processor → Service → Repository → DB

- API handlers MUST call Processors, NEVER Services directly
- Services accept Actions (frozen dataclasses), return ActionResults
- Repositories handle all DB access via `begin_session()` / `begin_readonly_session()`
- NEVER import from a lower layer to a higher layer
- For detailed patterns, read skill files: `/repository-guide`, `/service-guide`, `/api-guide`

## API Development Rules

**All new features MUST use v2 patterns across the full stack:**
- REST API: `api/rest/v2/{entity}/` (NEVER add new endpoints to REST v1)
- DTOs: `common/dto/manager/v2/{entity}/` (shared across GQL and REST v2)
- GraphQL: Strawberry-based `api/gql/{entity}/` (NEVER add to `gql_legacy/`)
- Adapter: `api/adapters/{entity}.py` (shared between GQL and REST v2)
- Client SDK: `client/v2/domains_v2/{entity}.py` (typed Pydantic request/response)
- CLI: `client/cli/v2/{entity}/` (calls SDK v2)

**Standard 6 operations per entity:** create, get, search, update, delete, purge
- For detailed API patterns: `/api-guide`
- For SDK/CLI patterns: `/cli-sdk-guide`

**After implementing new API endpoints, verify with the live server:**
1. Restart server: `./dev restart mgr` (invoke `/local-dev`)
2. Invoke `/bai-cli` skill, then test each operation via `./bai` CLI
3. Verify both admin and non-admin scenarios

## Development Guidelines

**README-First:** Always read component README (`src/ai/backend/{component}/README.md`) before making changes.

**BEP-First:** For significant features, use `/bep-guide` skill. Check `proposals/README.md` for existing BEP or create new one.

**TDD:** Write tests first. Use `/tdd-guide` skill for workflow. See `tests/CLAUDE.md` for test strategies.

**Implementation Patterns:** Use skills for detailed guidance:
- Repository layer → `/repository-guide`
- Service layer → `/service-guide`
- API/GraphQL → `/api-guide`
