# Backend.AI Claude Code Skills

This directory contains Claude Code skills for Backend.AI development tasks.

## Design & Planning

| Skill | Purpose | Use When |
|-------|---------|----------|
| `/bep-guide` | BEP creation workflow, document segmentation, overview+index pattern | Writing new BEPs, structuring long proposals |

## Development Guides

| Skill | Purpose | Use When |
|-------|---------|----------|
| `/repository-guide` | Repository base patterns (Querier, Creator, Updater, Purger, SearchScope) | New repository implementation, extending existing |
| `/service-guide` | Service layer (Actions, Processors, ActionProcessor) | New service implementation, Action/Processor patterns |
| `/api-guide` | REST/GraphQL API (scope, filter, admin_ prefix, BaseFilterAdapter) | API endpoint implementation |
| `/cli-sdk-guide` | Client SDK/CLI (Session, @api_function, Click, FieldSpec) | SDK function implementation, CLI command creation |
| `/test-guide` | Propose scenarios → refine with user → verify each (fixtures, with_tables, optional TDD) | Writing tests for a new feature/bug fix |

## Exploration & Navigation

| Skill | Purpose | Use When |
|-------|---------|----------|
| `/code-trace` | Map a feature across REST/GraphQL/Service/Repository/DB; read the large supergraph.graphql safely | Finding where a feature lives, tracing a request through layers |

For finding/defining exceptions, see `src/ai/backend/manager/errors/AGENTS.md`.

## Database Management

| Skill | Purpose |
|-------|---------|
| `/db-migrate` | Inspect & apply migrations (status, upgrade/downgrade) |

## Local Development & CLI

| Skill | Purpose | Use When |
|-------|---------|----------|
| `/local-dev` | Service management (`./dev`) — start, stop, restart, crash debugging | Restarting services after code changes, debugging startup crashes |
| `/bai-cli` | V2 CLI usage (`./bai`) — config, login, command patterns, entity reference | Testing API changes on live server, discovering CLI commands |
| `/observability` | Logs/metrics/traces via Grafana MCP (Loki, Prometheus, Tempo, Pyroscope) | Verifying behavior after a restart |
| `/halfstack` | Docker Compose halfstack — config, service health, DB/Valkey/etcd, supergraph | Halfstack/infra troubleshooting |

## Submission

| Skill | Purpose | Use When |
|-------|---------|----------|
| `/submit` | Quality checks, commit, PR creation, changelog, push | After finishing implementation, ready to submit PR |

## Release

| Skill | Purpose | Use When |
|-------|---------|----------|
| `/release` | Release script execution, changelog generation, RC consolidation with subsection grouping | Preparing a new version release (RC or final) |

## Skill Integration

**Feature Development Flow:**
```
bep-guide → ┬→ repository-guide ─┐
            ├→ service-guide ────┼→ integrate → cli-sdk-guide → local-dev → bai-cli
            └→ api-guide ────────┘
```

**Testing Flow:**
test-guide → repository/service/api layer tests

**Submission Flow:**
[implement] → submit (quality checks → commit → PR → changelog → push)

**Release Flow:**
release (pre-flight → release.sh → changelog editing → RC consolidation → summary)

**Infrastructure Flow:**
halfstack → db-migrate → local-dev → bai-cli

## Related Documents

- `CLAUDE.md` - Core development principles
- `tests/CLAUDE.md` - Testing guidelines
- `BUILDING.md` - Build system and quality enforcement
- Component READMEs: `src/ai/backend/{component}/README.md`
