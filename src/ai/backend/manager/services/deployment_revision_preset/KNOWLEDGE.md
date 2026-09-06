---
name: deployment-preset-service-shapes
type: decision-table
description: deployment preset knowledge: why the slot rows are field rows of the preset, how the rank is assigned without a lock, why only the update keeps a service method, why the internal name stays DeploymentPreset while the API keeps the longer one
scope: src/ai/backend/manager/services/deployment_revision_preset
keywords: [DeploymentPresetCreator, PresetResourceSlotCreator, PresetResourceSlotID, search_ops, field_group, RANK_GAP, DeploymentPresetUpdater, create_global_entity_with_fields]
sources:
  - src/ai/backend/manager/services/deployment_revision_preset
  - src/ai/backend/manager/models/deployment_revision_preset
  - src/ai/backend/manager/repositories/deployment_revision_preset
generated:
  by: claude-code/opus-5
  at: 2026-08-18
status: stable
---

# Deployment preset service — Knowledge

> Rules: `../AGENTS.md`. Spec selection: `../../models/specs/KNOWLEDGE.md`.

A deployment preset is the template a deployment is created from. It states the
resource slot amounts along with it, so this package covers two tables.

## The processor fields

`backend.ai mgr ops list --concern deployment --entity deployment_preset` prints the
wired list. Its output
answers the entity type, shape, operation, gate and backing.

## The slot rows are field rows of the preset

- `preset_resource_slots` is owned by one preset and cascades from it, so it is a field
  row and carries its own `id` uuid for `PresetResourceSlotID`. The primary key stays
  `(preset_id, slot_name)`.
- It has `PresetResourceSlotData` of its own rather than the shared
  `ResourceSlotEntryData`: a field row's data answers with its owning entity, and the
  shared type is written for a deployment revision's slots too.
- `search_resource_slots` is handed the preset, so no owner lookup runs. It is answered
  for by a read of the preset and recorded against it.

## The rank is settled inside the INSERT, without a lock

- The creator puts a `max(rank) + RANK_GAP` subquery on `rank` in `build_row()`. The
  three statements that locked the parent row and read the MAX became one.
- Concurrent inserts can land on the same rank. Rank only orders a listing and presets
  are created rarely, so the tie is accepted. A deterministic order would need the lock
  back, and that means a spec declaring what to lock.
- `RANK_GAP` leaves room to place a preset between two existing ones later.

## Only the update keeps a service method

- Restating the slots clears the existing ones and writes the new set. Two tables in one
  transaction is more than one spec can carry.
- `slot_creators` of `None` leaves the slots alone; a sequence replaces the whole set,
  and an empty one clears them.
- Creation needs no service: `create_global_entity_with_fields` puts the preset and its
  slots in one transaction.

## Only the inside is named DeploymentPreset

- The table is `deployment_revision_presets`, and the GraphQL types and DTOs keep that
  name — changing them breaks schema compatibility and needs a migration.
- The inside (actions, specs, repository, service) shortens to `DeploymentPreset`, which
  is also what the entity type and `DeploymentPresetID` are named.
