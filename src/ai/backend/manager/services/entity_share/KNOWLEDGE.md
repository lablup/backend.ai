---
name: entity-share-service-composition
type: design-rationale
description: the scope each entity share answer is checked in, the scope that answers a share addressed to a project, a user or an email, why the answering scope is resolved by a lookup that costs read on it
scope: src/ai/backend/manager/services/entity_share
keywords:
  - EntityShareProcessors
  - LookupEntityShareAnsweringScopeAction
  - EntityShareRepository.answering_scope
  - AcceptEntityShareAction
  - RejectEntityShareAction
  - LeaveEntityShareAction
  - answering_scope
sources:
  - src/ai/backend/manager/services/entity_share/processors.py
  - src/ai/backend/manager/services/entity_share/actions/answer.py
  - src/ai/backend/manager/services/entity_share/actions/lookup_answering_scope.py
  - src/ai/backend/manager/repositories/entity_share/repository.py
  - src/ai/backend/manager/models/entity_share/updaters.py
generated:
  by: claude-code/opus-5.5
  at: 2026-11-17
status: draft
---

# Entity share service

An entity share lends an entity from the sharing side to a person or a project, and the
receiving side accepts, rejects or gives it back. This package decides which scope each of
those answers is checked in.

Korean: [KNOWLEDGE.ko.md](KNOWLEDGE.ko.md)

## The processor composition

`backend.ai mgr ops list --concern rbac --entity entity_share` prints the wired list.
Its output answers the entity type, shape, operation, gate and backing.

## An answer is checked in the scope that answers the share

- `accept`, `reject` and `leave` are scope-shaped on `answering_scope`: the caller needs `update` on `entity_share` (`soft_delete` for `leave`) in that scope, granted there or in a scope governing it.
- `answering_scope` is the node the share is addressed to: the project, or the user.
- A share addressed by an email holds no node until it is answered, so the user holding that address answers it.
- The write guard matches the share's recipient against `answering_scope` in the same statement, so a scope the share does not name settles nothing.

## The answering scope is resolved first, and resolving it costs read on it

- `lookup_answering_scope` reads the share by its id and returns the scope it names: the answer cannot name its scope until the row is read.
- A share that names no scope yet resolves through its address to the user holding it, which takes a second read by email.
- It is wired through `group.lookup`, so the caller needs read on the scope it resolved: themselves, or the project. A caller without it gets the answer a share that does not exist gets.
- The answer that follows is checked in the same scope for `update` (`soft_delete` for `leave`).
