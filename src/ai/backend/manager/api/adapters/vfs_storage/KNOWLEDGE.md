---
name: vfs-storage-adapter-scenarios
type: reference
description: what the vfs storage adapter guarantees: the row lives in global alone, so update, purge and their partial bulk forms pass only for a superadmin
scope: src/ai/backend/manager/api/adapters/vfs_storage
keywords: [vfs storage, scenario, adapter, superadmin, purge, partial bulk update, partial bulk purge]
generated:
  by: claude-code/opus-5
  at: 2026-09-10
updated:
  by: claude-code/opus-5
  at: 2026-10-16
status: draft
---
# vfs_storage adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

A VFS storage row is created only in global. A call that updates or purges one or several rows checks the permission granted on that row. That permission comes from global only, so only superadmin passes.

## Update

## purge

The delete operation under the old name calls the same purge.

## Bulk update

## Bulk purge

A bulk operation does not reject the whole call. Processed VFS storage rows go into the processed list, and items that fail go into the failure list with the id and the reason.
