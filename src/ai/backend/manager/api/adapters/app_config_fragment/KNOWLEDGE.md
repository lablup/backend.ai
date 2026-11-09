---
name: app-config-fragment-adapter-scenarios
type: reference
description: what the app config fragment adapter guarantees; one config name holds a fragment per scope (public, each domain, each user) that the app_config adapter merges by allow-list rank, and this adapter writes, reads, searches and purges those fragments one by one at their owner's scope, the public fragment written behind the superadmin role and read by anyone signed in, and the allow-list entry as the write gate
scope: src/ai/backend/manager/api/adapters/app_config_fragment
keywords: [app config fragment, scenario, adapter, upsert, scope, public, rbac]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
status: draft
---
# app_config_fragment adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

One `config_name` holds one `app_config_fragment` per scope. One public fragment, one per domain and one per user sit together under the same name, and the `app_config` adapter that reads config returns those fragment rows merged in the order of the `rank` value of the `app_config_allow_list` entry. This adapter writes, reads, searches and deletes each fragment before the merge. The owner is a domain or a user, and a fragment with no owner is the public fragment. The `scope_type` field is decided by the kind of owner and is not stored separately. Writing the same name again in one scope changes the fragment row of that scope.

An `allow_list` entry is the precondition of a write. A write needs an entry that allows the name for that `scope_type` value, and when the entry disappears the fragment row disappears with it. So a fragment row that is not allowed does not remain.

The permission check differs by whether an owner exists. A write with an owner and a read of one scope check the permission granted on that owner's scope. The public fragment has no corresponding scope, so a write checks whether the calling user is superadmin, and a read by scope checks authentication only. A call that gets and deletes one by id checks the permission graph, and a call that gets and deletes several ids returns a result per entry. The unscoped search checks whether the caller is superadmin.

A write needs both create permission and update permission. A write may create a new fragment row or change an existing one, so one of the two alone does not pass.

The response fields are id, `config_name`, `scope_type`, `scope_id`, `config` and time. The `scope_id` field of the public fragment is empty. A write fails entirely when any `fragment` fails. The writes are `scoped_atomic_bulk_upsert` and `my_atomic_bulk_upsert`, and the response holds only the written nodes. The old GQL mutation and REST path are deprecated and return the same write with a `failed` field that is always empty.

## Writing one's own fragment

The scenario where a disallowed name is in the request checks that a write fails entirely when any `fragment` fails. The allowance check runs per entry, but one rejection rolls back the rest, so the fragment of an allowed name does not remain either. Scenarios check the response only, so they do not state what does not remain.

An unregistered name and, when the `scope_type` value is `user`, a disallowed name are rejected for the same reason. There is one check, and it looks only for an `allow_list` entry that allows the name for that `scope_type` value.

An empty entry list and a request with an empty or too-long name are not scenarios. The validation of the request type already rejects them.

## Writing to a specified scope

The scenario where a user who is not superadmin writes a public fragment and the scenario that cannot write even with the permission check off have the opposite result to the section on writing one's own fragment. The public write is protected by the superadmin check, not by the permission graph, so it does not pass even with the scope permission.

Whether an owner exists is checked in the permission graph. The row is written first and rolled back when the graph has no owner, so no fragment row remains after the rejection. This rejection responds with a server error, not the current request error. Before writing the scenario, settle whether to change it to a rejection for a missing target.

A request with a `scope_type` value of `public` that sets a `scope_id` value and a request with a `scope_type` value of `domain` or `user` that omits the `scope_id` value are not scenarios. The validation of the request type already rejects them.

## Getting one's own fragment by name

This read targets one user scope only. It exists to read the config value the user wrote before updating it, not the merged `config` value, so there is a scenario where a domain fragment and the public fragment are not mixed in.

## Getting a fragment of a specified scope by name

The scenario where anyone reads the public fragment exists because the public fragment has no scope to protect. That `config` value is merged and visible even before sign-in, so the read checks authentication only and responds. The public fragment scenario in the get section requires the same result.

A non-existent domain is rejected for different reasons for superadmin and for other users. The permission check runs first and whether an owner exists is checked after it, so only superadmin, who passes that check, is rejected for a missing target. The scenario that names a non-existent owner in the next section is the same.

## Search in one scope

The adapter rejects a scenario that names two scopes. The request type accepts several scopes, but this search runs in one scope only, so the adapter rejects the rest instead of ignoring them silently. A request that names no scope is not a scenario because the validation of the request type rejects it.

## Unscoped search

The scenario where a user who is not superadmin searches also includes read permission in its situation, to check that the search in one scope and the unscoped search check permission differently.

Filter, sort and pagination are the common search contract, so a scenario of this adapter does not verify them.

## Get

The scenario that gets the public fragment by id fails in the current code and was taken out of the run (BA-7933). A read by scope has no scope that corresponds to the public fragment and passes with authentication only, but a read by id checks the permission granted on that fragment itself. The public fragment belongs to no scope, so no role grants a permission on it other than a role attached directly to that fragment, and every user who is not superadmin is rejected for insufficient permission. A public fragment must respond with authentication only, as in a read by scope, and the scenario records that expected result. Return it to the run when it is fixed.

## Getting by several ids

A missing id is also an entry rejected for a user who is not superadmin. The permission check runs per entry first, and a missing row has no granted permission, so only superadmin, who passes that check, receives an empty entry for the missing id.

## Delete

Delete does not check the `allow_list` entry. A fragment row exists only while the `allow_list` entry exists, so an existing fragment row can always be deleted in its own scope.

The merge read document covers how, after a fragment is deleted, that `config` value drops out of the merge result and the `config` value of the scope with the next `rank` value appears instead. That document builds without the fragment from the start, so this document does not check the merge again after a delete.

This adapter has no delete that keeps the row. Deleting makes the row disappear, and there is no call that restores it.

## Deleting several

Without permission the whole request is not rejected; only that entry enters the `failed` list, and another user's fragment remains. A missing id and an id that cannot be deleted enter the same `failed` list, so the scenario mixes one's own fragment, another user's fragment and a missing id in one request and checks the order. The failure reason is returned as a string and a string may change, so the scenario does not check it.

An empty list is not a scenario. The validation of the request type already rejects it.

Deleting several is `partial_bulk_purge` and returns the deleted nodes. The old REST `POST /bulk-delete` is deprecated and returns the ids of the same delete only.
