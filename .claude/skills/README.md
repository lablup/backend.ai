# Backend.AI Claude Code skills

Skills for Backend.AI development tasks.

## Design and planning

| Skill | Purpose | Use when |
|---|---|---|
| `/bep-guide` | BEP creation workflow, document segmentation, overview and index pattern | Writing a new BEP, structuring a long proposal |

## Development guides

| Skill | Purpose | Use when |
|---|---|---|
| `/repository-guide` | Repository base patterns (Querier, Creator, Updater, Purger, SearchScope) | Implementing a new repository, extending an existing one |
| `/service-guide` | Service layer (Actions, Processors, ActionProcessor) | Implementing a new service, Action and Processor patterns |
| `/api-guide` | REST and GraphQL API (scope, filter, admin_ prefix, BaseFilterAdapter) | Implementing an API endpoint |
| `/cli-sdk-guide` | Client SDK and CLI (Session, @api_function, Click, FieldSpec) | Implementing an SDK function, creating a CLI command |
| `/test-guide` | Propose scenarios, refine them with the user, verify each (fixtures, with_tables, optional TDD) | Writing tests for a new feature or a bug fix |

## Exploration and navigation

| Skill | Purpose | Use when |
|---|---|---|
| `/code-trace` | Map a feature across REST, GraphQL, service, repository and DB. Read the large supergraph.graphql safely | Finding where a feature lives, tracing a request through layers |

For finding and defining exceptions, see `src/ai/backend/manager/errors/AGENTS.md`.

## Database management

| Skill | Purpose |
|---|---|
| `/db-migrate` | Inspect and apply migrations (status, upgrade, downgrade) |

## Local development and CLI

| Skill | Purpose | Use when |
|---|---|---|
| `/local-dev` | Service management (`./dev`): start, stop, restart, crash debugging | Restarting services after code changes, debugging startup crashes |
| `/bai-cli` | `./bai` CLI usage: config, login, command patterns, entity reference | Testing API changes on a live server, discovering CLI commands |
| `/observability` | Logs, metrics and traces via the Grafana MCP (Loki, Prometheus, Tempo, Pyroscope) | Verifying behavior after a restart |
| `/halfstack` | Docker Compose halfstack: config, service health, DB, Valkey, etcd, supergraph | Halfstack or infrastructure troubleshooting |

## Submission

| Skill | Purpose | Use when |
|---|---|---|
| `/submit` | Quality checks, commit, PR creation, changelog, push | After finishing implementation, ready to submit a PR |

## Release

| Skill | Purpose | Use when |
|---|---|---|
| `/release` | Release script execution, changelog generation, RC consolidation with subsection grouping | Preparing a new version release (RC or final) |

## Skill integration

Feature development flow:

```
bep-guide → ┬→ repository-guide ─┐
            ├→ service-guide ────┼→ integrate → cli-sdk-guide → local-dev → bai-cli
            └→ api-guide ────────┘
```

Testing flow: test-guide → repository, service and API layer tests

Submission flow: implement → submit. Submit runs quality checks → commit → PR → changelog → push.

Release flow: release runs pre-flight → release.sh → changelog editing → RC consolidation → summary.

Infrastructure flow: halfstack → db-migrate → local-dev → bai-cli

## Related documents

- `CLAUDE.md` - Core development principles
- `tests/CLAUDE.md` - Testing guidelines
- `BUILDING.md` - Build system and quality enforcement
- Component READMEs: `src/ai/backend/{component}/README.md`
