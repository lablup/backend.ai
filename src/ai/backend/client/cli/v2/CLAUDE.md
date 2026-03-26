# CLI v2 — Guardrails

## Command Hierarchy

```
./bai [admin|my] {entity} [{sub-entity}] {command} [options]
```

- `cli/v2/{entity}/commands.py` — user-facing commands (any authenticated user)
- `cli/v2/admin/{entity}.py` — admin-only commands (superadmin required)
- `cli/v2/my/{entity}.py` — self-service commands (current user's own resources)

## Admin vs Non-admin vs My Placement

**Admin-only operations MUST go in `admin/{entity}.py`, NOT in `{entity}/commands.py`.**

- `create`, `update`, `delete`, `purge` for admin-only entities (Domain, ContainerRegistry, etc.) → `admin/`
- `search` without scope (queries entire system) → `admin/`
- `get` by ID (any authenticated user) → `{entity}/commands.py`
- Scoped search (e.g., `--scope-domain`) → `{entity}/commands.py`

**Self-service operations (`my_` prefix on the server) MUST go in `my/{entity}.py`.**

- Self-service operations that act on the current user's own resources → `my/`
- Maps to `my_` prefix server APIs and `/v2/{entity}/my/` REST endpoints (`my` is a scope qualifier, entity comes first)
- Examples: `./bai my keypair search`, `./bai my keypair issue`

If both admin and non-admin variants exist for the same operation (different behavior, not just permissions), put admin in `admin/` and non-admin in `{entity}/commands.py`.

## SDK v2 Integration

- CLI calls SDK v2 methods (`registry.{entity}.method()`), never REST directly.
- SDK client: `client/v2/domains_v2/{entity}.py`
- SDK registry: `client/v2/v2_registry.py`
- New SDK domain clients must be registered as `@cached_property` in `V2ClientRegistry`.

## Command Patterns

- JSON body as CLI argument for create/update: `./bai admin domain create '{"name":"foo"}'`
- Entity identifier as argument for get/delete/purge: `./bai admin domain delete foo`
- Filter options as `--option` flags for search: `./bai admin domain search --name-contains foo`
- Use `print_result()` helper for JSON output.
- Use lazy imports inside command functions for DTO classes.

## Adding a New Entity

1. Create `cli/v2/{entity}/commands.py` with user-facing commands + `__init__.py`
2. Create `cli/v2/admin/{entity}.py` with admin-only commands
3. Create `cli/v2/my/{entity}.py` with self-service commands (if applicable)
4. Register user-facing group in `cli/v2/__init__.py`
5. Register admin group in `cli/v2/admin/__init__.py`
6. Register my group in `cli/v2/my/__init__.py` (if applicable)
