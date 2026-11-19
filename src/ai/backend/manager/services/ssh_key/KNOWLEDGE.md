---
name: ssh-key-service-shapes
type: decision-table
description: SSH key knowledge: why it is its own package, how upload and switch_default keep one default per user, why switch_default needs READ and UPDATE, the legacy SSH APIs still on the user service
scope: src/ai/backend/manager/services/ssh_key
keywords: [SSHKeyProcessors, SSHKeyService, SSHKeyRepository, UploadSSHKeyAction, SwitchDefaultSSHKeyAction, SSHKeyDefaultSetUpdater, uq_ssh_keypairs_is_default]
sources:
  - src/ai/backend/manager/services/ssh_key
  - src/ai/backend/manager/repositories/ssh_key
  - src/ai/backend/manager/models/ssh_keypair
  - src/ai/backend/manager/api/adapters/ssh_key
generated:
  by: claude-code/opus-5.5
  at: 2026-11-19
status: stable
---

# SSH key service: Knowledge

> Rules: `../AGENTS.md`. Spec selection: `../../models/specs/KNOWLEDGE.md`.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

This package handles the SSH public keys a user holds; a session reads the user's default key.
It is its own package so the SSH key operations stop living in the user and auth services.

## The processor fields

`backend.ai mgr ops list --field ssh_keypair` prints the wired list.

| Field | Backing | Authorized against |
|---|---|---|
| `upload` | `SSHKeyService.upload` | the user named in the action |
| `switch_default` | `SSHKeyService.switch_default` | the owning user, read by `LookupSSHKeypairOwnerAction` |
| `search` | ops (`atomic_bulk_scoped_search_ops`) | every user named |

## A user has at most one default

| Operation | Effect on the default |
|---|---|
| `upload` | The new key becomes the default only when the user has none |
| `switch_default` | Unmarks the previous default and marks the named key |

- Two writes racing on the default hit `uq_ssh_keypairs_is_default`, which the creator and the set updater map to `DefaultSSHKeyConflict`.

## switch_default needs READ and UPDATE on the owner

- `switch_default` names a key, so the processor first runs the owner lookup, which needs READ.
- The write that follows is an `UPDATE` on the owning user, so a caller with READ alone is rejected there.
- `upload` names the user directly and needs UPDATE alone.

## The legacy SSH APIs still run on the user and auth services

- REST v1 `/auth/ssh-keypair` and the admin `*SshKeypairV2` GQL fields still call `UserRepository.replace_default_ssh_key` and its siblings.
- They overwrite the default by purge and create, and identify the user by access key.
- They move here when those APIs are deprecated.
