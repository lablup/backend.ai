---
name: container-registry-adapter-scenarios
type: reference
description: container registry adapter guarantees; superadmin-gated management calls, per-id batch load, missing scoped search, RBAC project relations, linking a project as its default, legacy is_global image visibility, URL validated by the request DTO and the Harbor project rule by a column constraint
scope: src/ai/backend/manager/api/adapters/container_registry
keywords: [container registry, scenario, adapter, superadmin, scoped_search, operation scope, RBAC, allowed groups, is_global, image visibility]
sources:
  - src/ai/backend/manager/api/adapters/container_registry/adapter.py
  - src/ai/backend/manager/services/container_registry/actions/base.py
  - src/ai/backend/manager/services/container_registry/processors.py
  - src/ai/backend/manager/models/container_registry/creators.py
  - src/ai/backend/manager/models/image/creators.py
  - src/ai/backend/manager/models/image/row.py
  - src/ai/backend/manager/repositories/ops/v2/relation/write.py
  - src/ai/backend/manager/api/adapters/image/adapter.py
  - src/ai/backend/manager/api/gql/image/resolver.py
  - tests/scenario/bai_scenario/manager/container_registry
generated:
  by: codex/gpt-5
  at: 2026-09-14
updated:
  by: claude-code/opus-5.5
  at: 2026-10-30
status: draft
---
# container_registry adapter: Knowledge

This package converts a `container_registry` API request into container registry processor and RBAC processor calls. The scenarios below collect the permission checks, return values and errors the adapter guarantees.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

## Most calls are open only to superadmin

- Each registry is created as an RBAC entity owned by no parent scope.
- Create, search, update and purge calls, except the allowed project change, the multi-ID get and the bulk purge, are handled as global actions and gate access on whether the caller is superadmin, not on a per-entity RBAC permission.
- Adding and removing an allowed project uses RBAC relation operations, so they check permission on both the registry and the project and are affected by the entity permission check setting.
- The multi-ID get and the bulk purge check the entity permission per ID and return the result per ID.

## A project relation is recorded in the permission graph but not used in search yet

- Adding an allowed project makes the project govern the registry with `READ` permission, and this permission applies to images the registry owns too.
- The registry search provides `admin_search` for superadmin only, and there is no operation scope that converts a project relation into a condition and no `scoped_search` yet.
- So even when the new RBAC graph holds a relation, a general user cannot enumerate accessible registries or images through the search calls of this adapter.

## The `is_global` image visibility policy remains in legacy reads

- Every registry is created without a parent owning scope, so the `is_global` value does not change the RBAC ownership; changing the value keeps the existing project relations.
- The legacy image permission builder includes the images of a registry with `is_global` without a project relation, and includes the images of a registry without `is_global` only for a project with an allowed relation.
- The new relation graph grants read permission on the registry and its images to projects linked explicitly, but does not grant permission to every project by the `is_global` value alone.
- The image adapter has no scoped search that applies this policy, so before the legacy builder is removed, decide the operation scope applied in common to the image visibility rule, the list and the single get of a registry with `is_global`.

## The image scoped search must move the legacy access conditions too

- The per-project image condition must select the images of a registry with `is_global` and the images of a registry without `is_global` that has a relation with the project, and must also apply the `allowed_docker_registries` of the caller's domain.
- A customized image must be exposed only to the user the `creator_id` column points to, as in the existing read, or be replaced by the new project ownership policy so that the list and the single get return the same result.
- Without backfilling the permission graph of existing registries and images, the new scoped search cannot find the access permission for the earlier data.

## Create handles the defaults and the allowed project relations together

- A request whose `url` value or name consists only of whitespace is rejected by the request type, so it is not in the adapter scenarios.
- Omitting the `ssl_verify` and `is_global` values makes both true.
- Create with allowed projects is also superadmin only, and the caller does not need to hold a permission on the new registry in advance.

## Only superadmin runs the search, and it filters by registry-specific fields

Filter combination (`AND`/`OR`/`NOT`), sort and cursor or offset pagination are the behavior of the search framework shared by every entity, so they are not in the scenarios of this adapter.

## Several IDs are returned per ID in request order

- The multi-ID get checks read permission per ID. An ID without permission is rejected for insufficient permission, and the design returns an empty value for a non-existent ID, distinguished from a rejection.
- The permission check runs before the existence check, so a user without permission is rejected for insufficient permission even for a non-existent ID. Whether the target exists is not revealed.
- The per-ID permission check does not pass superadmin first. Superadmin is also judged by the permission graph, so an ID whose node is missing is rejected for insufficient permission, not returned as an empty value. The permission check of the single get passes superadmin first, so the two checks differ in result, and which one to follow is not decided yet.

## The request read validates the `url` value, and the database validates the `project` value

- The request DTO validates the `url` value. It checks only that a host is present and does not restrict the scheme.
- A `url` value that does not start with `http` or `https` is parsed after `http://` is prepended. So `ftp://reg.example` and a string containing whitespace pass too, and only a `url` value with an empty host is rejected.
- Whether to tighten this validation is not decided yet.
- A `CHECK` constraint on the `container_registries` table validates the `project` value. A Harbor row must hold a `project` value in the format Harbor accepts, and other types ignore this value.
- The constraint reads the row after the write. Changing only one of the `type` and `project` values is rejected when the row to store violates the rule, and the database rejects it, not the request read.
- v1 GraphQL does not go through the request DTO yet, so a Python validator handles the same check (`services/container_registry/validator.py`).

## Changing the allowed projects checks permission on both the registry and the project scope

- A relation operation pairs the registry and the project and checks permission, and rejects the whole request when either one is not allowed.
- A general user is rejected by the permission check before the relation state is checked. So the scenario that adds a non-existent project and the scenario that removes a project that is not allowed run as superadmin.
- With the entity permission check disabled, a user without permission can also change the relation. The create operation directly checks whether the caller is superadmin, so the result differs.
- Adding a relation that already exists is idempotent. An error occurs only when none of the relations in the removal request is deleted.
- Add requires create permission on both scopes and remove requires delete permission on both scopes. No other kind of permission substitutes for them.
- A relation change scenario checks the row counts of the related tables as well as the call result, to verify creation, retention and deletion and to verify that a rejected request has no side effect.

## Create the relation between a project and a registry and set the registry as the default

This call creates a relation between a project and a registry that have none yet and sets that registry as the project's default registry (the image commit target). Legacy project creation calls it right after creating the project.

- It is the same relation creation as adding an allowed project. It therefore runs only when the caller holds create permission on both the registry and the project.
- Relation creation and the default designation are written at once. When relation creation is rejected, the default designation does not remain either.
- A project that already has a relation cannot gain a default through this call. This call writes the default together only when it creates a new relation. Changing an existing relation to the default is handled by the project's default registry switch.

## Purge removes the registry and the allowed project relations together

This adapter supports neither delete nor restore. A purge removes the registry row from the database. The old delete calls (GQL `admin_delete_container_registry_v2`, REST `POST /delete`) call the same purge.

## Bulk purge

- The bulk purge does not reject the whole call. Processed registries go into the processed list, and failures carry the ID and the reason in the failure list.
- The single purge checks whether the caller is superadmin, while the bulk purge checks the `HARD_DELETE` permission per registry. The GQL resolver and the REST handler handle the superadmin check.

## The calls that get the name and the registry's internal project name check the registry read permission
