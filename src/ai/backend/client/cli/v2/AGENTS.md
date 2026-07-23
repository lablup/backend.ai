# CLI v2 — Guardrails

## Command hierarchy

```
./bai [admin|my] {entity} [{sub-entity}] {command} [options]
```

- `cli/v2/{entity}/commands.py` — user-facing commands (any authenticated user)
- `cli/v2/admin/{entity}.py` — admin-only commands (superadmin required)
- `cli/v2/my/{entity}.py` — self-service commands (the current user's own resources)

## admin / non-admin / my placement

**Place admin-only operations in `admin/{entity}.py`, not in `{entity}/commands.py`.**

- `create`, `update`, `delete`, `purge` of admin-only entities (Domain, ContainerRegistry, etc.) → `admin/`
- unscoped `search` (system-wide query) → `admin/`
- `get` by ID (any authenticated user) → `{entity}/commands.py`
- scoped search → take the scope as a required argument in `{entity}/commands.py`

**scoped search CLI pattern:**
- Command name `search-scoped`, mapped to SDK `scoped_search()` and REST `POST /v2/{entity}/scoped/search`.
- The scope ID is a required positional argument, not an option flag.
- **Legacy:** a command named after the scope — `./bai session project-search {project_id}` — do not add new ones.

**Place self-service operations (server `my_` prefix) in `my/{entity}.py`.**

- self-service operations dealing with the current user's own resources → `my/`
- Mapped to the server `my_`-prefixed API and the `/v2/{entity}/my/` REST endpoint (`my` is the scope qualifier, the entity comes first)
- e.g. `./bai my keypair search`, `./bai my keypair issue`

If an operation has both admin and non-admin variants (differing in behavior, not just permission), place the admin one in `admin/` and the
non-admin one in `{entity}/commands.py`.

## SDK v2 integration

- The CLI calls SDK v2 methods (`registry.{entity}.method()`) — direct REST calls are forbidden.
- SDK client: `client/v2/domains_v2/{entity}.py`
- SDK registry: `client/v2/v2_registry.py`
- Register new SDK domain clients in `V2ClientRegistry` with `@cached_property`.

## Operation naming

The standard 6 operations use fixed command names: `create`, `get`, `search`, `update`, `delete`, `purge`.
Only operations outside the 6-op pattern use different names:
- `enqueue`, `terminate` (session lifecycle)
- `revision add`, `revision activate`, `revision current` (deployment revision)
- `login`, `logout` (auth)

## Command input style

- **Default:** an individual `--option` flag per field.
- **Auxiliary:** for deeply nested structures (e.g. revision config), take a JSON string or `@file` path in a single option
  (e.g. `--config '{"cluster_config": ...}'` or `--config @revision.json`).
- **Never** use raw JSON as a positional argument for create/update.
- get/delete/purge take the entity identifier (UUID, name) as a positional argument.
- search filters use `--option` flags: `./bai admin domain search --name-contains foo`
- Use the `print_result()` helper for JSON output.
- Lazy-import DTO classes inside the command function.

## Adding a new entity

1. Create `cli/v2/{entity}/commands.py` holding user-facing commands + `__init__.py`
2. Create admin-only commands `cli/v2/admin/{entity}.py`
3. Create self-service commands `cli/v2/my/{entity}.py` (if applicable)
4. Register the user-facing group in `cli/v2/__init__.py`
5. Register the admin group in `cli/v2/admin/__init__.py`
6. Register the my group in `cli/v2/my/__init__.py` (if applicable)
7. Register the new entity and commands in the `/bai-cli` skill's Entity-Command Reference (so tests know what to run).
