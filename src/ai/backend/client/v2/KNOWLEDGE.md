---
name: sdk-v2-scoped-search-direction
type: design-rationale
description: typed REST v2 client consumed by the CLI and integration tests, scoped_search unification direction (scope as request data, decided together with URL patterns and the CLI surface)
scope: src/ai/backend/client/v2
keywords: [scoped_search, project_search, domain_search, typed_request, domains_v2]
sources:
  - src/ai/backend/client/v2/domains_v2
generated:
  by: claude-code/fable-5
  at: 2026-08-10
status: stable
---

# Client SDK v2 — Knowledge

> Rules: `AGENTS.md` in the same directory.

## Why this package exists

It is the typed Python client for the REST v2 API — one domain client per
entity, with Pydantic request/response models shared with the server
(`common/dto/manager/v2/`). It exists so that every programmatic consumer talks
to the API through one validated surface instead of hand-rolled HTTP.

- The **CLI** (`client/cli/v2/`) is built on top of it.
- **Integration tests** drive the live server with it.
- A v2 endpoint without an SDK method is invisible to both — shipping an endpoint includes shipping the client method.

## Scoped search unification is a direction, not yet a rule

- Today: a separate method per scope (`project_search(project_id, request)`, `domain_search(domain_name, request)`) maps to a parent-pinned URL.
- Direction: one `scoped_search(request)` per entity, with the scope as a field of the request DTO — matching the server's `scoped/search` transition (scope as request data, not a URL segment).
- Why it is not yet a rule: the server URL pattern, the SDK method shape, and the CLI options — three surfaces must move together.
- Until it settles, new SDK code follows the current per-scope shape and does not mix the two shapes within one entity.
- Cost of the current shape: every new scope type adds one method per entity, and drift risk against the server's scoped endpoints grows — the reason unification is being discussed.
