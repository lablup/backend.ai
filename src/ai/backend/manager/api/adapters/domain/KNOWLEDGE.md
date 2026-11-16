---
name: domain-adapter-scenarios
type: reference
description: what the domain adapter guarantees about creation, reads, name lookup, updates, deletion, and search
scope: src/ai/backend/manager/api/adapters/domain
keywords: [domain, scenario, adapter, rbac, superadmin, lookup_name, scoped_search]
generated:
  by: claude-code/opus-5
  at: 2026-09-28
status: draft
---
# domain adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory. When this document and a run result disagree, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

A domain cannot be granted permission through the permission graph. It is created outside every scope and has no child entity under it. A global superadmin role protects create and the unscoped search, and the permission graph protects the calls that read and update one domain. The two reject for different reasons, so the pairs are written separately. A user granted a permission appears only in a read within a resource group scope.

Framework contract tests check the common contract (target existence, bulk composition, page). This document records the representative success and representative failure of each operation and the differences the domain rules make.

## Create

The scenario that disables enforcement stands on its own, to make explicit that a role protects this call rather than the permission graph, so the enforcement switch does not apply.

Create does not link a resource group. The allowed list call on the resource group side links it, and that scenario is in the resource group adapter document.

The legacy GQL `CreateDomainNode` and `ModifyDomainNode` call domain create or update and the resource group link separately. When the link fails, a domain with only the create or update applied remains.

## Read

A missing target and a lack of permission must be rejected as different things. If the two are merged into one, the caller cannot distinguish which one blocked it.

## Reading several

Reading several does not reject the whole call and responds per entry.

## Finding an id by name

Both calls check authentication only. The call that receives the id checks the permission. A user without permission therefore sees whether a name exists, and the design allows it. The REST handler and GQL resolver of another entity call this first when resolving a domain name to an id. GQL uses finding several by name as a name-to-id loader and joins it to reading several by id.

## Update

Update also does not add or remove a resource group. As in create, the allowed list call on the resource group side does the linking.

The active flag of update is deprecated. Deactivating it calls delete, activating it calls restore, and it is not called when the state is already that. The update applies the other fields. The status is not carried on the node, so scenarios read it through the active flag.

## Delete, restore and purge

Delete and restore do not look at the current state. The call responds that it was done even when the state is already that. Purge does not check whether the domain is deleted either. A domain with nothing attached is purged even when it is active.

Delete deactivates the active flag and changes the status to deleted. Restore reverts both.

A single update, delete and restore take an id. The old REST path and GQL mutation that take a name call find-an-id-by-name first and lead to the same call. The call that takes a name is that path. Purge takes a name.

## Updating several

Updating several calls delete and restore by the same rule as the single update, per entry. A failure enters the failure list per entry.

## Deleting and restoring several

A bulk operation does not reject the whole call. Processed domains go into the processed list, and failures carry the id and the reason in the failure list. There is no bulk purge.

## search

## search in a resource group scope

The GQL resolver that takes a resource group name calls find-an-id-by-name of the resource group adapter first and passes the obtained id as the scope. The domain adapter does not resolve a resource group name.
