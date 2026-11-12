---
name: prometheus-query-preset-category-adapter-scenarios
type: reference
description: what the prometheus query preset category adapter guarantees; the catalog reads open to every authenticated caller, the superadmin role on create, the entity gate on purge that no role reaches, the unique name, the purge that empties the category of the presets pointing at it
scope: src/ai/backend/manager/api/adapters/prometheus_query_preset_category
keywords: [prometheus query preset category, scenario, adapter, superadmin, public, unique name, purge]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
updated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# prometheus_query_preset_category adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

A category groups `prometheus_query_preset` (preset below). Like a preset, a row belongs to both global and public. The permission check differs per call. Get and search check READ in public, create checks whether the calling user is superadmin, and the permission that delete needs comes from global only. Every account automatically receives the public membership role, so every signed-in user can read every row.

There is no update call. Changing the name or the description requires deleting and creating again. So the update scenarios of the preset document, such as "omitting a value keeps it unchanged", do not exist here.

The presets that reference a category are in `../prometheus_query_preset/KNOWLEDGE.md`. This document covers only what happens to those presets when the category is deleted.

## Create

A duplicate name is rejected by the unique constraint of the repository and is not mapped to a domain error. The preset name has no unique constraint, so the two entities behave the opposite way.

A request whose name is only whitespace is not in the scenarios. The request type rejects it first, so the adapter does not guarantee it.

## Get

Get checks READ in public. The permission check runs first and no permission is granted on a missing row, so a non-existent id and an unreachable id are rejected for the same reason.

## Search

## Getting by several ids

This read returns one result per requested id. The adapter checks permission per id, so the entry for a missing id contains a rejection saying that the id cannot be read.

## Delete

Delete has no conflict check. A category is deleted even while a preset still references it, and that preset remains with `category_id` set to NULL. Whether to block the delete while a referencing preset exists is not decided. The scenario "delete the category a preset references" records the current behavior as it is.

A non-existent id is rejected for different reasons for superadmin and for other users. The permission check runs first and no permission is granted on a missing row, so the other user is rejected for insufficient permission and only superadmin, who passes that check, is rejected for a missing target.

This adapter has no delete that keeps the row. Deleting removes the row at once and there is no call that restores it. Delete is purge. The old GQL mutation and REST path are deprecated and lead to the same call.

## Deleting several

A bulk operation does not reject the whole call. Processed categories go into the processed list, and failures are recorded in the failure list with the id and the reason.
