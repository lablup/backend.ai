# Client SDK v2 — Guardrails

## Architecture

```
CLI v2 → SDK v2 (domains_v2/) → REST v2 API (/v2/...)
```

SDK v2 domain clients live in `client/v2/domains_v2/{entity}.py`.
Each client class inherits `BaseDomainClient` and uses `self._client.typed_request()`.

## Naming Conventions

- Admin methods: `admin_search()`, `admin_create()`, `admin_update()`, `admin_delete()`, `admin_purge()`
- Scoped search methods: `{scope}_search()` — e.g., `project_search(project_id, request)`, `domain_search(domain_name, request)`
- Self-service methods: `my_search()`, `my_issue()` — maps to `/v2/{entity}/my/{operation}`
- User-facing methods: `get()`, `enqueue()`

**Scoped search URL pattern:**
- SDK method calls `POST /v2/{entity}/{scope_type}/{scope_id}/search`
- Example: `f"{_PATH}/projects/{project_id}/search"` (not `f"{_PATH}/search-by-project/{id}"`)
- Do NOT use `search-by-{scope}` URL pattern.

## typed_request Pattern

```python
async def admin_create(self, request: CreateFooInput) -> FooPayload:
    return await self._client.typed_request(
        "POST", _PATH, request=request, response_model=FooPayload,
    )
```

- Request/response models from `common/dto/manager/v2/{entity}/`
- HTTP methods: POST (create/search/delete/purge), GET (get), PATCH (update)

## Adding a New Entity

1. Create `domains_v2/{entity}.py` with domain client class
2. Register as `@cached_property` in `v2_registry.py`
