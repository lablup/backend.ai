---
name: project-service-composition
type: decision-table
description: why a project's operations take the shapes they do, why dotfiles are a column of the project row, why membership takes a path of its own, what a personal project changes
scope: src/ai/backend/manager/services/project
keywords:
  - GroupProcessors
  - GroupCreator
  - GroupUpdater
  - GroupDotfilesUpdater
  - assign_users_to_project
  - RoleManagedEntityCreator
  - ProjectType
  - personal project
sources:
  - src/ai/backend/manager/services/project/processors.py
  - src/ai/backend/manager/models/project
  - src/ai/backend/manager/data/project/types.py
generated:
  by: claude-code/opus-5
  at: 2026-08-22
status: draft
---

# Project service

A project sits under a domain, so creation is scope-shaped with the domain as the
scope, and an operation naming an existing project is single-entity.

## The processor composition

`backend.ai mgr ops list --concern organization --entity project` prints the wired
list. Its output answers the entity type, shape, operation, gate and backing.

## Personal projects

`ProjectType.PERSONAL` changes behavior in two places; everything else behaves like a
regular project.

| Place | Behavior |
|---|---|
| Member addition | Refused on all four paths: the project member update (add), user assignment, user binding, and the project sync that a user create or update runs |
| Deletion and purge | Refused on its own. A personal project goes with its user |

The project sync on a user update leaves personal projects out of both sets. Keeping one
out of the target set is not enough; it has to stay out of the current set too, or the
sync detaches the user from their own personal project.

Listing does not filter by type. The legacy group query already leaves them out through
its `type=[GENERAL]` default, and v2 search judges by scope and permission alone. A domain
search returns the projects that sit in the domain and the caller can reach, so a personal
project is visible to its owner and to domain admins.

Usage queries do not leave personal projects out. Their sessions consume real resources,
so dropping them makes the installation-wide totals wrong, and both usage endpoints can
name a project, which would then answer empty.
