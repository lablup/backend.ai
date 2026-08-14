---
name: storage-namespace-service-shapes
type: decision-table
description: storage namespace processor fields and their entity/operation/scope, why removal resolves a lookup before purging by id, the polymorphic storage_id and the missing foreign keys, what the association table points at
scope: src/ai/backend/manager/services/storage_namespace
keywords: [RegisterNamespaceAction, UnregisterNamespaceAction, ResolveStorageNamespaceAction, StorageNamespaceByStorageAndName, StorageNamespacePurger, lookup_ops, global_purge_ops, polymorphic, association_artifacts_storages]
sources:
  - src/ai/backend/manager/services/storage_namespace
  - src/ai/backend/manager/models/storage_namespace
  - src/ai/backend/manager/repositories/storage_namespace
  - src/ai/backend/manager/models/association_artifacts_storages/row.py
generated:
  by: claude-code/opus-5
  at: 2026-08-14
status: stable
---

# Storage namespace service — Knowledge

> Rules: `../AGENTS.md`. Family selection: `../../models/specs/KNOWLEDGE.md`.

A storage namespace is the bucket an object storage exposes or the subpath a VFS
storage exposes. The package exists because artifacts record where they were
stored by naming one of these rows, so the namespace needs an identity of its
own rather than living as a column on the storage.

## The processor fields

| Field | Action | Shape | Operation | Authorized against |
|---|---|---|---|---|
| `register` | `RegisterNamespaceAction` | global | CREATE | SUPERADMIN gate |
| `search` | `SearchStorageNamespacesAction` | global | SEARCH | SUPERADMIN gate |
| `get_namespaces` | `GetNamespacesAction` | global | SEARCH | SUPERADMIN gate |
| `lookup` | `ResolveStorageNamespaceAction` | lookup | — | authenticated caller |
| `unregister` | `UnregisterNamespaceAction` | global | PURGE | SUPERADMIN gate |

Every REST route in this domain declares `superadmin_required`, so the global
gate matches what the surface promises. The same holds for the object and VFS
storage packages this one hangs off: both of their surfaces, v1 included, are
super-admin operations, so no read in this family is open to a regular user.

## Removal takes an id, and the pair reaches it through the lookup

- Registration exposes `(storage_id, namespace)`, which is the table's unique
  constraint but not its primary key, and purge specs key on a single primary
  value.
- Rather than teach the purge a second addressing mode, the caller resolves the
  pair through `lookup` and passes the id — the lookup family already rejects a
  second match instead of answering with an arbitrary row.
- The translation lives in the adapter, so the API keeps naming a namespace the
  way it was registered.

## The owning storage is polymorphic and the schema does not say so

- `storage_id` points at either `object_storages` or `vfs_storages`, and the row
  carries no discriminator to say which.
- `artifact_revision/service.py` therefore reads the object storage first and
  falls back to the VFS storage on exception — failure used as a branch.
- The ORM models only half of it: `StorageNamespaceRow.object_storage_row` joins
  `ObjectStorageRow` alone, so a VFS-owned namespace resolves to nothing.

## Nothing in this chain has a foreign key

| Link | Constraint |
|---|---|
| `storage_namespace.storage_id` → either storage | none |
| `association_artifacts_storages.storage_namespace_id` → `storage_namespace.id` | none |
| `association_artifacts_storages.artifact_revision_id` → `artifact_revisions.id` | none |

- Removing a namespace an artifact still points at leaves the artifact naming a
  location that no longer exists; no `conflict_checks()` declares that either.
- The association is unique on `artifact_revision_id` and is only ever read from
  the revision side, so it is one-to-one and single-direction despite its shape.
