---
name: app-config-definition-adapter-scenarios
type: reference
description: app config definition adapter authorization, search, batch loading, and purge contracts
scope: src/ai/backend/manager/api/adapters/app_config_definition
keywords: [app config definition, scenario, adapter, superadmin, cascade]
generated:
  by: codex/gpt-5
  at: 2026-09-14
status: draft
---
# app_config_definition adapter: current contract

An `app_config_definition` entity registers a usable `config_name` value. The actual config values are stored in `app_config_fragment` rows, and the per-scope allowance in `app_config_allow_list` entries.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

- A `definition` entity belongs to no domain, project or user scope automatically.
- Create and the unscoped search check whether the caller is superadmin.
- Get, batch get and purge check the permission on the target `definition` entity.
- The scopes that receive a default role own no `definition` today, so a regular user fails the single-entity permission check too.

Creating one `definition` creates the RBAC node itself. The accurate statement is therefore not that a `definition` entity is not an RBAC entity, but that it is not attached to a domain, project or user ownership relation today.

## Registration is open to superadmin only

A duplicate name is rejected by a database constraint violation. No contract converts it to a dedicated error yet. The request DTO rejects an empty name and a name longer than 128 characters, so the adapter scenarios do not cover them.

## Get checks the entity read permission

The permission check runs before the data read. A user without permission who requests a non-existent ID is therefore rejected for insufficient permission, not for a missing target.

## Batch get returns a result per input position

A failed permission check on one ID does not stop the whole batch. Whether `None` is returned for a non-existent ID or the request is rejected for insufficient permission depends on whether the permission check for that ID passed first.

## The unscoped search is open to superadmin only

Filter, sort and pagination are the common search contract, so a scenario of this adapter does not verify them.

## Purge deletes the `definition` row and the RBAC node

Deleting a `definition` row also deletes the `allow_list` entry and the `fragment` rows of the same name by foreign key cascade. The RBAC node of the `definition` itself is deleted during purge. There is no delete or restore call.

The current purge does not delete the RBAC nodes of the `allow_list` entry and `fragment` rows deleted by the database cascade. A remaining RBAC node is a limitation that needs a separate fix, not guaranteed behavior. Scenarios verify the adapter response and do not read the cascaded rows or the remaining RBAC node directly.

## Purging several

A bulk operation does not reject the whole call. Processed `definition` rows go into the processed list, and the failure list contains the ID and the reason of each failed item. Bulk purge deletes the `allow_list` entry and the `fragment` rows of each `definition` first and processes each `definition` inside its own savepoint.

## Names

Purge of one `definition` is `purge` and applies only the entity permission check. The old `admin_purge` GQL mutation is deprecated; it leads to the same call and keeps the superadmin check. The REST `DELETE /v2/app-config-definitions/{id}` keeps its path and was changed to the behavior of the new name.

The merged config read contract is in the [app_config adapter](../app_config/KNOWLEDGE.md).
