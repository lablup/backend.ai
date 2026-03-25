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

**search — always two variants:**
- `POST /v2/admin/{entity}/search`: superadmin only, no scope — queries entire system.
- `POST /v2/domains/{domain}/{entity}/search`: non-admin, scope in URL path — queries within the given scope only.
- There is NO "search everything without scope" for non-admin users.

**create / update / get / delete / purge — when to separate `admin_` vs non-admin:**
- **Admin-only entity** (e.g., Domain, ContainerRegistry): single `admin_` endpoint.
- **Both admin and users, behavior differs** (e.g., admin sets more fields): separate `admin_` and non-admin endpoints with different DTOs.
- **Both admin and users, only permission check differs**: single endpoint — admin already has entity access permissions, no separate `admin_` variant needed.

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
