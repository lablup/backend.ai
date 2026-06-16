# REST v2 API layer — Contexts

> For rules, see `AGENTS.md` in the same directory; for implementation patterns, see the `/api-guide` skill.

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

## scoped search URL examples (current pattern)

- `POST /v2/sessions/projects/{project_id}/search` — sessions within a project
- `POST /v2/sessions/agents/{agent_id}/search` — sessions on an agent
- `POST /v2/users/domains/{domain_name}/search` — users within a domain
- `POST /v2/users/projects/{project_id}/search` — users within a project
- `POST /v2/users/roles/{role_id}/search` — users with a specific role

## Pagination mode behavior

search endpoints accept both cursor and offset pagination arguments.

- **Default (no args):** falls back to offset (`limit=10, offset=0`).
- **Offset (`limit`/`offset`):** applies the user-specified `order`, or the entity's default ordering if absent. Use when custom ordering is needed.
- **Cursor (`first`/`after` or `last`/`before`):** ordering is fixed to the entity's cursor key (usually `created_at` or the PK).
  The user-specified `order` is ignored — a fixed ordering is required for cursor consistency. Suited to infinite scroll / "load more" UX.
- Only one mode per request. Mixing `first`+`limit` is an error.
