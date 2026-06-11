# REST v2 API Layer — Guardrails

> REST v2 uses Pydantic DTOs from `common/dto/manager/v2/` — the same DTOs that back
> the GraphQL schema. Both APIs share a single source of truth.

## Architecture

```
REST v2 Handler → Adapter (api/adapters/) → Processor → Service → Repository
```

## Handler Style

- All handlers MUST be methods on an `APIHandler` class.
- Parse requests via `BodyParam[T]` where `T` is a DTO from `common/dto/manager/v2/`.
- Return `APIResponse.build(status_code=..., response_model=payload)` where `payload`
  is a DTO from `common/dto/manager/v2/`.

## Handler Dependency Injection

Each handler receives its **individual adapter** (NOT the Adapters registry):

```python
class V2DomainHandler:
    def __init__(self, *, adapter: DomainAdapter) -> None:
        self._adapter = adapter

    async def admin_search(self, body: BodyParam[T]) -> APIResponse:
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
```

- Call `self._adapter.method()` — never `self._adapters.domain.method()`.
- Adapters are shared with the GQL layer — do not create REST-specific adapters.
- `admin_` prefixed adapter methods → `superadmin_required` middleware.
- Non-admin methods → `auth_required` middleware.

## DTOs

- Use DTOs from `common/dto/manager/v2/` exclusively.
- Never import from `common/dto/manager/` (those are v1 DTOs used by legacy REST handlers).
- Never define REST-specific request/response models — use the shared v2 DTOs.

## Naming & Scope Rules

- Superadmin-only endpoints: `admin_` prefix + `superadmin_required` middleware.
- Scoped endpoints: `{scope}_` prefix (e.g., `domain_search_users`).
- Self-service endpoints: `/v2/{entity}/my/` — entity first, `my` as scope qualifier.

**search — always two variants:**
- `POST /v2/{entity}/search`: superadmin only, no scope — queries entire system.
- Scoped search (non-admin): scope is a **required** path segment — queries within the given scope only.
- There is NO "search everything without scope" for non-admin users.

**Scoped search URL pattern:**
- Pattern: `POST /v2/{entity}/{scope_type}/{scope_id}/search`
- The scope type and ID are expressed as nested resource path segments.
- Examples:
  - `POST /v2/sessions/projects/{project_id}/search` — sessions within a project
  - `POST /v2/sessions/agents/{agent_id}/search` — sessions on an agent
  - `POST /v2/users/domains/{domain_name}/search` — users within a domain
  - `POST /v2/users/projects/{project_id}/search` — users within a project
  - `POST /v2/users/roles/{role_id}/search` — users with a specific role
- Do NOT use `search-by-{scope}` pattern (e.g., `/search-by-agent/{id}` is wrong).
- All scoped search routes use `auth_required` middleware.

**Self-service (`my`) endpoints:**
- URL pattern: `POST /v2/{entity}/my/{operation}` (entity is the primary resource, `my` as scope qualifier).
- Examples: `POST /v2/keypairs/my/search`, `POST /v2/sessions/my/search`.
- The adapter resolves the current user internally via `current_user()`.
- All `my` routes use `auth_required` middleware.

**create / update / get / delete / purge — when to separate `admin_` vs non-admin:**
- **Admin-only entity** (e.g., Domain, ContainerRegistry): single `admin_` endpoint.
- **Both admin and users, behavior differs** (e.g., admin sets more fields): separate `admin_` and non-admin endpoints with different DTOs.
- **Both admin and users, only permission check differs**: single endpoint — admin already has entity access permissions, no separate `admin_` variant needed.

## Pagination Mode Behavior

Search endpoints accept both cursor-based and offset-based pagination arguments.

**Default (no pagination args):** Falls back to offset pagination (`limit=10, offset=0`).

**Offset pagination (`limit`/`offset`):**
- User-specified `order` is applied. If no `order`, the entity's default order is used.
- Use this mode when custom ordering is needed.

**Cursor pagination (`first`/`after` or `last`/`before`):**
- Ordering is fixed to the entity's cursor key (typically `created_at` or the primary key).
- User-specified `order` is **ignored** — cursor consistency requires a fixed sort order.
- Use this mode for infinite scrolling / "load more" UX where stable page boundaries matter.

Only one pagination mode is allowed per request. Combining `first` with `limit` raises an error.

## Routing

- Use `RouteRegistry` for route registration (same framework as REST v1).
- Route registration in a dedicated registrar function per domain.

## What Belongs Here

- HTTP request/response translation only.
- Auth middleware (`superadmin_required`, `auth_required`).

## What Does NOT Belong Here

- Business logic or domain rules.
- Direct database access or ORM imports.
- Imports of Repository, Service, or Processor classes.
- Conversion logic between domain Data types and DTOs (that belongs in Adapters).
