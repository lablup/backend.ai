---
name: local-dev
description: Local development tools — service management (./dev) and v2 CLI testing (./bai)
version: 1.0.0
tags:
  - dev
  - testing
  - server
  - cli
  - bai
---

# Local Development Guide

Tools for managing Backend.AI services locally and testing v2 REST API endpoints.

## ./dev — Service Management

Manages Backend.AI services via tmux sessions.

```bash
./dev status                         # Show all service statuses
./dev restart mgr                    # Restart manager only
./dev restart all                    # Restart all services
./dev stop <service|all>             # Stop service(s)
./dev start <service|all>            # Start service(s)
./dev log <service>                  # Show recent log output
```

**Services:** `mgr`, `agent`, `storage`, `web`, `proxy-coordinator`, `proxy-worker`

### Debugging Startup Crashes

`./dev` runs services in tmux — if a service crashes on startup, the tmux window
closes and logs are lost. To see the actual error, run the service directly:

```bash
# Run manager directly to see startup errors (e.g., import errors, schema issues)
PYTHONPATH=src python -c "from ai.backend.manager.api.gql.schema import schema; print('OK')"

# Or test a specific import chain
PYTHONPATH=src python -c "from ai.backend.manager.api.adapters.registry import Adapters; print('OK')"
```

After fixing, restart with `./dev start mgr`.

### After Code Changes

Server-side code changes (handler, adapter, DTO, model) require a server restart:

```bash
./dev restart mgr        # Most changes only need manager restart
sleep 5                  # Wait for server initialization
```

If DTO changes affect GQL schema, also restart webserver:

```bash
./dev restart mgr
./dev restart web
sleep 5
```

If GQL schema changes affect the federated supergraph (new types, fields, modules),
regenerate and restart the Hive Gateway — see `/halfstack` skill for details:

```bash
./scripts/generate-graphql-schema.sh
cp docs/manager/graphql-reference/supergraph.graphql ./supergraph.graphql
docker compose -f docker-compose.halfstack.current.yml restart backendai-half-apollo-router
```

## ./bai — V2 CLI

Shortcut for `./backend.ai v2`. Calls `/v2/` REST API endpoints.

### Setup (Webserver Session — Recommended)

The default testing flow uses webserver session auth, matching the production
environment where users access Backend.AI through the web console:

```bash
./bai config set endpoint http://127.0.0.1:8090
./bai config set endpoint-type session
./bai login
# User ID: admin@lablup.com
# Password: (admin password)
./bai config show
```

For non-interactive environments (CI, Claude Code), use environment variables:

```bash
BACKEND_USER=admin@lablup.com BACKEND_PASSWORD=changeme ./bai login
```

This stores a session cookie in `~/.backend.ai/session/cookie.dat`.

### Setup (Direct API — Alternative)

For direct manager API access without webserver (HMAC signature auth):

```bash
./bai config set endpoint http://127.0.0.1:8091
./bai config set endpoint-type api
./bai config set access-key AKIAIOSFODNN7EXAMPLE
./bai config set secret-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
./bai config show
```

Config is stored in `~/.backend.ai/config.toml` and `credentials.toml`.

### Command Pattern

```
./bai [admin] {entity} [{sub-entity}] {operation} [options]
```

- `admin` — superadmin-only operations
- Entity names are **singular** (domain, user, agent)
- Sub-entities are Click sub-groups (revision, channel, role)

### Common Commands

```bash
# Admin search with filters and ordering (superadmin only)
./bai admin domain search --limit 5 --name-contains default
./bai admin user search --status active --order-by created_at:desc
./bai admin agent search --limit 10
./bai admin image search --name-contains python
./bai admin session search --limit 5

# Get single entity (any authenticated user)
./bai domain get default
./bai user get <uuid>

# User-scoped search (any authenticated user)
./bai user search --scope-domain default --limit 5
./bai user search --scope-project <project-id> --limit 5

# Sub-entity operations
./bai admin deployment revision search
./bai rbac role search
./bai notification channel search
./bai scheduling-history session search --limit 10

# Filter options (domain-specific, explicit — no JSON)
./bai admin user search --username-contains admin --role superadmin
./bai admin agent search --status ALIVE --schedulable
./bai audit-log search --entity-type user --operation create
```

### --order-by Syntax

Multiple ordering supported via `field:direction`:

```bash
./bai admin user search --order-by created_at:desc --order-by username:asc
```

## Testing Workflow

### Prerequisites

Ensure webserver session is configured (recommended):

```bash
./bai config show   # Check endpoint-type is "session"
./bai login         # Login if session expired
```

### After Modifying Server Code

```bash
# 1. Restart affected service(s)
./dev restart mgr        # Handler, adapter, DTO changes
./dev restart web        # If GQL schema or webserver config changed
sleep 5                  # Wait for initialization

# 2. Verify with CLI (through webserver)
./bai admin domain search --limit 1
./bai admin user search --limit 1
./bai domain get default

# 3. For comprehensive validation
./bai admin agent search --limit 1
./bai admin image search --limit 1
./bai admin session search --limit 1
./bai resource-group search --limit 1
./bai audit-log search --limit 1
```

### Testing as a Regular User

Switch credentials to a non-admin user to verify permission boundaries.

Default user accounts and passwords are in `fixtures/manager/example-users.json`.
API keypairs (access_key, secret_key) are in the `keypairs` DB table.

```bash
# Direct API — switch to regular user keypair
./bai config set endpoint-type api
./bai config set access-key AKIANABBDUSEREXAMPLE
./bai config set secret-key <secret_key from keypairs table for user@lablup.com>

# Or session login as regular user
./bai config set endpoint-type session
BACKEND_USER=user@lablup.com BACKEND_PASSWORD=C8qnIo29 ./bai login
```

Regular user test scenarios:

```bash
# These should succeed (user-facing endpoints)
./bai domain get default
./bai user search --scope-domain default --limit 5

# These should fail with 403 (admin-only)
./bai admin domain search --limit 1   # expect: forbidden
./bai admin user search --limit 1     # expect: forbidden
```

Remember to switch back to admin credentials after testing.

## Smoke Test Script

Quick validation of all major endpoints:

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
