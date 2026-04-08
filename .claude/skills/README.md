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
| `/tdd-guide` | TDD workflow (Red → Green → Refactor) | Test-first approach for new features/bug fixes |

## Database Management

| Skill | Purpose |
|-------|---------|
| `/db-status` | Check schema version and migration status |
| `/db-migrate` | Apply migrations (upgrade/downgrade) |

## Local Development & CLI

| Skill | Purpose | Use When |
|-------|---------|----------|
| `/local-dev` | Service management (`./dev`) — start, stop, restart, crash debugging | Restarting services after code changes, debugging startup crashes |
| `/bai-cli` | V2 CLI usage (`./bai`) — config, login, command patterns, entity reference | Testing API changes on live server, discovering CLI commands |

## Component Execution

| Skill | Purpose |
|-------|---------|
| `/cli-executor` | Execute component CLI (mgr, ag, storage, web, app-proxy) |

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
tdd-guide → repository/service/api layer tests

**Submission Flow:**
jira-issue → [implement] → submit (quality checks → commit → PR → changelog → push)

**Release Flow:**
release (pre-flight → release.sh → changelog editing → RC consolidation → summary)

**Infrastructure Flow:**
halfstack → db-status → db-migrate → cli-executor → local-dev → bai-cli

## Related Documents

- `CLAUDE.md` - Core development principles
- `tests/CLAUDE.md` - Testing guidelines
- `BUILDING.md` - Build system and quality enforcement
- Component READMEs: `src/ai/backend/{component}/README.md`
