# REST v2 API layer: Guardrails

> For background (pagination mode behavior, dependency injection example, scoped URL examples), see `KNOWLEDGE.md` in the same directory; for implementation patterns, see the `/api-guide` skill.
> REST v2 uses the Pydantic DTOs in `common/dto/manager/v2/`: the same DTOs as the GQL schema (single source).

## Architecture

```
REST v2 Handler → Adapter (api/adapters/) → Processor → Service → Repository
```

## Handler style

- Every handler must be a method of an `APIHandler` class.
- Parse requests with `BodyParam[T]`: `T` is a DTO from `common/dto/manager/v2/`.
- Return via `APIResponse.build(status_code=..., response_model=payload)`: `payload` is also a v2 DTO.

## Handler dependency injection

- Each handler is injected with an **individual adapter** (not the Adapters registry): call `self._adapter.method()`,
  not `self._adapters.domain.method()`.
- The Adapter is shared with the GQL layer: do not create a REST-only adapter.
- `admin_`-prefixed adapter methods → `superadmin_required` middleware, non-admin → `auth_required`.

## DTO

- Use only the DTOs in `common/dto/manager/v2/`.
- Do not import from `common/dto/manager/` (v1, for legacy REST).
- Do not define REST-only request/response models: use the shared v2 DTOs.

## Naming and scope

- superadmin only: `admin_` prefix + `superadmin_required` middleware.
- scoped: currently a `{scope}_` prefix. See the scoped search URL below for the planned `scoped_` prefix.
- self-service at `/v2/{entity}/my/`: the entity comes first, `my` is the scope qualifier.
- anonymous at `/v2/{entity}/public/`: no auth middleware. `public` is reserved for this (see below).

**search: always two variants**
- `POST /v2/{entity}/search`: superadmin only, no scope; system-wide query.
- scoped search (non-admin): scope required; query within that scope.
- There is no "unscoped system-wide query" for non-admins.

**scoped search URL** (under consideration):
- Current: `POST /v2/{entity}/{scope_type}/{scope_id}/search` expresses the scope as a nested resource path (not `search-by-{scope}`).
  Example: `/v2/sessions/projects/{project_id}/search`. See `KNOWLEDGE.md` for more examples.
- The plan is to use the fixed path `/v2/{entity}/scoped/search` with the scope as a request body field (not a path param).
  This is consistent with SDK `scoped_search` and GQL `scopedFoosV2`.
- All scoped search routes use the `auth_required` middleware.

**self-service (`my`):**
- `POST /v2/{entity}/my/{operation}` (for example `/v2/keypairs/my/search`). `my/search`: the handler sets the `UserContext`
  user as the user scope and calls the adapter's `scoped_search`. Do not add `my_search` to the adapter.
  `auth_required` middleware.

**anonymous (`public`): reserved segment**
- `POST /v2/{entity}/public/{operation}` (for example `/v2/app-config/public/get`). No auth middleware. `public` marks the missing
  auth, never a property of the resource.
- The webserver proxies exactly this shape anonymously by pattern (`web/server.py`), so adding a route here exposes it with no
  further edit. Two segments only: nothing nested below the operation.

**create, update, get, delete, purge: criteria for splitting out `admin_`**
- admin-only entities: a single `admin_`.
- both admin and user with different behavior: split `admin_` and non-admin (different DTOs).
- differing only in permission checks: a single one; admins already have access.

## Pagination

- Accept both cursor and offset arguments. Only one mode per request: mixing `first` and `limit` is an error.
- For mode-specific behavior and defaults, see `KNOWLEDGE.md`.

## Routing

- Register routes via the `RouteRegistry` (the same framework as REST v1), from a per-domain dedicated registrar function.

## What belongs here / What does not belong here

- Belongs: HTTP request/response conversion, auth middleware (`superadmin_required`, `auth_required`).
- Does not belong: business logic / domain rules, direct DB access or ORM imports, Repository/Service/Processor imports,
  conversion between domain Data and DTO (the Adapter's responsibility).
