---
name: retention-policy-adapter-scenarios
type: reference
description: what the retention policy adapter guarantees; the one policy a category holds, the read that needs the entity gate unlike the other catalogs, the purge that the deprecated delete also calls, the partial bulk update and purge, the monitor role passing the search
scope: src/ai/backend/manager/api/adapters/retention_policy
keywords: [retention policy, scenario, adapter, superadmin, monitor, category, purge, partial bulk]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
status: draft
---
# retention_policy adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

There is one `retention_policy` policy per category, and it is created outside every scope. Create and search check whether the calling user is superadmin, and the get, update and purge by id check the permission granted on that policy, but there is no way to receive it. Create and search, and get, update and purge, all pass only for superadmin, but the rejection reason differs.

Unlike the other global catalogs, the get of one by id goes through a permission check too. If the get scenario of a catalog that checks authentication only is copied, a user without any permission is rejected for insufficient permission instead of passing.

## Create

The request cannot decide the `last_swept_at` value. It is empty on create and the cleanup loop fills it later, and no call of this adapter updates it.

A request with a retention period shorter than a day is not a scenario. The request type already rejects it.

"a monitor role user creates" is paired with "a monitor role user searches" in the search section. The same user can search and cannot create.

## Get

A non-existent id is rejected for different reasons for superadmin and for other users. The permission check runs first and a missing row has no granted permission either, so only superadmin, who passes that check, is rejected for a missing target. The missing id scenarios in the sections below are all the same.

## Search

There are only the eight categories listed in the create section, so policies cannot exceed eight either. A scenario that creates more than 10 rows to check the next page cannot exist, so there is none.

A monitor role passes the superadmin check for reads only. The pair that shows the difference in this entity is "a monitor role user searches" and "a monitor role user creates".

## Update

A duplicate category is rejected with a different error on create and on update. Create rejects it with the error of this entity, and update propagates the constraint violation of the repository as it is. Before writing the scenario, decide whether to unify them into one.

## Purge

No delete leaves a row. The deprecated delete GQL mutation and SDK method call purge.

## Bulk update

## Bulk purge

A bulk operation does not reject the whole call. Processed policies go into the processed list, and failures are recorded in the failure list with the id and the reason.
