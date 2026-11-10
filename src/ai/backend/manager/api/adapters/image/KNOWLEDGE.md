---
name: image-adapter-scenarios
type: reference
description: "what the image adapter guarantees: its superadmin and image permission checks, the custom-image creator check on purge, partial bulk writes, and single-tag scan"
scope: src/ai/backend/manager/api/adapters/image
keywords: [image, scenario, adapter, superadmin, permission, customized image, alias, scan]
generated:
  by: claude-code/opus-5
  at: 2026-09-11
status: draft
---
# The image adapter converts image requests and responses

The rules are in `AGENTS.md` in the parent directory. When this document and a run result differ, doubt the sentence first.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

Four checks block calls: the superadmin check, the image permission check, the container registry permission check and the custom image creator check.

| Check | Calls it applies to | What it checks |
|---|---|---|
| superadmin check | search, alias | whether the caller is superadmin |
| image permission check | update, delete, restore, purge, several ID get (per ID), bulk update/delete/restore (per ID), alias search of one image | whether the caller has permission on that image |
| container registry permission check | image search with one container registry as the scope | whether the caller has permission on that container registry |
| custom image creator check | purge | whether the image is a custom image and the caller created it |

On purge, the image permission check and the custom image creator check run in order. Passing the image permission check still requires the custom image creator check.

An `image` entity belongs to a container registry. A custom image made by session commit also belongs to the personal project of the user who committed, so the image permission received in that personal project applies to that image. The scenarios of the container registry itself are in `../container_registry/KNOWLEDGE.md`.

## Search

The request type accepts size, offset and a cursor, but one request uses one method only. Specifying both is rejected as invalid input. With size and cursor omitted, the adapter reads 50 images by offset.

A cursor search exists separately for image search and alias search.

There are two alias searches. The superadmin check blocks the alias search across all images, and the permission check on that image blocks the alias search of one image. The rejection reason differs even for the same regular user.

A rejection for specifying size and cursor together or for a bad cursor value does not come from the request type. It comes from the adapter choosing the paging method. It is behavior the adapter guarantees, so it stays as a scenario.

There are two image searches too. The superadmin check blocks the unscoped search, and the permission check on that container registry blocks the search with one container registry as the scope.

## Getting by several IDs

Getting by several IDs passes the image permission check per ID, not per request. A rejected ID position returns the exception object, and the other ID positions return the read result as it is.

## Delete and restore

Delete does not remove the row. It changes only the status to the `DELETED` value, so the image can be restored. Removing the row itself is the purge below.

Delete and restore pass the image permission check only. A user with the granted permission can delete even a non-custom image.

Delete applies to an image in the `ALIVE` status. Restore applies to both an image in the `DELETED` status and one in the `ALIVE` status, and restoring an image in the `ALIVE` status changes nothing. Any other status is rejected for a missing target.

Update, delete and restore take an id. The old REST path that carries the id in the body leads to the same call.

## Bulk delete and restore

A bulk operation does not reject the whole call. Processed images go into the processed list, and the failure list contains the id and the reason. There is no bulk purge.

## Purge

Do not merge the rejection of the image permission check (insufficient permission) and the rejection of the custom image creator check (access denied). If the rejections are merged, the caller cannot distinguish whether getting more permission would resolve the situation.

A non-custom image cannot pass the creator check. Only superadmin skips this check and purges. This does not mean an RBAC ownership relation between the image and the container registry.

## Registering and removing aliases

An alias is a value that belongs to an image. Registration and removal are protected by the superadmin check, not by the image permission. The image permission check blocks delete and the superadmin check blocks alias registration, so the rejection reason differs even for the same image. "a custom image creator registers an alias on their own image" checks the difference. Even a custom image creator cannot register an alias on their own image.

## Update

Only the `supported_accelerators` field distinguishes omission, emptying and specifying a value. The other fields accept only omission and specifying a value, so the scenario that empties a field exists only for the `supported_accelerators` field.

## Bulk update

## Single-tag scan

A tag scan registers and updates every architecture as the existing scanner does, and restricts the response to the requested architecture. When the requested architecture is absent, the call is rejected for a missing image.
