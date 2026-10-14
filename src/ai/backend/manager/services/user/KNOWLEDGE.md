---
name: user-service-composition
type: decision-table
description: why a user's operations take the shapes they do, why a keypair is a field row of the user, why the email-addressed operations are gone
scope: src/ai/backend/manager/services/user
keywords:
  - UserProcessors
  - keypair_group
  - LookupKeypairOwnerByAccessKeyAction
  - KeypairDotfilesUpdater
  - bootstrap_script
sources:
  - src/ai/backend/manager/services/user/processors.py
  - src/ai/backend/manager/models/keypair
  - src/ai/backend/manager/models/user
  - src/ai/backend/manager/models/bootstrap_script
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

- `bootstrap_scripts` holds scripts per `(entity_type, entity_id)`; at most one per entity is `is_default`.
- The API and session creation use the user's default script. Reading one that is missing answers an empty script; updating it answers not found.
- Dotfiles stay on `keypairs.dotfiles`.

## The operations that keep a service

Creation (which creates a keypair with the user), purge (which cleans up vfolders,
sessions and endpoints), the bulk operation set, every keypair operation, the monthly
statistics and the dotfile write set stay in the service. The four reads — global, by
domain, by project, by role — go straight to ops.

## A role is not a scope a user sits in

`search_users_by_role` is a global search with a condition, not a scope search.
