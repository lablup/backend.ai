---
name: runtime-variant-service-shapes
type: decision-table
description: runtime_variant knowledge - why every read and the create and update run against ops, why the two purges keep a service, why the bulk purge is custom-backed and partial
scope: src/ai/backend/manager/services/runtime_variant
keywords: [PurgeRuntimeVariantAction, BulkPurgeRuntimeVariantsAction, RuntimeVariantService, RuntimeVariantRepository, RuntimeVariantPresetsOfVariantPurger, partial_bulk, single_entity, RuntimeVariantEntityType]
sources:
  - src/ai/backend/manager/services/runtime_variant
  - src/ai/backend/manager/repositories/runtime_variant
generated:
  by: claude-code/opus-5
  at: 2026-09-18
status: draft
---

# Runtime variant service — Knowledge

> Rules: `../AGENTS.md`. Spec selection: `../../models/specs/KNOWLEDGE.md`.

A runtime variant is a system-wide catalog entry naming the serving runtime a deployment
revision runs on. The package exists for the two purges: everything else is a spec handed
to ops.

## The processor fields

`backend.ai mgr ops list` prints the wired list. Its output answers the entity type,
shape, operation, gate and backing.

## A variant is global and read by everyone

- A `runtime_variants` row belongs to no scope, so nothing is granted per row and only
  a superadmin passes the entity gate on update and purge.
- Every read — get, bulk get, search, lookup by name — is wired public: naming a runtime
  costs no permission.

## The purges keep a service

- A variant owns presets, and the row goes only after they do
  (`RuntimeVariantPresetsOfVariantPurger` then `RuntimeVariantPurger`).
- Two specs in one transaction is a multi-table write, which the generic ops purge
  does not do; the repository writes it and the service hands it the action's purger.

## The bulk purge is custom-backed and partial

- `bulk_purge` runs through `ProcessorGroup.partial_bulk` because its per-item function
  is the service purge above, not the generic ops purge.
- The shape is partial: the gate answers per id, a denied id or one matching no row is
  one failed item, and the run itself succeeds.
- Each variant is purged with its presets inside its own savepoint, so one failure
  leaves the others purged.
- The adapter reports the answer as it is: the purged ids and, per id that did not go,
  its reason.
