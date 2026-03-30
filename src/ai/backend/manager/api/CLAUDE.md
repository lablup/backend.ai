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

## Naming & Scope Rules

- Superadmin-only endpoints: `admin_` prefix + call `_check_superadmin(request)` first.
- Scoped endpoints: `{scope}_` prefix (e.g., `domain_search_users`).
- Self-service endpoints: `my_` prefix (e.g., `my_keypairs`). Adapter resolves user internally.
  - REST URL pattern: `/v2/{entity}/my/{operation}` — entity first, `my` as scope qualifier.

**search — always two variants:**
- `admin_search_*`: superadmin only, no scope — queries entire system.
- `{scope}_search_*`: non-admin, scope parameter required — queries within the given scope only.
- There is NO "search everything without scope" for non-admin users.

**Scoped search REST URL pattern:**
- Pattern: `/v2/{entity}/{scope_type}/{scope_id}/search`
- Scope is expressed as nested resource path segments, NOT as `search-by-{scope}`.
- Example: `/v2/sessions/projects/{project_id}/search` (not `/v2/sessions/search-by-project/{id}`).

**create / update / get / delete / purge — when to separate `admin_` vs non-admin:**
- **Admin-only entity** (e.g., Domain, ContainerRegistry): single `admin_` endpoint.
- **Both admin and users, behavior differs** (e.g., admin sets more fields): separate `admin_` and non-admin endpoints with different DTOs.
- **Both admin and users, only permission check differs**: single endpoint — admin already has entity access permissions, no separate `admin_` variant needed.

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

**After implementing new API endpoints, verify them with the live server before committing:**

1. Restart the server: `./dev restart mgr` (add `./dev restart web` if GQL schema changed)
2. Login if needed: `./bai login`
3. Test each new operation via `./bai` CLI commands
4. Verify both success cases and expected error cases (e.g., 403 for non-admin)

```bash
# Example: after adding domain CRUD
./dev restart mgr && sleep 5
./bai admin domain create '{"name":"test-domain"}'
./bai domain get test-domain
./bai admin domain update test-domain '{"description":"updated"}'
./bai admin domain delete test-domain
```

See `/local-dev` skill for full setup, `./bai` command patterns, and regular user testing.

## What Does NOT Belong Here

- Business logic or domain rules.
- Direct database access or ORM imports from `manager/models/`.
- Imports of Repository or Service classes (use Processors via context).
