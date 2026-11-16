---
name: role-preset-adapter-scenarios
type: reference
description: what the role preset adapter guarantees for its writes; the permission graph guarding each write, bulk operations answering per id, and role permission presets added all-or-nothing and removed one by one
scope: src/ai/backend/manager/api/adapters/role_preset
keywords: [role preset, scenario, adapter, partial bulk, soft delete, restore, purge, permission entry]
generated:
  by: claude-code/opus-5
  at: 2026-10-15
status: draft
---
# role_preset adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

A role preset (preset below) is created in the global scope. The permission graph on the preset checks update, delete, restore, purge, and the addition and removal of permission entries. A user who received no role has no permission from the global scope and so is rejected. This document covers only the write operations. Create and read are not covered yet.

Framework contract tests check the common contract (target existence, bulk composition). This document records only the representative success and representative failure of each operation.

## Update

## Delete, restore and purge

## Bulk update

## Bulk delete, restore and purge

A bulk operation does not reject the whole call. Processed presets go into the processed list, and failures are recorded in the failure list with the id and the reason.

## Adding and removing role permission presets

Adding is all or nothing. Removing responds per entry.
