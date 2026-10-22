---
name: user-service-composition
type: decision-table
description: why a user's operations take the shapes they do, why a keypair is a field row of the user, why the email-addressed operations are gone
scope: src/ai/backend/manager/services/user
keywords:
  - UserProcessors
  - keypair_group
  - LookupKeypairOwnerByAccessKeyAction
  - DotfileRow
  - bootstrap_script
sources:
  - src/ai/backend/manager/services/user/processors.py
  - src/ai/backend/manager/models/keypair
  - src/ai/backend/manager/models/user
  - src/ai/backend/manager/models/bootstrap_script
  - src/ai/backend/manager/models/bootstrap_script_revision
generated:
  by: claude-code/opus-5
  at: 2026-08-19
status: draft
---

# User service

A user sits under a domain, so creation is scope-shaped with the domain as the scope,
and an operation naming an existing user is single-entity. A keypair is a field row of
the user, so every operation over a keypair is answered for by the owning user.

## The shape of the keypair operations

A keypair row carries no membership of its own. A request naming a keypair by its
access key reads the owning user through the key owner lookup first, and the operation
that follows names the user. Every write is an UPDATE — adding and removing a keypair
row is a change to that user.

## Bootstrap scripts and dotfiles

- `bootstrap_scripts` holds scripts per `(entity_type, entity_id)`; at most one live script (`deleted_at IS NULL`) per entity is `is_default`.
- A script's content lives in `bootstrap_script_revisions`, which only ever gain rows: an update appends the next `revision_number` with the requester as `creator_id`, and the latest revision is the current content.
- The API and session creation use the latest revision of the user's live default script. Reading one that is missing answers an empty script; updating it answers not found.
- `dotfiles` stores one file per row with `entity_type`, `entity_id`, `path`, `perm`, `data`, and `is_default`. Each entity has at most one default row per path; user APIs and sessions use these rows.
- `(entity_type, entity_id)` references `virtual_entities` with `ON DELETE CASCADE`. Creating for an entity with no node fails, and a row created while its owner is purged goes with the node.
- Project and domain dotfiles remain in their existing columns.
- Creation stores a non-default file. Its ActionResult retains `entries`: the existing default files followed by the new file. No runtime operation currently selects a default; migrated default files remain available.
- Requests limit each file's `data` to `MAXIMUM_DOTFILE_SIZE` characters, the limit the row's CHECK enforces.
- The adapter creates `DotfileEntryCreator`. `CreateDotfileAction` passes it to `UserRepository`, which calls write ops in one transaction. `DotfileEntryCreator` names the owner, and `CreateDotfileAction` takes its user from there.
- Migration unpacks keypair bytes, deduplicates `(path, perm, data)` per user, and preserves whether any source was the default keypair. It reads rows in batches and writes up to 1,000 file rows per insert before dropping `keypairs.dotfiles`.
- Downgrade packs each user’s default files into msgpack and restores them to all of that user’s keypairs.
- Reads are `SearchDotfilesAction` on `DotfileProcessors`, scope-shaped with the user as the scope, from a dangling field group because the owner's kind is a value on the row. The legacy single-file read is that search with a path condition. `UpdateDotfileAction` and `PurgeDotfileAction` name one row by id and are answered for by the owner its lookup reads; the legacy update and delete find the default row's id by path first.
- An access key selects its owning user for the existing dotfile API. Purging a user deletes its dotfile rows.

## The operations that keep a service

Creation (which creates a keypair with the user), purge (which cleans up vfolders,
sessions and endpoints), the bulk operation set, every keypair operation, the monthly
statistics and the dotfile write set stay in the service. The four reads — global, by
domain, by project, by role — go straight to ops.

## A role is not a scope a user sits in

`search_users_by_role` is a global search with a condition, not a scope search.
