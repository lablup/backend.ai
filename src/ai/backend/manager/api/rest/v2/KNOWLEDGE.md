---
name: rest-v2-handler-and-pagination
type: reference
description: adapter-backed handlers and gate registration (admin_/public/scoped), handler dependency-injection example, scoped search URL direction, cursor vs offset pagination mode behavior
scope: src/ai/backend/manager/api/rest/v2
keywords: [BodyParam, APIResponse, scoped search, cursor, offset, pagination]
generated:
  by: claude-code/fable-5
  at: 2026-08-10
status: stable
---
# REST v2 API layer — Knowledge

> For rules, see `AGENTS.md` in the same directory; for implementation patterns, see the `/api-guide` skill.

## Adapter dependency and operation surface

Handlers hold no behavior — every handler calls the shared per-entity adapter
(`api/adapters/`). Registration mirrors the gates: `admin_*` handlers register with
`superadmin_required`, bare global reads register with `auth_required` only (public
reads), and scoped searches take the scopes from the request body.

## Handler dependency injection example

```python
class V2DomainHandler:
    _adapter: DomainAdapter

    def __init__(self, *, adapter: DomainAdapter) -> None:
        self._adapter = adapter

    async def admin_search(self, body: BodyParam[T]) -> APIResponse:
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
```

## Scoped search URLs

- Current direction: one `scoped/search` endpoint per entity taking caller-supplied
  scopes in the body (e.g. `POST .../kernels/scoped/search`,
  `POST .../replica-groups/scoped/search` under `scheduling_history/`).
- Outgoing pattern: parent-fixed paths (`POST /v2/sessions/projects/{project_id}/search`,
  `POST /v2/users/domains/{domain_name}/search`, ...). Do not add new ones — a scope is
  request data, not a URL segment.

## Pagination mode behavior

search endpoints accept both cursor and offset pagination arguments.

- **Default (no args):** falls back to offset (`limit=10, offset=0`).
- **Offset (`limit`/`offset`):** applies the user-specified `order`, or the entity's default ordering if absent. Use when custom ordering is needed.
- **Cursor (`first`/`after` or `last`/`before`):** ordering is fixed to the entity's cursor key (usually `created_at` or the PK).
  The user-specified `order` is ignored — a fixed ordering is required for cursor consistency. Suited to infinite scroll / "load more" UX.
- Only one mode per request. Mixing `first`+`limit` is an error.
