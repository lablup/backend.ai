---
name: vfolder-auto-mount-service-shapes
type: design-rationale
description: vfolder_auto_mount service knowledge - why only the create and the update have a service method, why one search is global and the other per scope, what each operation is authorized against, why the read by ids is partial
scope: src/ai/backend/manager/services/vfolder_auto_mount
keywords: [GlobalSearchVFolderAutoMountsAction, SearchVFolderAutoMountsAction, CreateVFolderAutoMountAction, UpdateVFolderAutoMountAction, BulkGetVFolderAutoMountsAction, VFolderAutoMountProcessors, VFolderAutoMountService, VFolderAutoMountCreator, global_searcher_ops, scoped_search_ops, partial_bulk_get_ops]
sources:
  - src/ai/backend/manager/services/vfolder_auto_mount
  - src/ai/backend/manager/models/vfolder_auto_mount
  - src/ai/backend/manager/repositories/vfolder_auto_mount/repository.py
generated:
  by: claude-code/opus-5.5
  at: 2026-11-25
status: draft
---

# Auto-mount vfolder service: Knowledge

> Rules: `../AGENTS.md`. Wiring: `backend.ai mgr ops list`.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

A `vfolder_auto_mount` row makes one vfolder an auto-mount vfolder of a project or a user.
This package holds the operations a caller reaches through the API.

## The processor fields

| Field | Failure mode | Authorized against |
|---|---|---|
| `bulk_get_ids` | partial bulk | each named row |
| `create` | one run | the project or the user the row is created in |
| `global_search` | one run | the `global` singleton, by entity type |
| `search` | one run | every named project, user and vfolder |
| `update` | one row | the named row |
| `delete` | one row | the named row |
| `restore` | one row | the named row |
| `purge` | one row | the named row |

## Only the create and the update have a service method

- The create's spec carries a precondition on the project the vfolder belongs to, which the
  generic create does not take. The service hands it to the domain repository.
- The create and the update reject a mount destination `verify_mount_destination` returns
  False for and a subpath leading outside the vfolder. A session runs the same checks on a
  requested mount.
- The other operations hand a spec to the generic ops services, so they have no
  `service.py` method.

## The admin search is global

- It reads the rows of every project and every user, so it names no scope to check.

## The scoped search is per scope

- The caller names projects, users and vfolders, and the rows of any of them are read.
- A user scope reads the rows set on the user, not those of the personal project.
- A vfolder scope reads the rows of that vfolder in every project and user they are set on.

## Both searches exclude the deleted rows by default

- The searcher reads the deleted rows too. The adapter adds the condition that excludes them,
  unless the top-level filter names `deleted_at`.

## The read by ids is partial

- It feeds the GQL DataLoader, where one batch mixes ids from several resolvers. A row the
  caller may not read fails alone.
