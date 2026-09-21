---
name: container-registry-service-gates
type: decision-table
description: container registries as global entities scanned for images, the per-project Harbor quota operations gated at the API layer instead of the processor, why the quota processors are wired anonymous, how a project resolves to the registry the quota client talks to, the registry conditions that reject a quota operation
scope: src/ai/backend/manager/services/container_registry
keywords: [ContainerRegistryProcessors, ContainerRegistryService, CreateRegistryQuotaAction, ReadRegistryQuotaAction, anonymous_global, superadmin_required, allowed_roles, get_project_registry, ContainerRegistryQuotaClientPool, HarborQuotaClient]
sources:
  - src/ai/backend/manager/services/container_registry
  - src/ai/backend/manager/api/rest/group/registry.py
  - src/ai/backend/manager/api/gql_legacy/container_registry.py
  - src/ai/backend/manager/api/gql_legacy/group.py
  - src/ai/backend/manager/repositories/container_registry/repository.py
  - src/ai/backend/manager/clients/container_registry
generated:
  by: claude-code/opus-5
  at: 2026-09-21
status: stable
---

# Container registry service — Knowledge

> Rules: `../AGENTS.md`. Action shapes and gates: `../../actions/KNOWLEDGE.md`.

A container registry is a global entity the manager scans images from. The service also
manages the storage quota Harbor keeps per project, reached through the project that names
the registry rather than through the registry itself.

## The quota operations are gated at the API layer, not by the processor

| Entry point | Gate | Who passes |
|---|---|---|
| REST v1 `/group/registry-quota` | `superadmin_required` middleware on the route | SUPERADMIN |
| Legacy GraphQL quota mutations | `allowed_roles` on the mutation class | SUPERADMIN, ADMIN |
| Legacy GraphQL `GroupNode.registry_quota` | none | anyone who resolves the node |

- The four quota processors are wired `anonymous_global`, so the processor runs the
  monitors and no validator; the catalog lists them with an anonymous gate.
- The `global` shape was not used because its SUPERADMIN gate would cut the ADMIN access
  the legacy GraphQL mutations grant.
- The `scope` shape over the project is the intended end state; it waits on the seed
  roles, which grant `container_registry: [read]` only, to grant the write operations.
- The webhook processor is the other anonymous wiring here: Harbor holds no keypair, and
  the service checks the webhook secret itself.

## A quota operation reaches the registry through the project

- `get_project_registry` reads `ProjectRow.container_registry` for a registry name and
  project, then the `ContainerRegistryRow` they name; any missing step is
  `ContainerRegistryNotFound`.
- The client pool picks a client by registry type; only `HARBOR2` has one, and any other
  type is `ContainerRegistryQuotaNotSupported`.
- A registry whose `project`, `username` or `password` is null is
  `ContainerRegistryQuotaNotConfigurable` before Harbor is called; `ssl_verify` null
  means verify.
- `HarborQuotaClient` opens a session per call, so the pool holds no connection state and
  needs no close.
