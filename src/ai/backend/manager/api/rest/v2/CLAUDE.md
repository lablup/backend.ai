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

## Calling Services

- Handlers MUST call Adapters (`self._adapters.{domain}.method(dto_input)`), never
  Processors or Services directly.
- Adapters are shared with the GQL layer — do not create REST-specific adapters.

## DTOs

- Use DTOs from `common/dto/manager/v2/` exclusively.
- Never import from `common/dto/manager/` (those are v1 DTOs used by legacy REST handlers).
- Never define REST-specific request/response models — use the shared v2 DTOs.

## Naming

- Scoped endpoints: `{scope}_operation` prefix (e.g., `domain_search_users`).
- Superadmin-only endpoints: `admin_` prefix + `superadmin_required` middleware.

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
