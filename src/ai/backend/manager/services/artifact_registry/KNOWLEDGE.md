---
name: artifact-registry-service-composition
type: decision-table
description: why the HuggingFace and Reservoir registry writes keep service methods, why their partial bulk runs are service-backed rather than ops-backed, and why their reads return the stored credential only to a superadmin
scope: src/ai/backend/manager/services/artifact_registry
keywords:
  - ArtifactRegistryProcessors
  - ArtifactRegistryWriteOps
  - partial_bulk_update_huggingface_registries
  - partial_bulk_purge_reservoir_registries
  - bulk_get_reservoir_registries
  - secret key
  - token
sources:
  - src/ai/backend/manager/services/artifact_registry/processors.py
  - src/ai/backend/manager/repositories/ops/v2/artifact_registry/write.py
generated:
  by: claude-code/opus-5
  at: 2026-10-16
updated:
  by: claude-code/opus-5
  at: 2026-11-09
status: draft
---

# Artifact registry service: Knowledge

A registry is two rows: a per-kind row holding the connection settings (huggingface,
reservoir) and an `artifact_registries` row holding the name and kind. A write handles both
rows in one operation of `ArtifactRegistryWriteOps`.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

## Why the writes keep service methods

| Operation | Shape | Reason |
|---|---|---|
| update | `single_entity` + service | It updates both rows together. A generic ops update writes one row |
| purge | `single_entity` + service | It deletes both rows and the graph node together |
| bulk update | `partial_bulk` + service | Same reason. One savepoint per item |
| bulk purge | `partial_bulk` + service | Same reason. One savepoint per item |

- A bulk operation checks each registry's permission separately. A registry without
  permission and an absent id become failed items, and the rest are processed.
- The succeeded items of a bulk purge hold only the ids of the deleted registries. The
  names were in the rows deleted with them.
- The single purge action keeps the old name (`delete_*`) and uses the `PURGE` operation
  type. The old delete alias calls the same action.

## Credentials in results

Every result that carries a registry holds the stored Reservoir `secret_key` and HuggingFace
`token` only when the caller is a superadmin. Any other caller gets `*****` in their place, and a
HuggingFace registry without a token keeps null.

| Operation | Shape | Reason |
|---|---|---|
| bulk get | `partial_bulk` + service | The result is masked for the caller. A generic ops read takes no step after the read |

- The artifact import reads the credentials from `ReservoirRegistryRepository` and
  `HuggingFaceRepository` directly, not through these actions, so it gets the stored values.
