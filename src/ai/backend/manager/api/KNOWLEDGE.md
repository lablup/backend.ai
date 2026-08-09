---
name: api-surface-and-naming
type: design-rationale
description: REST v2 (CLI) and GraphQL (WebUI) surfaces shipped together and backed by shared per-entity adapters, operation naming and gates (admin_ global, public global read, scoped, my_), live-server verification workflow
scope: src/ai/backend/manager/api
keywords: [rest, graphql, adapter, admin_, public, scoped, my_, verification]
sources:
  - src/ai/backend/manager/api/adapters
generated:
  by: claude-code/fable-5
  at: 2026-08-10
status: stable
---

# Manager API layer — Knowledge

> For rules, see `AGENTS.md` in the same directory; for implementation patterns, see the `/api-guide` skill.

## Two surfaces, one adapter

The layer exposes each operation through two surfaces — REST v2 (`api/rest/v2/`),
consumed mainly by the CLI, and GraphQL (`api/gql/`), consumed mainly by the WebUI.
Every operation ships on **both** surfaces together — adding one without the other
leaves a client without the feature. Neither surface holds behavior: both call the
shared per-entity adapter (`api/adapters/{entity}.py`), which owns auth context,
scope building, and DTO mapping, so the two surfaces cannot drift apart.
Adapter-side patterns: [adapters/KNOWLEDGE.md](adapters/KNOWLEDGE.md).

## Operation naming and gates

| Shape | Meaning | Gate |
|---|---|---|
| `admin_*` | global operation across all scopes | superadmin |
| bare global read (get/search) | public read, served to every authenticated user | authenticated |
| scoped operation (`scoped/search` paths) | one operation over caller-supplied scopes | RBAC per scope |
| `my_*` | self-service — the caller is the scope | authenticated (adapter resolves the user) |

## v2 endpoint verification

Verify new API endpoints against the live server before committing. For server restart, `./bai` commands, and log checks, see
the `/local-dev`, `/bai-cli`, and `/observability` skills.
