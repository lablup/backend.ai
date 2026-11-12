---
name: rbac-adapter-scenarios
type: reference
description: what the rbac adapter guarantees for role writes: permission checks by the scope's permission graph, deprecated status handling, and partial bulk results
scope: src/ai/backend/manager/api/adapters/rbac
keywords: [rbac, role, scenario, adapter, restore, partial_bulk, status]
generated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# rbac adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

This document covers role writes only for now. A role belongs to one scope, and the permission graph of that scope checks the calls that update a role. The target role is placed in a domain the caller does not belong to. A call made by a user who is not superadmin runs as a user without any permission.

## Update

The deprecated `status` is handled after the update. The adapter sends DELETED to delete the role and ACTIVE to a deleted role to restore it. When the role is already in that state, the adapter does nothing and does not apply INACTIVE.

## Delete, restore, purge

## Bulk update

The deprecated `status` is handled per role by the same rule as the single update. A role that fails in delete or restore goes into the failure list with that reason.

## Bulk delete, restore, purge

A bulk operation does not reject the whole call. Processed roles go into the processed list, and failed items go into the failure list with the id and the reason.
