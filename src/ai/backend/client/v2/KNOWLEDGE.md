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

## Scoped search unification: the server has moved, the SDK has not

- Today in the SDK: a separate method per scope (`project_search(project_id, request)`, `domain_search(domain_name, request)`) maps to a parent-pinned URL.
- The server settled its half in BA-7742: `POST /{entity}/scoped/search` takes a `scope` object of
  per-kind `UUIDScope` lists, all OR'd, and the per-scope routes stay beside it. So the URL pattern
  and the request shape are no longer open questions.
- What remains: one `scoped_search(request)` per entity in the SDK and the CLI options that drive it.
  Until those land, new SDK code follows the current per-scope shape and does not mix the two shapes
  within one entity.
- Cost of the current shape: every new scope type adds one method per entity, and the drift against the
  server's scoped endpoints now grows with every entity the server converts.
