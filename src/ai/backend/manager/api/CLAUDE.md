# Manager API Layer — Guardrails

> For full implementation patterns, see the `/api-guide` skill.

## Handler Style

- All handlers MUST be methods on an `APIHandler` class — no module-level async functions.
- Parse requests via `BodyParam[T]` and `PathParam[T]` — never read `request.json()` or
  `request.rel_url.query` directly inside a handler.
- Return `APIResponse.build(status_code=..., response_model=...)` — never `web.json_response()`.

## Calling Services

- Handlers MUST invoke services through a Processor, not directly:
  ```python
  # CORRECT
  await processors_ctx.processors.foo.wait_for_complete(FooAction(...))
  # WRONG
  await self._foo_service.do_something(...)
  ```

## Naming

- Scoped endpoints: `{scope}_create_`, `{scope}_search_`, `{scope}_update_`, ... prefix.
- Superadmin-only endpoints (no scope): `admin_` prefix + call `_check_superadmin(request)` first.

## Routing

- Route registration belongs exclusively in `create_app()`.
- `app["prefix"]` must be set to the URL segment for this sub-app.

## What Belongs Here

- HTTP request/response translation only.
- Auth decorators (`@auth_required_for_method`).

## What Does NOT Belong Here

- Business logic or domain rules.
- Direct database access or ORM imports from `manager/models/`.
- Imports of Repository or Service classes (use Processors via context).
