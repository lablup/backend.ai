---
name: resource-preset-adapter-scenarios
type: reference
description: what the resource preset adapter guarantees for update and purge, single and partial bulk
scope: src/ai/backend/manager/api/adapters/resource_preset
keywords: [resource preset, scenario, adapter, rbac, update, purge, partial bulk]
generated:
  by: claude-code/opus-5
  at: 2026-10-15
status: draft
---
# resource_preset adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

A resource preset belongs to the public scope unless it is tied to a resource group. The permission graph checks update and purge. A user who received the preset update permission in the public scope can update without being superadmin.

## Update

## purge

## Bulk update

A bulk update does not change the resource group. The resource group changes who can see the preset, so only the single update changes the resource group.

## Bulk purge

A bulk operation does not reject the whole call because of entries it could not process. Processed presets go into the processed list, and failures are recorded in the failure list with the id and the reason.
