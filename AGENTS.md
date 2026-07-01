# AI Coding Agent Guidelines

This file contains the core rules for AI coding agents. For detailed patterns and workflows, use the skills and documents below.

## Document structure (AGENTS.md / CONTEXTS.md)

- **`AGENTS.md`**: Guardrails (rules) only. Concise and imperative. Always auto-loaded (`CLAUDE.md` is a symlink to this file).
- **`CONTEXTS.md`**: Background read for development (assumptions, rationale, caveats, examples, development context). Updated relatively often as assumptions and such change. Read on demand, with a pointer placed at the top of the corresponding `AGENTS.md`.
- **`README.md`**: A document for humans to understand the component's composition. Should not change often. Does not duplicate AGENTS/CONTEXTS.
- Place a rule **only once, at the highest level** of its scope — global at this root, component-global at the component top level. Do not duplicate an upper-level rule lower down.

## Writing style

Applies to every generated artifact — docs, code comments, BEPs, PR descriptions.

- Lead with the conclusion; keep background short.
- Implementation details live in the code and the PR — docs describe interfaces and contracts, not line-by-line steps.
- Prefer tables and lists over prose.
- Code examples show the interface/contract only, not internal implementation.
- State a rule once at its highest scope (see above); link instead of repeating.

## Document index

**Core Documents (Read directly):**
- `tests/AGENTS.md` — Testing guidelines and strategies
- `BUILDING.md` — Build system, quality enforcement, BUILD policies
- `src/ai/backend/manager/models/alembic/README.md` — Alembic migration backport strategy
- `README.md` — Project overview and architecture
- `proposals/README.md` — BEP (Backend.AI Enhancement Proposals)

**Skills (Invoke with `/skill-name`):**

When to use:
- Finding where a feature lives / tracing it across layers (REST, GraphQL, Service, Repository, DB) → `/code-trace`
- Designing features → `/bep-guide`
- Implementing repo/service/API layers → `/repository-guide`, `/service-guide`, `/api-guide`
- Implementing SDK/CLI code → `/cli-sdk-guide`
- Writing tests → `/test-guide`
- Restarting services after code changes → `/local-dev`
- **Running any `./bai` command → `/bai-cli` (MUST load before executing)**
- Checking logs/metrics/traces during development → `/observability` (Grafana MCP)
- Docker/halfstack issues → `/halfstack`
- Checking/applying DB migrations → `/db-migrate`
- Running component servers directly → `/local-dev`
- Submitting PR → `/submit`
- Preparing release → `/release`

Skills source: `.claude/skills/{name}/SKILL.md`

## Absolute rules (global)

**Do NOT bypass quality enforcement:**
- Do NOT suppress linter warnings with `# noqa`.
- Do NOT suppress type errors with `# type: ignore`.
- Fix quality issues immediately, even if unrelated to your change.

**Python critical rules:**
- **Async-first**: Use async/await for all I/O.
- **Exceptions**: Inherit from `BackendAIError` everywhere possible — do NOT raise built-in exceptions directly in business logic.
- **Imports**: Do NOT use parent relative imports (`from ..module`) — use absolute imports.
- **re-export**: Where possible, do NOT use `__init__.py` re-exports; import modules directly.
- **Class fields**: Declare the instance fields a class uses at the top of the class body with their types (assign them in `__init__`).

**BUILD files:**
- ❌ Do NOT add BUILD files to the `src/` directory.
- ✅ MUST add BUILD files to new test directories.
- Use `python_tests()` for test modules, `python_testutils()` for utilities.

## Before committing

Before committing, run the commands below and fix all errors:

```bash
pants fmt --changed-since=HEAD~1
pants fix --changed-since=HEAD~1
pants lint --changed-since=HEAD~1
pants check --changed-since=HEAD~1
pants test --changed-since=HEAD~1
```

**Fix all lint, type, and test errors — never suppress or skip.**

**After API/CLI changes, verify with the live server using the `./bai` CLI, and check runtime logs/metrics via the Grafana MCP (`/observability`).**
**MUST load the `/bai-cli` skill before running any `./bai` command.** This skill contains the entity-command reference — without it, you will guess commands wrong.
For service restarts, see `/local-dev`; for docker service changes, see the `/halfstack` skill.

## Alembic migration backport

When backporting migrations to release branches, both the backport and main branch migrations must be idempotent.
For the full strategy and examples, see `src/ai/backend/manager/models/alembic/README.md`.

## Layer architecture

API Handler → Processor → Service → Repository → DB

- API handlers call Processors — they do NOT call Services directly.
- Services accept Actions (frozen dataclasses) and return ActionResults.
- Repositories handle all DB access (transactions and sessions are the repository's responsibility).
- Do NOT import from a lower layer into a higher layer.
- For detailed patterns, see the skills: `/repository-guide`, `/service-guide`, `/api-guide`.

## API development rules

**All new features MUST use v2 patterns across the full stack:**
- REST API: `api/rest/v2/{entity}/` (do NOT add new endpoints to REST v1)
- DTO: `common/dto/manager/v2/{entity}/` (shared across GQL and REST v2)
- GraphQL: Strawberry-based `api/gql/{entity}/` (do NOT add to `gql_legacy/`)
- Adapter: `api/adapters/{entity}.py` (shared between GQL and REST v2)
- Client SDK: `client/v2/domains_v2/{entity}.py` (typed Pydantic request/response)
- CLI: `client/cli/v2/{entity}/` (calls SDK v2)

**Standard 6 operations per entity:** create, get, search, update, delete, purge
- For detailed API patterns: `/api-guide`
- For SDK/CLI patterns: `/cli-sdk-guide`

**After implementing new API endpoints, verify with the live server** — check both admin and non-admin. For the server restart, `./bai`
test, and log-checking procedures, see the `/local-dev`, `/bai-cli`, and `/observability` skills.

## Development guidelines

**Document-first:** Before making changes, read the `AGENTS.md` in the relevant directory, and if you need more context, read `CONTEXTS.md` in the same directory.

**BEP-first:** For significant features, use the `/bep-guide` skill. Check `proposals/README.md` for an existing BEP or create a new one.

**Testing:** Agree on test scenarios first (success/exception/edge), then implement and verify each. See the `/test-guide` skill; for strategies, see `tests/AGENTS.md`.

**Implementation patterns:** For details, use the skills:
- Repository layer → `/repository-guide`
- Service layer → `/service-guide`
- API/GraphQL → `/api-guide`
