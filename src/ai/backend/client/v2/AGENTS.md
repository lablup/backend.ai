# Client SDK v2 — Guardrails

## Architecture

```
CLI v2 → SDK v2 (domains_v2/) → REST v2 API (/v2/...)
```

Place SDK v2 domain clients in `client/v2/domains_v2/{entity}.py`.
Each client class inherits from `BaseDomainClient` and uses `self._client.typed_request()`.

## Naming conventions

- admin methods: `admin_search()`, `admin_create()`, `admin_update()`, `admin_delete()`, `admin_purge()`
- scoped search methods: `scoped_search(request)`, taking the scope as a field of the request DTO.
  **Legacy:** `{scope}_search()` — e.g. `project_search(project_id, request)` — do not add new ones.
- self-service methods: `my_search()`, `my_issue()` — mapped to `/v2/{entity}/my/{operation}`
- user-facing methods: `get()`, `enqueue()`

**scoped search URL pattern:**
- The SDK method calls `POST /v2/{entity}/scoped/search`, e.g. `f"{_PATH}/scoped/search"`.
- **Legacy:** `POST /v2/{entity}/{scope_type}/{scope_id}/search` — do not add new ones.
- Do NOT use the `search-by-{scope}` URL pattern.

## typed_request pattern

```python
async def admin_create(self, request: CreateFooInput) -> FooPayload:
    return await self._client.typed_request(
        "POST", _PATH, request=request, response_model=FooPayload,
    )
```

- Request/response models come from `common/dto/manager/v2/{entity}/`.
- HTTP methods: POST (create/search/delete/purge), GET (get), PATCH (update).

## Adding a new entity

1. Create `domains_v2/{entity}.py` holding the domain client class
2. Register it in `v2_registry.py` with `@cached_property`
