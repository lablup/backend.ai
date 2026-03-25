# Client SDK v2 — Guardrails

## Architecture

```
CLI v2 → SDK v2 (domains_v2/) → REST v2 API (/v2/...)
```

SDK v2 domain clients live in `client/v2/domains_v2/{entity}.py`.
Each client class inherits `BaseDomainClient` and uses `self._client.typed_request()`.

## Naming Conventions

- Admin methods: `admin_search()`, `admin_create()`, `admin_update()`, `admin_delete()`, `admin_purge()`
- User-facing methods: `get()`, `search_by_domain()`, `search_by_project()`
- Self-service methods: methods without scope prefix (adapter resolves user internally)

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
