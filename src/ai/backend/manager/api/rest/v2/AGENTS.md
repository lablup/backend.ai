# REST v2 API layer — Guardrails

> For background (pagination mode behavior, DI example, scoped URL examples), see `CONTEXTS.md` in the same directory; for implementation patterns, see the `/api-guide` skill.
> REST v2 uses the Pydantic DTOs in `common/dto/manager/v2/` — the same DTOs as the GQL schema (single source).

## Architecture

```
REST v2 Handler → Adapter (api/adapters/) → Processor → Service → Repository
```

## Handler style

- Every handler must be a method of an `APIHandler` class.
- Parse requests with `BodyParam[T]` — `T` is a DTO from `common/dto/manager/v2/`.
- Return via `APIResponse.build(status_code=..., response_model=payload)` — `payload` is also a v2 DTO.

## Handler dependency injection

- Each handler is injected with an **individual adapter** (not the Adapters registry): call `self._adapter.method()` —
  no `self._adapters.domain.method()`.
- The Adapter is shared with the GQL layer — do not create a REST-only adapter.

## DTO

- Use only the DTOs in `common/dto/manager/v2/`.
- Do not import from `common/dto/manager/` (v1, for legacy REST).
- Do not define REST-only request/response models — use the shared v2 DTOs.

## Naming & scope

Method names carry the audience as a prefix: `admin_`, `scoped_`, `my_`.
**Legacy:** scoped endpoints named after the scope (`project_search`) — do not add new ones.

**URL grammar:** `/v2/{entity}/{audience}/{operation}`

| Segment | Rule |
|---|---|
| `{entity}` | The resource. For a sub-app covering several entities, the `{domain}/{entity}` pair — `/v2/scheduling-history/kernels/…`. `{entity}` below means the whole pair. |
| `{audience}` | Exactly one of `admin` / `scoped` / `my`, matching the method prefix. Never omitted. |

**the three audiences:**

| Audience | Who | Scope | Middleware |
|---|---|---|---|
| `admin` | superadmin only | none — system-wide | `superadmin_required` |
| `scoped` | non-admin | required | `auth_required` |
| `my` | the caller | the adapter resolves the user via `current_user()` | `auth_required` |

- search always has both `admin` and `scoped` variants — there is no "unscoped system-wide query" for non-admins.
- e.g. `POST /v2/{entity}/admin/search`, `POST /v2/{entity}/scoped/search`, `POST /v2/keypairs/my/issue`.

**how the scope reaches a `scoped` endpoint:**
- The scope is a **request body field**, so the path stays the fixed `/v2/{entity}/scoped/search`.
  Consistent with SDK `scoped_search` and GQL `scopedFoosV2`.
- **Legacy:** a nested resource path, `POST /v2/{entity}/{scope_type}/{scope_id}/search`
  (e.g. `/v2/sessions/projects/{project_id}/search`). Most existing routes still look like this —
  do not add new ones. (Examples: `CONTEXTS.md`)

**create / update / get / delete / purge — criteria for splitting out `admin_`:**
- admin-only entities: a single `admin_`.
- both admin and user with different behavior: split `admin_` and non-admin (different DTOs).
- differing only in permission checks: a single one — admins already have access.

## Pagination

- Accept both cursor and offset arguments. Only one mode per request — mixing `first` and `limit` is an error.
- For mode-specific behavior and defaults, see `CONTEXTS.md`.

## Routing

- Register routes via the `RouteRegistry` (the same framework as REST v1), from a per-domain dedicated registrar function.

## What belongs here / What does NOT belong here

- Belongs: HTTP request/response conversion, auth middleware (`superadmin_required`, `auth_required`).
- Does NOT belong: business logic / domain rules, direct DB access or ORM imports, Repository/Service/Processor imports,
  domain Data ↔ DTO conversion (the Adapter's responsibility).
