# Entity-Command Quick Reference

Syntax: `./bai [admin|my] {entity} [{sub-entity}] {command} [options]`

**This is a guide, not a source of truth.** Always verify with `--help`:
```bash
./bai {entity} --help
./bai admin {entity} --help
./bai my {entity} --help
```

## Core

- **domain**: user(get) | admin(search, create, update, delete)
- **user**: user(get, create, update, delete, search) | admin(create, delete)
- **project**: user(get) | admin(search, create, update, delete)
- **agent**: admin(search, create, delete)
- **image**: admin(search, create, delete)
- **session**: user(enqueue, get, project-search, terminate, start-service, shutdown-service, logs, update) | admin(search) | my(search)
  - admin sub: kernel(search, inspect, restart)

## Compute & Serving

- **deployment**: user(project-search, get, create, update, delete) | admin(search) | my(search)
  - admin sub: revision(search, add, get, current, activate), replica(search, scale-up, scale-down)
- **model-card**: user(project-search, get, deploy, available-presets) | admin(search, create, update, delete)
- **service-catalog**: admin(search, create, update, delete)
- **runtime-variant**: user(search, get) | admin(search, create, update, delete)
- **runtime-variant-preset**: user(search, get) | admin(search, create, update, delete)
- **scheduling-history**: sub: session(search, search-scoped), deployment(search, search-scoped), route(search, search-scoped)

## Storage

- **vfolder**: user(my-search, project-search, admin-search, create, get, upload, download, delete, purge, ls, mkdir, mv, rm, clone, bulk-delete, bulk-purge)
- **vfs-storage**: user(create, list-all, get, update, search, delete)
- **storage-namespace**: user(register, unregister, search, get-by-storage)
- **object-storage**: user(create, get, update, search, delete)

## Registries & Artifacts

- **container-registry**: admin(search, create, update, delete)
- **artifact**: user(get, update, delete, restore) | admin(search, purge)
  - user sub: revision(get, approve, reject, cancel-import, cleanup)
- **artifact-registry**: user(get) | admin(search, create, update, delete)
- **huggingface-registry**: user(create, search, get, update, delete) | admin(search)
- **reservoir-registry**: user(create, search, get, update, delete) | admin(search)

## Access Control & Auth

- **rbac**: sub: role(search, get, create, delete), permission(search), assignment(search, assign, revoke), entity(search)
- **keypair**: admin(search, get, create, update, delete) | my(search, create, issue, delete)
- **login-history**: admin(search) | my(search)
- **login-session**: admin(search, delete) | my(search, delete)

## Resource Management

- **resource-group**: user(search, get, create, delete, resource-info, allowed-for-domain, allow-for-domain, allowed-for-project, allow-for-project, allowed-domains, allow-domains, allowed-projects, allow-projects) | admin(search, create, update, delete)
- **resource-allocation**: user(project-usage, resource-group-usage) | admin(search, create, update, delete) | my(search)
- **resource-preset**: admin(search, get, create, update, delete)
- **resource-policy**: admin(search, get, create, update, delete) | my(search)
- **resource-slot**: sub: slot-type(search), agent-resource(search), allocation(search)
- **resource-usage**: sub: domain(search), project(search), user(search)

## Monitoring & Audit

- **audit-log**: user(search) | admin(search)
- **scheduling-history**: sub: session(search, search-scoped), deployment(search, search-scoped), route(search, search-scoped)
- **fair-share**: sub: domain(search, get), project(search, get), user(search, get)
- **notification**: sub: channel(search, get, delete), rule(search, get, delete)
- **prometheus-query-definition**: user(search, get, create, update, execute, delete) | admin(search, create, update, delete)
- **app-config**: user(get-domain, delete-domain, get-user, delete-user, get-merged) | admin(create, update, delete)
- **export**: admin(list, request, purge) | my(list, request, purge)
