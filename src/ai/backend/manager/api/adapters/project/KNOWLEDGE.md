---
name: project-adapter-scenarios
type: reference
description: what the project adapter guarantees; domain-scope authorization on create, the active flag mapped to soft delete and restore, partial bulk results, and image commit registries
scope: src/ai/backend/manager/api/adapters/project
keywords: [project, scenario, adapter, rbac, roster]
generated:
  by: claude-code/opus-5
  at: 2026-09-10
status: draft
---
# project adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

A project is created under a domain. Create requires the permission of that domain scope, not a global role. This differs from domain creation, so the pair is written separately.

## Create

## Member list

## Update

The active flag of update is deprecated. Deactivating it calls delete, activating it calls restore, and it is not called when the project is already in that state. The update applies the other fields. The status is not carried on the node, so scenarios read it through the active flag.

## Updating several

Updating several performs the same write as the single update for each project. It updates the project row and then rewrites the resource policy share the project follows.

The active flag calls delete and restore by the same rule as the single update per entry. A failure is added to the failure list for each entry.

## Deleting and restoring several

A bulk operation does not reject the whole call. Processed projects go into the processed list, and failures are recorded in the failure list with the id and the reason. There is no bulk purge.

## Container Registry read for image commit

A general project read does not include the Container Registry read for image commit. When the GraphQL request asks for that field, the adapter reads it in a separate bulk read.
