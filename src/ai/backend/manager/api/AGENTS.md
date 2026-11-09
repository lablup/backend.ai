# Manager API layer: Guardrails

> For background and verification procedures, see `KNOWLEDGE.md` in the same directory; for implementation patterns, see the `/api-guide` skill.

## Handler style

- Every handler must be a method of an `APIHandler` class: no module-level async functions.
- Parse requests with `BodyParam[T]` and `PathParam[T]`: do not read `request.json()` or
  `request.rel_url.query` directly inside a handler.
- Return via `APIResponse.build(status_code=..., response_model=...)`: no `web.json_response()`.

## Calling services

- **New (v2):** The handler calls the Adapter (`self._adapters.{domain}.method(dto_input)`);
  no direct Processor/Service calls. The Adapter is shared with the GQL layer.
- **Legacy REST (v1):** The handler calls the Processor directly (`await self._foo.wait_for_complete(FooAction(...))`).
- All new API endpoints follow the v2 pattern.
- **Do not add to or modify REST v1 or the graphene-based GQL code (`gql_legacy/`)**:
  changes go to v2; v1 accepts critical fixes only (rationale: `KNOWLEDGE.md`).

## Naming and scope

- superadmin only: `admin_` prefix + call `_check_superadmin(request)` on the first line.
- scoped: currently a `{scope}_` prefix (for example `domain_search_users`). A `scoped_` prefix with the scope as a request field is under consideration (see scoped search REST URL below).
- self-service: `my_` prefix (for example `my_keypairs`). The Adapter resolves the user internally.
  - REST URL `/v2/{entity}/my/{operation}`: the entity comes first, `my` is the scope qualifier.

**search: always two variants**
- `admin_search_*`: superadmin only, no scope; system-wide query.
- scoped search: non-admin, scope argument required; query within that scope.
- There is no "unscoped system-wide query" for non-admins.

**scoped search REST URL** (under consideration):
- Current: `/v2/{entity}/{scope_type}/{scope_id}/search` expresses the scope as a nested resource path (not `search-by-{scope}`).
  Example: `/v2/sessions/projects/{project_id}/search`.
- The plan is to use a fixed path of the form `/v2/{entity}/scoped/search` with the scope as a request body field (not a path param). This is consistent with SDK `scoped_search` and GQL `scopedFoosV2`.

**create, update, get, delete, purge: criteria for splitting out `admin_`**
- admin-only entities (Domain, ContainerRegistry, etc.): a single `admin_` endpoint.
- both admin and user, with different behavior (for example admin sets more fields): split `admin_` and non-admin into different DTOs.
- both admin and user, differing only in permission checks: a single endpoint; admins already have entity access, so no separate `admin_` is needed.

## Write responses (DTO, REST)

- When the target still exists (create, update, soft delete, restore), return the target DTO.
- A purge finishing within the request returns 200 with the removed target's UUID: `entity_id` for an entity,
  `field_id` for a field row, the end UUIDs for a relation.
- A purge of an entity with `purge_status` starts the cleanup and returns 202 Accepted with the target DTO
  (`purge_status = purging`). A force purge finishes within the request.
- A request naming a relation takes the end UUIDs in the body. Do not put an id in the path.
- DTOs carry UUIDs only. The GQL layer builds global IDs (`gql/AGENTS.md`).

## Routing

- Register routes only in `create_app()`.
- Set `app["prefix"]` to this sub-app's URL segment.

## V2 DTO: the shared schema

The v2 DTOs (`common/dto/manager/v2/`) are the schema shared by REST v2 handlers, GQL types, the Client SDK, and the CLI.
**A DTO change affects all four of these layers**: coordinate them in the order DTO → Adapter → REST handler → GQL type → SDK → CLI.

## What belongs here / What does not belong here

- Belongs: HTTP request/response conversion, auth decorators (`@auth_required_for_method`).
- Does not belong: business logic / domain rules, direct DB access or `manager/models/` ORM imports,
  Repository/Service class imports.
