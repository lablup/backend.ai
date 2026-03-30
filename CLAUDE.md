# Coding Guidelines for AI Coding Agents

This file contains core rules for AI coding agents. For detailed patterns and workflows, use skills and documentation below.

## Documentation Index

**Core Documents (Read directly):**
- `tests/CLAUDE.md` - Testing guidelines and strategies
- `BUILDING.md` - Build system, quality enforcement, BUILD policies
- `README.md` - Project overview and architecture
- `proposals/README.md` - BEP (Backend.AI Enhancement Proposals)

**Skills (Invoke with `/skill-name`):**

Design: `/bep-guide`
Development: `/repository-guide`, `/service-guide`, `/api-guide`, `/tdd-guide`
Utilities: `/cli-executor`, `/db-status`, `/db-migrate`, `/local-dev`, `/halfstack`

Skills are in `.claude/skills/{name}/SKILL.md`. See `.claude/skills/README.md` for complete documentation.

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
1. Restart server: `./dev restart mgr`
2. Test each operation via `./bai` CLI (see `/local-dev` skill for setup and commands)
3. Verify both admin and non-admin scenarios

## Development Guidelines

**README-First:** Always read component README (`src/ai/backend/{component}/README.md`) before making changes.

**BEP-First:** For significant features, use `/bep-guide` skill. Check `proposals/README.md` for existing BEP or create new one.

**TDD:** Write tests first. Use `/tdd-guide` skill for workflow. See `tests/CLAUDE.md` for test strategies.

**Implementation Patterns:** Use skills for detailed guidance:
- Repository layer → `/repository-guide`
- Service layer → `/service-guide`
- API/GraphQL → `/api-guide`
