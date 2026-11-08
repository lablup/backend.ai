# Backend.AI Claude Code Skills

This directory contains Claude Code skills for Backend.AI development tasks.

## Design and Planning

| Skill | Purpose | Use When |
|-------|---------|----------|
| `/bep-guide` | BEP creation workflow, document segmentation, overview and index pattern | Writing new BEPs, structuring long proposals |

## Development Guides

| Skill | Purpose | Use When |
|-------|---------|----------|
| `/repository-guide` | Repository base patterns (Querier, Creator, Updater, Purger, SearchScope) | New repository implementation, extending existing |
| `/service-guide` | Service layer (Actions, Processors, ActionProcessor) | New service implementation, Action and Processor patterns |
| `/api-guide` | REST and GraphQL API (scope, filter, admin_ prefix, BaseFilterAdapter) | API endpoint implementation |
| `/cli-sdk-guide` | Client SDK and CLI (Session, @api_function, Click, FieldSpec) | SDK function implementation, CLI command creation |
| `/test-guide` | Propose scenarios → refine with user → verify each (fixtures, with_tables, optional TDD) | Writing tests for a new feature or a bug fix |

## Exploration and Navigation

| Skill | Purpose | Use When |
|-------|---------|----------|
| `/code-trace` | Map a feature across REST, GraphQL, service, repository and DB; read the large supergraph.graphql safely | Finding where a feature lives, tracing a request through layers |

For finding and defining exceptions, see `src/ai/backend/manager/errors/AGENTS.md`.

## Database Management

| Skill | Purpose |
|-------|---------|
| `/db-migrate` | Inspect and apply migrations (status, upgrade, downgrade) |

## Local Development and CLI

| Skill | Purpose | Use When |
|-------|---------|----------|
| `/local-dev` | Service management (`./dev`): start, stop, restart, crash debugging | Restarting services after code changes, debugging startup crashes |
| `/bai-cli` | V2 CLI usage (`./bai`): config, login, command patterns, entity reference | Testing API changes on live server, discovering CLI commands |
| `/observability` | Logs, metrics and traces via Grafana MCP (Loki, Prometheus, Tempo, Pyroscope) | Verifying behavior after a restart |
| `/halfstack` | Docker Compose halfstack: config, service health, DB, Valkey, etcd, supergraph | Halfstack or infrastructure troubleshooting |

## Submission

| Skill | Purpose | Use When |
|-------|---------|----------|
| `/local-review` | Review the work in a separate session (direction, structure and consistency, implementation, missing pieces, follow-up work), then check each finding | Before committing or opening a PR, when the work needs a review from another session |
| `/submit` | Quality checks, commit, PR creation, changelog, push | After finishing implementation, ready to submit PR |
| `/backport` | Find the committed conflict markers, resolve or reapply on the release branch, verify, commit, push | CI fails on a backport pull request |

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
test-guide → repository, service and API layer tests

**Submission Flow:**
implement → local-review → submit (quality checks → commit → PR → changelog → push)

**Release Flow:**
release (pre-flight → release.sh → changelog editing → RC consolidation → summary)

**Infrastructure Flow:**
halfstack → db-migrate → local-dev → bai-cli

## Related documents

- `CLAUDE.md` - Core development principles
- `tests/CLAUDE.md` - Testing guidelines
- `BUILDING.md` - Build system and quality enforcement
- Component READMEs: `src/ai/backend/{component}/README.md`
