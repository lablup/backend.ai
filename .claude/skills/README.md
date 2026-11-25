# Backend.AI Claude Code Skills

This directory contains Claude Code skills for Backend.AI development tasks.

## Design and Planning

| Skill | Purpose | Use When |
|-------|---------|----------|
| `/bep-guide` | BEP creation workflow, document segmentation, overview and index pattern | Writing new BEPs, structuring long proposals |

## Development Guides

| Skill | Purpose | Use When |
|-------|---------|----------|
| `/test-guide` | Propose scenarios → refine with user → verify each (fixtures, with_tables, optional TDD) | Writing tests for a new feature or a bug fix |

## Local Development and CLI

| Skill | Purpose | Use When |
|-------|---------|----------|
| `/observability` | Logs, metrics and traces via Grafana MCP (Loki, Prometheus, Tempo, Pyroscope) | Verifying behavior after a restart |
| `/halfstack` | Docker Compose halfstack: config, service health, DB, Valkey, etcd, supergraph | Halfstack or infrastructure troubleshooting |

## Submission

| Skill | Purpose | Use When |
|-------|---------|----------|
| `/local-review` | Review the work in a separate session (direction, structure and consistency, implementation, missing pieces, follow-up work), then check each finding | Before committing or opening a PR, when the work needs a review from another session |
| `/submit` | Quality checks, commit, PR creation, changelog, push | After finishing implementation, ready to submit PR |

## Skill Integration

**Submission Flow:**
implement → local-review → submit (quality checks → commit → PR → changelog → push)

## Related documents

- `CLAUDE.md` - Core development principles
