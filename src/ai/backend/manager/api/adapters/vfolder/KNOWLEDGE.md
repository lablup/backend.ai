---
name: vfolder-adapter-scenarios
type: reference
description: what the vfolder adapter guarantees: ownership, which scopes can reach a vfolder, and how bulk operations report results
scope: src/ai/backend/manager/api/adapters/vfolder
keywords: [vfolder, scenario, adapter, rbac, ownership]
generated:
  by: claude-code/opus-5
  at: 2026-09-10
status: draft
---
# vfolder adapter: Knowledge

The rules are in `AGENTS.md` in the parent directory.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

A personal vfolder is created in the scope of the user who created it. The permission to create a vfolder therefore applies to that user. The storage host the vfolder is placed on must be allowed by both the domain and the keypair policy.

## Create

## Get

## Whose vfolder is reachable

A vfolder sits under a project. A personal vfolder sits in the personal project of that user, and a project vfolder in that project. Sharing is another scope borrowing the vfolder under a limit. Whether a vfolder is reachable is decided by whether a role on the scope that holds the vfolder allows vfolder read.

## Reading several vfolders at once

The call reads the vfolders another entity refers to, all at once, by an id list. The response has one entry per id, in input order, and the whole call is not rejected. Each entry is judged separately by the same rule as the single vfolder read.

For a user who is not superadmin, a missing id is also rejected for insufficient permission. The fact that the vfolder is missing is not revealed to a user without permission. Only superadmin sees the empty value.

## Update

Update changes the name, whether the vfolder can be cloned, and the default mount permission. The name must not collide within the scope that holds the vfolder.

## Updating, deleting and restoring several

A bulk operation does not reject the whole call. It judges each vfolder separately by the same rule as the single vfolder operation, so processed vfolders go into the processed list and failures are recorded in the failure list with the id and the reason. Delete and restore check the same permission. Bulk purge does not have this shape.
