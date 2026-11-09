---
name: runtime-variant-preset-adapter-scenarios
type: reference
description: what the runtime variant preset adapter guarantees; the rank the insert fills in, the value-type rule checked by the request on create and by the service on update, the batch read that is a search, the partial bulk update and purge that answer per id, the variant column with no foreign key in the ORM
scope: src/ai/backend/manager/api/adapters/runtime_variant_preset
keywords: [runtime variant preset, scenario, adapter, superadmin, rank, value type, flag, public read, partial bulk update, partial bulk purge]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
updated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# runtime_variant_preset adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, review the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

A `runtime_variant_preset` entity references one `runtime_variant` by a column but is not created inside its scope. A row belongs to both global and public. Create checks whether the calling user is superadmin. The per-preset permission that update and delete need comes from global only, so only superadmin passes. Get and search check READ in public. Every account automatically receives the public membership role, so every signed-in user can read.

The scenarios of the `runtime_variant` adapter are in `../runtime_variant/KNOWLEDGE.md`.

## Create

The `rank` value cannot be set in the request. Create adds 100 to the largest `rank` value under the same `runtime_variant`, and the `rank` value of the first preset becomes 100. The scenario that creates one more preset under the same `runtime_variant` checks this gap.

The `ui_type` value has no separate field in the request and is read from the `ui_option` field. Specifying the `ui_option` field includes the `ui_type` value in the response, and if the `ui_option` field is omitted, as in the scenario that creates with only the required entries, the `ui_type` value is empty too.

The rule that a `value_type` value of `flag` requires the `preset_target` value to be `args` and the `default_value` value to match the `value_type` value is not in the create scenarios. The create request type decides both acceptance and rejection, and the unit tests of the request type check it per `value_type` value.

The scenario that creates with a non-existent `runtime_variant_id` value is not included yet. The `runtime_variant` column of a preset has a foreign key in the migration but not in the ORM. A database built by the migration therefore rejects the request, while a database whose schema was created in one step creates the row. Write the scenario after settling the correct behavior.

## Get

Get checks READ in public. The scenario in which get succeeds for a user with only the public get permission verifies it. A create request, on the other hand, is rejected for anyone who is not superadmin. A non-existent ID and an unreachable ID are rejected for the same reason.

The get of several IDs at once runs as a search with an ID condition. It is not a separate get per ID, so a non-existent ID does not reject the whole request and the response returns an empty entry at that position.

An unauthenticated call is not a scenario. A scenario always calls as a user prepared beforehand.

## Search

The `runtime_version` filter returns only the presets whose `added_version` value is at most the `runtime_version` value and whose `deprecated_version` value is above it. An empty `added_version` value has no lower bound, and an empty `deprecated_version` value has no upper bound. The scenario that searches with the `runtime_version` filter checks together the case with both the `added_version` and `deprecated_version` values, the case with only `added_version`, the case with only `deprecated_version` and the case with neither.

## Update

An update request may omit the `preset_target` or `value_type` value, so the request type alone cannot validate the combination with the stored value. The service combines the stored row and the request and checks the same rule, and that check is not a scenario. The adapter and the database do not change the result, and the service unit tests check it.

A request that changes only the `value_type` value does not validate the stored `default_value` value again. Today the preset is updated with the `default_value` value disagreeing with the new `value_type` value. Write the scenario after settling whether to reject it.

## Bulk update

A bulk update runs the same check as the single update per preset. A preset caught by the check enters the failure list with that reason and the rest are updated.

## Purge

A bulk operation does not reject the whole call. Processed presets go into the processed list, and failures are recorded in the failure list with the ID and the reason.

This adapter has no delete that keeps the row.
