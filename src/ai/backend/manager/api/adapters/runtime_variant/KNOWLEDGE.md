---
name: runtime-variant-adapter-scenarios
type: reference
description: what the runtime variant adapter guarantees; the superadmin role on create, the entity gate nobody but a superadmin passes on update and purge, the reads answered in the public scope, the partial bulk update and purge that response per id
scope: src/ai/backend/manager/api/adapters/runtime_variant
keywords: [runtime variant, scenario, adapter, superadmin, public read, lookup, bulk delete, partial bulk update, partial bulk purge]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
updated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# runtime_variant adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

A `runtime_variant` row is created in both global and public. Create checks whether the calling user is superadmin, and a call that updates or deletes an entity by id checks the permission granted on that `runtime_variant` row. That permission comes from global only, so only superadmin passes, and the rejection reason differs between create and update or delete. The get by id, the name-to-id conversion, the get by multiple ids and the search check READ in public. Every account automatically receives the public membership role, so every signed-in user can read.

The presets under a `runtime_variant` have their own adapter, in `../runtime_variant_preset/KNOWLEDGE.md`.

## Create

The request cannot set the `default_model_definition` field and the `reads_vfolder_config_files` value. Create fixes the values and no call changes either of them. The value at creation is kept as it is, so the scenario "superadmin creates with only a name" checks both together.

A request whose name is empty or exceeds the length limit is not a scenario. The request type already rejects it, so the adapter does not guarantee it.

## Get

Get checks READ in public. The scenario where a user with only the public get permission succeeds proves it. The same user can get but cannot create. The matching rejection scenario is the one rejected for an insufficient role in the create section.

A non-existent id and an unreachable id are rejected for the same reason. The permission check runs first and a missing row has no granted permission either. The call that converts a name to an id is followed by a permission check on the converted target, so it rejects a non-existent name and an unreachable name for the same reason.

An unauthenticated call is not a scenario. A scenario always calls as a user prepared beforehand.

## Search

## Update

## Bulk update

The description accepts three (omitted, emptied, value given) and the name only two (omitted, value given). So the emptying scenario exists only for the description.

A non-existent id receives different rejection reasons for superadmin and other users. The permission check runs first and a missing row has no granted permission either, so only superadmin, who passes that check, is rejected for a missing target. The same applies to the scenario in the purge section.

A duplicate name is rejected with a different error on create and on update. Create rejects it with the error of this entity, and update propagates the constraint violation of the repository as it is. Before writing the scenario, settle on one.

## purge

The single purge and the bulk purge are `purge` and `partial_bulk_purge`. The old bulk delete (`bulk_delete`) calls the same processor and responds with the id list and the deletion count. The rows in the table that delete several are that path.

Bulk delete is a partial bulk purge that responds per id. The permission check is per id too, and a rejected id and a missing id enter the failure list while the call itself is not rejected. The deleted ids go into the deleted list in request order, and the deletion count is the length of that list. Each `runtime_variant` row is deleted inside its own savepoint together with its presets, so the rest remain deleted after one failure.

Delete deletes the presets under the `runtime_variant` first and then the `runtime_variant` row. The scenario that deletes a `runtime_variant` row carrying presets is commented out in `test_retiring.py`. Uncomment it when the preset seed is added together with the scenarios of `../runtime_variant_preset` and the `runtime_variant` column of a preset has the same foreign key in the ORM as in the migration (BA-7931).

This adapter has no delete that keeps the row. Deleting makes the row disappear and there is no call that restores it.
