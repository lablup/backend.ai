---
name: client-ip-masking-adapter-scenarios
type: reference
description: what the client IP masking adapter guarantees: one policy per target set by an upsert that replaces the whole row, the superadmin role on upsert and search against the entity gate on purge, single and partial bulk, no single read
scope: src/ai/backend/manager/api/adapters/client_ip_masking
keywords: [client ip masking, scenario, adapter, superadmin, monitor, upsert, target, purge]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
updated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# client_ip_masking adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt this document first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

The adapter provides four calls: `upsert`, `admin_search`, `purge` and `partial_bulk_purge`. There is no call that gets one by `id`.

One policy row exists per `target_type` (the unique constraint on `client_ip_masking_policies`). `target_type` is one of `default` (the default value inherited by the other `target_type` values), `login_history` and `audit_logs`, and `mode` is one of `none`, `truncate` and `drop`. `ipv4_prefix` and `ipv6_prefix` decide how many leading bits of the address the `truncate` mode keeps (the `/24` and `/48` of CIDR) and may be omitted in the request.

The check each call must pass differs.

| Call | Check | Callers that pass | Rejection |
|---|---|---|---|
| `upsert` | whether the caller is superadmin | superadmin | `InsufficientPrivilege` |
| `admin_search` | whether the caller is superadmin | superadmin, monitor | `InsufficientPrivilege` |
| `purge` | the entity permission on that policy | superadmin | `NotEnoughPermission` |
| `partial_bulk_purge` | the entity permission per policy | superadmin | the reason for insufficient permission in the failure list per policy |

A policy belongs to no scope, so there is no way to be granted the entity permission that `purge` checks. Only superadmin passes `purge` as a result.

## Upsert (`upsert`)

An upsert replaces the whole row with the values sent, without merging into the existing row. An `ipv4_prefix` or `ipv6_prefix` omitted in the request therefore becomes null even when a value is stored. The behavior looks like a partial update and is easy to misread, so the scenario "upsert again without a prefix for a policy that has one stored" stands on its own.

A null `ipv4_prefix` or `ipv6_prefix` means the policy row stores no value. `ClientIPMasker`, which applies the masking, fills the default values it uses to cut the address (24 and 48), and the adapter response carries the null as it is.

A request whose `ipv4_prefix` falls outside 0 to 32 or whose `ipv6_prefix` falls outside 0 to 128 is not a scenario. The validation of the request DTO rejects it before the adapter is called. Whether each `target_type` and `mode` value is stored is not a scenario either. That is the list of values the column type accepts, not something the adapter guarantees, and it belongs to the unit tests.

## Search (`admin_search`)

What the `target_type` and `mode` filters narrow is not a scenario. Moving a filter into a condition and selecting rows by that condition belong to the unit tests. There are only three `target_type` values (`default`, `login_history` and `audit_logs`), so policy rows cannot exceed three, and a scenario that creates more rows than the page size to check the next page cannot exist either.

The monitor role passes the superadmin check for read calls only. "a monitor role user searches all rows" (passes) and "a monitor role user upserts" (rejected) show the difference.

## Purge (`purge`)

Among `upsert`, `admin_search` and `purge`, only `purge` takes an `id`. The upsert finds the row by `target_type` and the purge by `id`, so the id to purge must be read from the upsert response or a search result. There is no call that gets one, so a search is the only way to check that row again even with the id known.

A non-existent `id` is rejected for a different reason per caller. The permission check runs before the row read, and a missing row has no granted permission, so a regular user receives `NotEnoughPermission`. Only superadmin, who passes the permission check, receives `EntityNotFoundError`.

There is no delete that keeps the row.

## Purging several (`partial_bulk_purge`)

A bulk operation does not reject the whole call. Processed policies go into the processed list, and failures carry the `id` and the reason in the failure list.
