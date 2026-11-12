---
name: app-config-allow-list-adapter-scenarios
type: reference
description: app config allow-list adapter authorization, rank, search, batch loading, and purge contracts
scope: src/ai/backend/manager/api/adapters/app_config_allow_list
keywords: [app config allow list, scenario, adapter, rank, superadmin, cascade]
generated:
  by: codex/gpt-5
  at: 2026-09-14
status: draft
---
# app_config_allow_list adapter: current contract

An `app_config_allow_list` entry makes a registered `config_name` value usable in the scopes of a given `scope_type` value. The `rank` value of each `allow_list` entry settles the precedence applied when merging `app_config_fragment` rows from several scopes.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

- An `allow_list` entry is not attached to a domain, project or user scope automatically.
- Create and the unscoped search apply a superadmin check.
- Get, batch get, update and purge apply the permission check on the `allow_list` entity.
- No ownership relation exists today between the scopes that receive a default role and an `allow_list` entry, so a regular user fails the single-entity permission check too.

Creating an `allow_list` entry creates the RBAC node itself. The entry is an RBAC entity but is not attached to a domain, project or user ownership relation today.

The `rank` column is on the `allow_list` row, not on the `fragment` row. A user who may write a `fragment` row cannot change the `rank` value of that row. The [app_config adapter](../app_config/KNOWLEDGE.md) covers the actual merge contract.

## Only superadmin can create

Omitting `rank` uses the default for that `scope_type` value. The gap of 100 lets superadmin place another `rank` value between the existing defaults.

An unregistered `config_name` value is converted to a dedicated error and rejected. A duplicate `allow_list` entry is not yet converted to a dedicated error and is rejected by a database constraint violation.

## Get checks the entity read permission

The permission check runs before the data read. A user without permission who requests a non-existent ID is therefore rejected for insufficient permission, not for a missing target.

## Batch get returns a result per input position

A failed permission check on one ID does not stop the whole batch. Whether a non-existent ID returns `None` or is rejected for insufficient permission depends on whether the permission check for that ID passed first.

## Only superadmin can run the unscoped search

Entries pre-stored in one request have the same creation time. The default order is creation time descending, ties broken by ID ascending, so the page after the cursor neither repeats nor skips an entry.

Filter and sort are the common search contract and are not verified by a scenario of this adapter.

## `rank` is the only updatable field

The `config_name` and `scope_type` fields are absent from the update request DTO. To change these two fields, delete the existing `allow_list` entry and create a new one.

## Updating several

## Purge removes the `allow_list` row and the RBAC node

Deleting an `allow_list` row also deletes the `fragment` rows that reference it, by foreign key cascade. The RBAC node of the entry itself is deleted during purge. There is no delete or restore call.

The current purge does not delete the RBAC node of a `fragment` row deleted by the database cascade. The remaining node is a limitation that needs a separate fix, not guaranteed behavior. Scenarios verify the adapter response and do not read the cascaded rows or the remaining RBAC node directly.

## Purging several

A bulk operation does not reject the whole call. Processed entries go into the processed list, and the failure list contains the ID and the reason. Bulk purge deletes the `fragment` row of each entry first and processes each entry inside its own savepoint.

## Names

Update and purge of one entry are `update` and `purge` and apply only the entity permission check. The old `admin_update` and `admin_purge` GQL mutations and the update and purge of the REST singular path (`/v2/app-config-allow-list`) are deprecated; they lead to the same call and keep the superadmin check. The new write paths sit under `/v2/app-config-allow-lists`.
