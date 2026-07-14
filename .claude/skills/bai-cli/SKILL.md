---
name: bai-cli
description: ./bai v2 CLI usage for testing/verifying API endpoints and managing resources — entity-command reference, login/config, search patterns, testing workflow (REST API client, NOT the v1 backend.ai CLI)
tags:
  - cli
  - bai
  - testing
  - rest-api
---

# ./bai CLI Usage Guide

Guide for testing and verifying API endpoints and managing resources with the Backend.AI **v2 CLI** (`./bai`).

**IMPORTANT:**
- `./bai` is the v2 REST API CLI. It is separate from the legacy v1 CLI (`backend.ai` / `./backend.ai`).
- Do NOT use v1 CLI commands. Do all testing and verification with `./bai`.
- **Before running a `./bai` command, confirm the command exists in the Entity-Command Reference below.** No guessing or fabrication, no searching the CLI source.
- Verify the command tree with `--help` (works without a server): `./bai {entity} --help`, `./bai admin {entity} --help`, `./bai my {entity} --help`.

### v1 → v2 terminology

| v1 (legacy, do NOT use) | v2 (`./bai`) |
|--------------------------|-------------|
| `group` | `project` |
| `backend.ai vfolder list` | `./bai vfolder my-search` |
| `backend.ai admin vfolders` | `./bai vfolder admin-search` |
| `backend.ai ps` | `./bai my session search` |

---

## Entity-Command Reference

Syntax: `./bai [admin|my] {entity} [{sub-entity}] {command} [options]`

Each entity is marked by access level — **user** (user-facing) / **admin** (superadmin only) / **my** (own resources).
"(empty group)" is a placeholder group with no commands (example: `./bai agent` is empty and the actual commands are under `./bai admin agent`).
Check options with `--help`.

### Core

- **domain**: user(get) · admin(search, create, update, delete, purge)
- **user**: user(get, create, update, delete, search) · admin(create, delete, search)
- **project**: user(get, assign-users, unassign-users · sub role: search) · admin(search, create, update, delete, purge)
- **agent**: user(empty group) · admin(search, total-resources)
- **image**: user(empty group) · admin(search, forget, purge, update · sub alias: create, remove, search)
- **session**: user(enqueue, get, logs, project-search, start-service, shutdown-service, terminate, update) · admin(search · sub kernel: search) · my(search)

### Compute & Serving

- **deployment**: user(create, get, update, delete, project-search, chat) · admin(search) · my(search)
  - user sub: access-token(create, get, search, delete, bulk-delete), auto-scaling-rule(create, get, search, update, delete, bulk-delete), replica(search), revision(add, get, current, activate, search), revision-preset(get, search), options(get, replace), chat-cache(show, clear), chat-config(set, show, clear), chat-history(show, clear), policy(empty group)
  - admin sub: policy(search), replica(search), revision(search, refresh), revision-preset(create, get, search, update, delete)
- **model-card**: user(project-search, get, deploy, available-presets) · admin(search, get, create, update, delete, bulk-delete, scan)
- **service-catalog**: user(empty group) · admin(search)
- **runtime-variant**: user(get, search) · admin(get, search, create, update, delete, bulk-delete)
- **runtime-variant-preset**: user(get, search) · admin(get, search, create, update, delete)
- **scheduling-history**: sub session / deployment / route — each (search, search-scoped)
- **scheduling-handler**: admin(list)

### Storage

- **vfolder**: user(my-search, project-search, admin-search, create, project-create, get, upload, download, delete, purge, restore, ls, mkdir, mv, rm, clone, deploy, bulk-delete, bulk-purge)
- **vfs-storage**: user(create, get, search, list-all, update, delete)
- **storage-namespace**: user(register, unregister, search, get-by-storage)
- **object-storage**: user(create, get, search, update, delete)
- **storage-host**: my(permissions)

### Registries & Artifacts

- **container-registry**: user(empty group) · admin(search, create, update, delete)
- **artifact**: user(get, update, delete, restore · sub revision: get, approve, reject, cancel-import, cleanup) · admin(search)
- **artifact-registry**: user(get)
- **huggingface-registry**: user(create, get, search, update, delete) — no admin variant
- **reservoir-registry**: user(create, get, search, update, delete)

### Access Control & Auth

- **rbac**: sub assignment(assign, revoke, search), entity(search), permission(search),
  invitation(create, accept, reject, cancel, my-search, my-sent-search, role-search),
  role(create, get, search, update, delete, project-search, add-permission, remove-permission, replace-permission)
- **role**: my(search)
- **role-preset**: admin(create, get, search, update, delete, purge, restore, permission-add, permission-remove, permission-search)
- **invitation**: admin(search)
- **keypair**: admin(create, get, search, update, delete · sub ssh: register, get, delete) · my(issue, revoke, search, update, switch-main)
- **login-history**: admin(search) · my(search)
- **login-session**: admin(search, revoke) · my(search, revoke)
- **login-client-type**: user(get) · admin(search, create, update, delete)

### Resource Management

- **resource-group**: user(empty group) · admin(search, get, create, delete, resource-info, default-options, default-session-options, allow-domains, allowed-domains, allow-projects, allowed-projects, allow-for-domain, allowed-for-domain, allow-for-project, allowed-for-project)
- **resource-allocation**: user(project-usage, resource-group-usage) · admin(domain-usage, effective) · my(effective, keypair-usage)
- **resource-preset**: admin(search, get, create, update, delete, check-availability)
- **resource-policy**: admin(sub keypair / project / user — each create, get, search, update, delete) · my(keypair, user)
- **resource-slot**: sub slot-type(search), agent-resource(search), allocation(search)
- **resource-usage**: sub domain(search), project(search), user(search)

### Monitoring & Audit

- **audit-log**: user(search)
- **fair-share**: sub domain / project / user — each (get, search)
- **notification**: sub channel(get, search, delete), rule(get, search, delete)
- **prometheus-query-definition**: user(get, search, execute) · admin(create, update, delete, preview)
- **prometheus-query-definition-category**: user(get, search) · admin(create, delete)
- **app-config**: user(get-domain, get-user, get-merged, delete-domain, delete-user)
- **app-config-definition**: admin(create, get, search, purge)
- **app-config-allow-list**: admin(create, get, search, update, purge)
- **export**: admin(list-reports, get-report, audit-logs, keypairs, projects, sessions, sessions-by-project, users, users-by-domain) · my(keypairs, sessions)

### Utilities (not entities)

`login`, `logout`, `config`, `gql` — single commands at the root.

> When adding a new CLI command, update this Reference as well (see "Adding a new entity" in `client/cli/v2/AGENTS.md`).

---

## Setup (Webserver session — recommended)

```bash
./bai config set endpoint http://127.0.0.1:8090
./bai config set endpoint-type session
./bai login
# User ID: admin@lablup.com
# Password: (admin password)
./bai config show
```

Non-interactive environments (CI, Claude Code):

```bash
BACKEND_USER=admin@lablup.com BACKEND_PASSWORD=wJalrXUt ./bai login
```

The session cookie is stored in `~/.backend.ai/session/cookie.dat`.

### Direct API (alternative)

Access the manager directly without the webserver (HMAC signature auth):

```bash
./bai config set endpoint http://127.0.0.1:8091
./bai config set endpoint-type api
./bai config set access-key AKIAIOSFODNN7EXAMPLE
./bai config set secret-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
./bai config show
```

The configuration is stored in `~/.backend.ai/config.toml` and `credentials.toml`.

## Command pattern

```
./bai [admin|my] {entity} [{sub-entity}] {command} [options]
```

- `admin` — superadmin-only operations
- `my` — self-service (the current user's own resources)
- Entity names are **singular** (domain, user, agent)
- A sub-entity is a Click sub-group (revision, channel, role, etc.)

The standard 6 operations: `create`, `get`, `search`, `update`, `delete`, `purge` (only some, depending on the entity).
Special operations: `enqueue`/`terminate` (session), `revision add`/`revision activate` (deployment), `login`/`logout`.

## CLI input style

- **Default:** an individual `--option` flag per field.
- **Secondary:** a JSON string or an `@file` path for complex nested structures (example: `--initial-revision`, `--config`).
- Do NOT use raw JSON as a positional argument for create/update (with some admin command exceptions: `admin domain create`).
- For get/delete/purge, use the entity identifier (UUID, name) as a positional argument.

## Search patterns

```bash
# admin search — whole system (superadmin only)
./bai admin {entity} search --limit 5

# project-scoped search — the scope ID is a positional argument (not an option)
./bai {entity} project-search {project_id} --limit 5

# self-service search — own resources
./bai my {entity} search --limit 5
```

Options and filters differ per entity, so check with `./bai {entity} {command} --help`.

### --order-by syntax

Multi-sort with `field:direction`:

```bash
./bai admin user search --order-by created_at:desc --order-by username:asc
```

## Naming conventions

- The CLI `--order-by` maps to the DTO `order` field (common across all entities).
- The CLI `--kebab-case` option maps to the DTO `snake_case` field (Click standard).
- Scoped search: the scope ID is a **positional argument**, not a `--scope-*` option.

## Raw GraphQL

`./bai gql` (not `./bai admin gql`) sends a raw GraphQL query. Useful for testing GQL schema changes or when there is no REST CLI:

```bash
./bai gql '{ domain(name: "default") { name } }'
./bai gql --v2 '{ myKeypairs(first: 5) { count edges { node { accessKey } } } }'
./bai gql -f query.graphql
./bai gql --var limit=5 '{ keypair_list(limit: $limit) { items { access_key } } }'
```

- `--v2`: targets the Strawberry v2 schema (only needed in direct API mode; session mode provides both)
- `--var key=value`: query variables (repeatable)
- `-f file`: read the query from a file
- stdin: `echo '{ ... }' | ./bai gql`

## Common commands

```bash
# admin search + filter (superadmin only)
./bai admin domain search --limit 5 --name-contains default
./bai admin user search --status active --order-by created_at:desc
./bai admin agent search --limit 10
./bai admin image search --name-contains python
./bai admin session search --limit 5

# single entity lookup
./bai domain get default
./bai user get <uuid>

# sub-entity operations
./bai admin deployment revision search
./bai rbac role search
./bai notification channel search
./bai scheduling-history session search --limit 10
```

## Testing workflow

### Prerequisites

```bash
./bai config show   # check endpoint-type
./bai login         # log in if the session expired
```

### After modifying server code

For local development, restart the service first — see the `/local-dev` skill.

```bash
# 1. confirm basic connectivity
./bai admin domain search --limit 1
./bai domain get default

# 2. test the modified entity (with the command matching its level)
#    if user-facing ./bai {entity} ..., if admin-only ./bai admin {entity} ...
./bai admin {entity} search --limit 1
./bai {entity} get {id}

# 3. test the permission boundary
./bai admin {entity} search    # admin succeeds
# after switching to a regular user, the same command → should fail with 403
```

After commands, verify the runtime behavior with the Grafana MCP — see `/observability`.
To catch errors not surfaced in the CLI response, check Loki (`{service_name="manager"} |= "error"`);
to check the request count, look at Prometheus (`backendai_api_request_count`).

### Testing as a regular user

The default accounts are in `fixtures/manager/example-users.json`.

```bash
# log in as a regular user session
BACKEND_USER=user@lablup.com BACKEND_PASSWORD=C8qnIo29 ./bai login

# should succeed (user-facing)
./bai domain get default

# should fail with 403 (admin only)
./bai admin domain search --limit 1
```

After testing, revert to the admin credentials.

## Smoke test script

Run everything with admin credentials. OK if each command returns JSON.

```bash
for cmd in \
  "admin domain search --limit 1" \
  "domain get default" \
  "admin user search --limit 1" \
  "admin project search --limit 1" \
  "admin agent search --limit 1" \
  "admin image search --limit 1" \
  "admin session search --limit 1" \
  "admin resource-group search --limit 1" \
  "audit-log search --limit 1" \
  "rbac role search --limit 1"; do
  echo -n "$cmd: "
  ./bai $cmd 2>&1 | python3 -c "import sys,json;json.load(sys.stdin);print('OK')" 2>&1 || echo "FAIL"
done
```

## When a CLI command is unavailable

If the CLI command for an entity/operation is not in the Reference above:

1. That command is **not implemented**.
2. **Report to the user**: "{entity} {operation} is not provided via the CLI. It needs to be implemented."
3. As a temporary workaround, try `./bai gql` for operations available via GraphQL.
4. Do NOT guess CLI options or fabricate commands — it wastes time and causes errors.

## Related skills

- `/local-dev` — restart local services before CLI testing
- `/observability` — check logs/metrics with the Grafana MCP after CLI testing
- `/cli-sdk-guide` — implement new CLI commands
