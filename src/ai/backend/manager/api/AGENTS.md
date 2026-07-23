# Manager API layer — Guardrails

> For background and verification procedures, see `CONTEXTS.md` in the same directory; for implementation patterns, see the `/api-guide` skill.

## Handler style

- Every handler must be a method of an `APIHandler` class — no module-level async functions.
- Parse requests with `BodyParam[T]` and `PathParam[T]` — do not read `request.json()` or
  `request.rel_url.query` directly inside a handler.
- Return via `APIResponse.build(status_code=..., response_model=...)` — no `web.json_response()`.

## Calling services

- **New (v2):** The handler calls the Adapter (`self._adapters.{domain}.method(dto_input)`) —
  no direct Processor/Service calls. The Adapter is shared with the GQL layer.
- **Legacy REST (v1):** The handler calls the Processor directly (`await self._foo.wait_for_complete(FooAction(...))`).
- All new API endpoints follow the v2 pattern.

## Naming & scope

- superadmin only: `admin_` prefix + call `_check_superadmin(request)` on the first line.
- scoped: `scoped_` prefix, receiving the scope as a request field (see scoped search REST URL below).
  **Legacy:** a `{scope}_` prefix (e.g. `domain_search_users`) — do not add new ones.
- self-service: `my_` prefix (e.g. `my_keypairs`). The Adapter resolves the user internally.
  - REST URL: `/v2/{entity}/my/{operation}` — the entity comes first, `my` is the scope qualifier.

**search — always two variants:**
- `admin_search_*`: superadmin only, no scope — system-wide query.
- scoped search: non-admin, scope argument required — query within that scope.
- There is no "unscoped system-wide query" for non-admins.
- The audience (`admin` / `scoped` / `my`) is always a REST path segment before the operation
  name — see `api/rest/v2/AGENTS.md` for the full URL grammar.

**scoped search REST URL:**
- Fixed path `/v2/{entity}/scoped/search`, with the scope as a request body field (not a path param).
  Consistent with SDK `scoped_search` and GQL `scopedFoosV2`.
- **Legacy:** the scope as a nested resource path, `/v2/{entity}/{scope_type}/{scope_id}/search`
  (e.g. `/v2/sessions/projects/{project_id}/search`) — do not add new ones.

**create / update / get / delete / purge — criteria for splitting out `admin_`:**
- admin-only entities (Domain, ContainerRegistry, etc.): a single `admin_` endpoint.
- both admin and user, with different behavior (e.g. admin sets more fields): split `admin_` and non-admin into different DTOs.
- both admin and user, differing only in permission checks: a single endpoint — admins already have entity access, so no separate `admin_` is needed.

## Routing

- Register routes only in `create_app()`.
- Set `app["prefix"]` to this sub-app's URL segment.

## V2 DTO — single source of truth

The v2 DTOs (`common/dto/manager/v2/`) are the schema shared by REST v2 handlers, GQL types, the Client SDK, and the CLI.
**A DTO change affects all four of these layers** — coordinate them in the order DTO → Adapter → REST handler → GQL type → SDK → CLI.

## What belongs here / What does NOT belong here

- Belongs: HTTP request/response conversion, auth decorators (`@auth_required_for_method`).
- Does NOT belong: business logic / domain rules, direct DB access or `manager/models/` ORM imports,
  Repository/Service class imports.
