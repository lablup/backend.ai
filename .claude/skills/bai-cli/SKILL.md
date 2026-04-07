# ./bai CLI Usage Guide

Guide for using the Backend.AI **v2 CLI** to test API endpoints, verify changes, and manage resources.

**IMPORTANT:**
- `./bai` is the v2 REST API CLI. It is separate from the legacy v1 CLI (`backend.ai` / `./backend.ai`).
- Do NOT use v1 CLI commands. All testing and verification MUST use `./bai`.
- **BEFORE running any `./bai` command, check the Entity-Command Reference below** to confirm the command exists. Do NOT guess or fabricate commands. Do NOT explore CLI source code.

### v1 → v2 Terminology

| v1 (legacy, do NOT use) | v2 (`./bai`) |
|--------------------------|-------------|
| `group` | `project` |
| `backend.ai vfolder list` | `./bai vfolder my-search` |
| `backend.ai admin vfolders` | `./bai vfolder admin-search` |
| `backend.ai ps` | `./bai my session search` |

---

## Entity-Command Reference

Syntax: `./bai [admin|my] {entity} [{sub-entity}] {command} [options]`

Verify options with `--help`: `./bai {entity} {command} --help`

### Core

- **domain**: user(get) | admin(search, create, update, delete)
- **user**: user(get, create, update, delete, search) | admin(create, delete)
- **project**: user(get) | admin(search, create, update, delete)
- **agent**: admin(search, create, delete)
- **image**: admin(search, create, delete)
- **session**: user(enqueue, get, project-search, terminate, start-service, shutdown-service, logs, update) | admin(search) | my(search)
  - admin sub: kernel(search, inspect, restart)

### Compute & Serving

- **deployment**: user(project-search, get, create, update, delete) | admin(search) | my(search)
  - admin sub: revision(search, add, get, current, activate), replica(search, scale-up, scale-down)
- **model-card**: user(project-search, get, deploy, available-presets) | admin(search, create, update, delete)
- **service-catalog**: admin(search, create, update, delete)
- **runtime-variant**: user(search, get) | admin(search, create, update, delete)
- **runtime-variant-preset**: user(search, get) | admin(search, create, update, delete)
- **scheduling-history**: sub: session(search, search-scoped), deployment(search, search-scoped), route(search, search-scoped)

### Storage

- **vfolder**: user(my-search, project-search, admin-search, create, get, upload, download, delete, purge, ls, mkdir, mv, rm, clone, bulk-delete, bulk-purge)
- **vfs-storage**: user(create, list-all, get, update, search, delete)
- **storage-namespace**: user(register, unregister, search, get-by-storage)
- **object-storage**: user(create, get, update, search, delete)

### Registries & Artifacts

- **container-registry**: admin(search, create, update, delete)
- **artifact**: user(get, update, delete, restore) | admin(search, purge)
  - user sub: revision(get, approve, reject, cancel-import, cleanup)
- **artifact-registry**: user(get) | admin(search, create, update, delete)
- **huggingface-registry**: user(create, search, get, update, delete) | admin(search)
- **reservoir-registry**: user(create, search, get, update, delete) | admin(search)

### Access Control & Auth

- **rbac**: sub: role(search, get, create, delete), permission(search), assignment(search, assign, revoke), entity(search)
- **keypair**: admin(search, get, create, update, delete) | my(search, create, issue, delete)
- **login-history**: admin(search) | my(search)
- **login-session**: admin(search, delete) | my(search, delete)

### Resource Management

- **resource-group**: user(search, get, create, delete, resource-info, allowed-for-domain, allow-for-domain, allowed-for-project, allow-for-project, allowed-domains, allow-domains, allowed-projects, allow-projects) | admin(search, create, update, delete)
- **resource-allocation**: user(project-usage, resource-group-usage) | admin(search, create, update, delete) | my(search)
- **resource-preset**: admin(search, get, create, update, delete)
- **resource-policy**: admin(search, get, create, update, delete) | my(search)
- **resource-slot**: sub: slot-type(search), agent-resource(search), allocation(search)
- **resource-usage**: sub: domain(search), project(search), user(search)

### Monitoring & Audit

- **audit-log**: user(search) | admin(search)
- **scheduling-history**: sub: session(search, search-scoped), deployment(search, search-scoped), route(search, search-scoped)
- **fair-share**: sub: domain(search, get), project(search, get), user(search, get)
- **notification**: sub: channel(search, get, delete), rule(search, get, delete)
- **prometheus-query-definition**: user(search, get, create, update, execute, delete) | admin(search, create, update, delete)
- **app-config**: user(get-domain, delete-domain, get-user, delete-user, get-merged) | admin(create, update, delete)
- **export**: admin(list, request, purge) | my(list, request, purge)

---

## Setup (Webserver Session — Recommended)

```bash
./bai config set endpoint http://127.0.0.1:8090
./bai config set endpoint-type session
./bai login
# User ID: admin@lablup.com
# Password: (admin password)
./bai config show
```

For non-interactive environments (CI, Claude Code):

```bash
BACKEND_USER=admin@lablup.com BACKEND_PASSWORD=changeme ./bai login
```

Session cookie stored in `~/.backend.ai/session/cookie.dat`.

### Direct API (Alternative)

For direct manager access without webserver (HMAC signature auth):

```bash
./bai config set endpoint http://127.0.0.1:8091
./bai config set endpoint-type api
./bai config set access-key AKIAIOSFODNN7EXAMPLE
./bai config set secret-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
./bai config show
```

Config stored in `~/.backend.ai/config.toml` and `credentials.toml`.

## Command Pattern

```
./bai [admin|my] {entity} [{sub-entity}] {command} [options]
```

- `admin` — superadmin-only operations
- `my` — self-service (current user's own resources)
- Entity names are **singular** (domain, user, agent)
- Sub-entities are Click sub-groups (revision, channel, role)

Standard 6 operations: `create`, `get`, `search`, `update`, `delete`, `purge`.
Special operations: `enqueue`/`terminate` (session), `revision add`/`revision activate` (deployment), `login`/`logout`.

## CLI Input Style

- **Primary:** Individual `--option` flags for each field.
- **Secondary:** JSON string or `@file` path for complex nested structures (e.g., `--initial-revision`, `--config`).
- Never use raw JSON as a positional argument for create/update (except some admin commands like `admin domain create`).
- Entity identifier (UUID, name) as positional argument for get/delete/purge.

## Search Patterns

Four distinct search scopes:

```bash
# Admin search — entire system (superadmin only)
./bai admin {entity} search --limit 5

# Project-scoped search — positional scope ID (not --option)
./bai {entity} project-search {project_id} --limit 5

# Self-service search — current user's own resources
./bai my {entity} search --limit 5

# User search with scope filters
./bai {entity} search --scope-domain default --limit 5
```

### --order-by Syntax

Multiple ordering via `field:direction`:

```bash
./bai admin user search --order-by created_at:desc --order-by username:asc
```

## Naming Conventions

- CLI `--order-by` maps to DTO `order` field (by design, all entities follow this)
- CLI `--kebab-case` options map to DTO `snake_case` fields (standard Click convention)
- Scoped search: scope ID is a **positional argument**, not a `--scope-*` option

## Raw GraphQL

`./bai gql` (NOT `./bai admin gql`) sends raw GraphQL queries, useful for testing GQL schema changes or when REST CLI is unavailable:

```bash
./bai gql '{ domain(name: "default") { name } }'
./bai gql --v2 '{ myKeypairs(first: 5) { count edges { node { accessKey } } } }'
./bai gql -f query.graphql
./bai gql --var limit=5 '{ keypair_list(limit: $limit) { items { access_key } } }'
```

- `--v2`: Target Strawberry v2 schema (only needed in direct API mode; session mode serves both)
- `--var key=value`: Pass query variables (repeatable)
- `-f file`: Read query from file
- Stdin: `echo '{ ... }' | ./bai gql`

## Common Commands

```bash
# Admin search with filters (superadmin only)
./bai admin domain search --limit 5 --name-contains default
./bai admin user search --status active --order-by created_at:desc
./bai admin agent search --limit 10
./bai admin image search --name-contains python
./bai admin session search --limit 5

# Get single entity
./bai domain get default
./bai user get <uuid>

# Sub-entity operations
./bai admin deployment revision search
./bai rbac role search
./bai notification channel search
./bai scheduling-history session search --limit 10
```

## Testing Workflow

### Prerequisites

```bash
./bai config show   # Check endpoint-type
./bai login         # Login if session expired
```

### After Modifying Server Code

For local development, restart services first — see `/local-dev` skill.

```bash
# 1. Verify basic connectivity
./bai admin domain search --limit 1
./bai domain get default

# 2. Test the entity you modified
./bai admin {entity} search --limit 1
./bai {entity} get {id}

# 3. Test permission boundaries
./bai admin {entity} search    # Should work as admin
# Switch to regular user, same command should fail with 403
```

### Testing as a Regular User

Default accounts in `fixtures/manager/example-users.json`.

```bash
# Session login as regular user
BACKEND_USER=user@lablup.com BACKEND_PASSWORD=C8qnIo29 ./bai login

# Should succeed (user-facing)
./bai domain get default

# Should fail with 403 (admin-only)
./bai admin domain search --limit 1
```

Remember to switch back to admin credentials after testing.

## Smoke Test Script

```bash
for cmd in \
  "admin domain search --limit 1" \
  "domain get default" \
  "admin user search --limit 1" \
  "admin project search --limit 1" \
  "admin agent search --limit 1" \
  "admin image search --limit 1" \
  "admin session search --limit 1" \
  "resource-group search --limit 1" \
  "audit-log search --limit 1" \
  "rbac role search --limit 1"; do
  echo -n "$cmd: "
  ./bai $cmd 2>&1 | python3 -c "import sys,json;json.load(sys.stdin);print('OK')" 2>&1 || echo "FAIL"
done
```

## CLI Command Not Available

If a CLI command for an entity/operation does not exist in the reference above:

1. The command is **not implemented**
2. **Report to the user**: "{entity} {operation} is not available via CLI. Implementation is needed."
3. As a workaround, try `./bai gql` for GraphQL-accessible operations
4. Do NOT guess CLI options or fabricate commands — this wastes time and causes errors

## Related Skills

- `/local-dev` — Restart local services before CLI testing
- `/cli-sdk-guide` — Implement new CLI commands
