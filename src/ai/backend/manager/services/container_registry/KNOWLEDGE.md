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

> Rules: `../AGENTS.md`. Action shapes and the gate: `../../actions/KNOWLEDGE.md`.

A container registry is a global entity the Manager scans for images. This service also
handles the storage quota Harbor keeps per project. A quota operation does not take the
registry directly; it takes the project that references the registry and finds the registry
from it.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

## A quota operation's permission is gated at the API layer, not in the processor

| Entry point | Gate | Roles that pass |
|---|---|---|
| REST v1 `/group/registry-quota` | the route's `superadmin_required` middleware | SUPERADMIN |
| legacy GraphQL quota mutation | the mutation class's `allowed_roles` | SUPERADMIN, ADMIN |
| legacy GraphQL `GroupNode.registry_quota` | none | anyone who can read the node |

- The four quota processors are wired as `anonymous_global`. Only the monitor is attached,
  with no validator, and the catalog records them under the anonymous gate.
- The reason for not using the `global` shape is that its SUPERADMIN gate cuts out the ADMIN
  that the legacy GraphQL mutation allows.
- The target is the `scope` shape with the project as the scope. The seed role still grants
  only `container_registry: [read]`, so it moves after the write permission is added to the role.
- The webhook processor uses the same anonymous wiring. Harbor has no keypair, so the service
  checks the webhook secret itself.

## A quota operation reaches the registry through the project

- `get_project_registry` reads the registry name and project name from the project's
  `container_registry` setting and finds the registry those two reference. If any of the
  project, the setting or the registry is missing, it is `ContainerRegistryNotFound`.
- The client pool picks a client by registry type. The only implementation is `HARBOR2`, so
  any other type is `ContainerRegistryQuotaNotSupported`.
- A registry whose `project`, `username` or `password` is null is rejected with
  `ContainerRegistryQuotaNotConfigurable` before Harbor is called. A null `ssl_verify` is not
  rejected and is read as `True` (TLS verification), the same as the column's `server_default`.
- `HarborQuotaClient` opens a session per call, so the pool keeps no connection state and needs
  no close.

## The name and inner-project lookup checks read permission on the found registry

- `lookup_by_name_and_registry_project` resolves the name and the registry's inner project name
  through the existing lookup and returns the registry ID.
- It performs the lookup after authentication and checks read permission on the found registry.
  For an ordinary user it returns non-existence and lack of permission as the same error.
- When several registries match the same key, the shared lookup rejects it and does not pick an
  arbitrary row.
