---
name: artifact-registry-service-composition
type: decision-table
description: why the HuggingFace and Reservoir registry writes keep service methods, and why their partial bulk runs are service-backed rather than ops-backed
scope: src/ai/backend/manager/services/artifact_registry
keywords:
  - ArtifactRegistryProcessors
  - ArtifactRegistryWriteOps
  - partial_bulk_update_huggingface_registries
  - partial_bulk_purge_reservoir_registries
sources:
  - src/ai/backend/manager/services/artifact_registry/processors.py
  - src/ai/backend/manager/repositories/ops/v2/artifact_registry/write.py
generated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---

# Artifact registry service — Knowledge

A registry is two rows: a per-kind row carrying the connection settings (huggingface,
reservoir) and an `artifact_registries` row carrying the name and kind. A write handles both
rows in one operation of `ArtifactRegistryWriteOps`.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

## Why the writes keep service methods

| Operation | Shape | Reason |
|---|---|---|
| update | `single_entity` + service | It edits both rows together. A generic ops update writes one row |
| purge | `single_entity` + service | It deletes both rows and the graph node together |
| bulk update | `partial_bulk` + service | Same reason. One savepoint per item |
| bulk purge | `partial_bulk` + service | Same reason. One savepoint per item |

- A bulk operation checks each registry's permission separately. A registry without
  permission and an absent id become failed items, and the rest are processed.
- The succeeded items of a bulk purge carry only the ids of the deleted registries. The
  names were in the rows deleted with them.
- The single purge action keeps the old name (`delete_*`) and uses the `PURGE` operation
  type. The old delete alias calls the same action.
