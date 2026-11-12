---
name: object-storage-adapter-scenarios
type: reference
description: what the object storage adapter guarantees; update, purge and their partial bulk forms, which only a superadmin passes because the row lives in global alone, and the secret key a read gives only to a superadmin
scope: src/ai/backend/manager/api/adapters/object_storage
keywords: [object storage, scenario, adapter, superadmin, purge, partial bulk update, partial bulk purge, secret key]
generated:
  by: claude-code/opus-5
  at: 2026-09-10
updated:
  by: claude-code/fable-5
  at: 2026-11-04
status: draft
---
# object_storage adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

An object storage row is created in global alone. A call that updates or purges one or several by id checks the permission granted on that row. That permission comes from global only, so only superadmin passes.

## Read

Every node the adapter returns, from a get, a search or the DataLoader, carries the stored `secret_key` only when the caller is a superadmin. Any other caller, a monitor reading the global list included, gets `*****` in its place. The field keeps its type, so the schema does not change.

## Update

## purge

The delete under the old name calls the same purge.

## Bulk update

## Bulk purge

A bulk operation does not reject the whole call. Processed object storage rows go into the processed list, and failures carry the id and the reason in the failure list.
