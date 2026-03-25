# Manager API Layer — Guardrails

> For full implementation patterns, see the `/api-guide` skill.

## Handler Style

- All handlers MUST be methods on an `APIHandler` class — no module-level async functions.
- Parse requests via `BodyParam[T]` and `PathParam[T]` — never read `request.json()` or
  `request.rel_url.query` directly inside a handler.
- Return `APIResponse.build(status_code=..., response_model=...)` — never `web.json_response()`.

## Calling Services

**New API (v2):** Handlers MUST call Adapters (`self._adapters.{domain}.method(dto_input)`),
never Processors or Services directly. Adapters are shared with the GQL layer.

**Legacy REST (v1):** Handlers call Processors directly:
  ```python
  await self._foo.wait_for_complete(FooAction(...))
  ```

**All new API endpoints MUST follow the v2 pattern.**

## Naming

- Scoped endpoints: `{scope}_create_`, `{scope}_search_`, `{scope}_update_`, ... prefix.
- Superadmin-only endpoints (no scope): `admin_` prefix + call `_check_superadmin(request)` first.

## Routing

- Route registration belongs exclusively in `create_app()`.
- `app["prefix"]` must be set to the URL segment for this sub-app.

## What Belongs Here

- HTTP request/response translation only.
- Auth decorators (`@auth_required_for_method`).

## Adapter `my_` Pattern

For self-service (`my_`) endpoints, the Adapter method handles authentication internally:
- The Adapter calls `current_user()` internally to obtain the user context.
- The Adapter constructs the `SearchScope` from the user context.
- The GQL resolver / REST handler does NOT pass scope — only the search input DTO.
- This keeps authentication logic inside the adapter, not scattered across resolvers.

## V2 DTO — Single Source of Truth

v2 DTOs (`common/dto/manager/v2/`) are the shared schema for:
- REST v2 handlers (`api/rest/v2/`)
- GraphQL (Strawberry) types (`api/gql/`)
- Client SDK (`client/v2/domains_v2/`)
- CLI (`client/cli/v2/`)

**Any DTO change affects all four layers.** Coordinate updates across:
1. DTO definition → 2. Adapter → 3. REST handler → 4. GQL type → 5. SDK client → 6. CLI command

## Testing v2 Endpoints

Use `./bai` (= `./backend.ai v2`) to test REST v2 endpoints directly.
After server-side changes, restart with `./dev restart mgr` and verify with `./bai`.
See `/local-dev` skill for detailed usage patterns.

## What Does NOT Belong Here

- Business logic or domain rules.
- Direct database access or ORM imports from `manager/models/`.
- Imports of Repository or Service classes (use Processors via context).
