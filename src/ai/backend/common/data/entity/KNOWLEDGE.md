---
name: entity-type-catalog
type: reference
description: entity classification (Entity/Public entity/Global/Field/Virtual), ownership and reference relations, the foreign-key rule for assignments
scope: src/ai/backend/common/data/entity
keywords: [EntityType, ENTITY_TYPE, EntityCreator, GlobalEntityCreator, FieldEntityCreator, member_of, virtual entity, ownership, entity relation]
sources:
  - src/ai/backend/common/data/entity
  - src/ai/backend/manager/models
generated:
  by: claude-code/opus-5
  at: 2026-08-16
status: draft
---

# Entity catalog

This package declares one type constant per entity. A constant carries only a name, so
what the entity is, what it owns and what it is tied to is recorded here. Everything is
stated at the conceptual level; which table holds it belongs to the `models` documents.

A tree states ownership; a table states fields and references. A field is authorized
through the entity that owns it, while a reference is not ownership and therefore never
becomes an authorization path.

## Entity

An entity that belongs somewhere. There is no common root — several entities sit at the
top.

```
domain
├── project
│   ├── session
│   ├── session group
│   ├── deployment
│   ├── network
│   ├── vfolder          (owned by project)
│   ├── model card
│   └── role
└── user
    ├── vfolder          (owned by user)
    └── role

resource group
└── agent

container registry
└── image
```

### domain

| Relation | Targets |
|---|---|
| field | usage bucket |

### project

| Relation | Targets |
|---|---|
| field | usage bucket |

### user

| Relation | Targets |
|---|---|
| field | keypair, error log, login session, login history, usage bucket |
| reference | resource policy |

### session

| Relation | Targets |
|---|---|
| field | kernel |
| reference | image, vfolder, session group, resource group |

### deployment

| Relation | Targets |
|---|---|
| field | replica group, replica, deployment revision, deployment policy |
| reference | image, vfolder, runtime variant, deployment revision preset, session group, resource group, prometheus query preset |

### model card

| Relation | Targets |
|---|---|
| reference | vfolder |

### role

| Relation | Targets |
|---|---|
| field | permission |

### resource group

| Relation | Targets |
|---|---|
| field | fair share |

### agent

| Relation | Targets |
|---|---|
| field | agent resource |

### image

| Relation | Targets |
|---|---|
| field | image alias |

## Public entity

Reading requires authentication only; creating, updating and deleting are admin-only.

### Execution spec

| Entity | Chosen by |
|---|---|
| runtime variant | deployment revision |
| runtime variant preset | references a runtime variant |
| deployment revision preset | deployment revision |
| session template | session |
| resource preset | session |
| resource slot type | agent resource |

### Authentication

| Entity | Chosen by |
|---|---|
| login client type | login session |

## Global

Both reading and writing are admin-only.

### Policy

| Entity | Field | Reference |
|---|---|---|
| resource policy | | |
| retention policy | | |
| role preset | role permission preset | |

### Artifact

```
artifact registry
└── artifact
```

| Entity | Field | Reference |
|---|---|---|
| artifact registry | huggingface registry, reservoir registry | |
| artifact | | storage namespace |

### Storage

| Entity | Field | Reference |
|---|---|---|
| storage namespace | object storage, vfs storage | |

### Observability

| Entity | Field | Reference |
|---|---|---|
| audit log | | |
| event log | | |
| prometheus query preset | | prometheus query preset category |
| prometheus query preset category | | |

### Notification

| Entity | Field | Reference |
|---|---|---|
| notification channel | | |
| notification rule | | notification channel |

### Configuration and operations

| Entity | Field | Reference |
|---|---|---|
| app config definition | | |
| app config allow list | app config fragment | app config definition |
| idle checker | | |
| service catalog | | |

## Assignment

An administrator assigns a shared resource to a scope. Neither side contains the other,
so this is not a virtual-entity edge; an assignment table is not an entity itself but a
relation between two entities.

### resource group

| Assigned to |
|---|
| domain |
| project |
| keypair |

### idle checker

| Assigned to |
|---|
| domain, project, user |

## Assignment foreign keys are RESTRICT on both sides

- This is not ownership, so deleting one side does not mean deleting the other. The
  dependency is large, though, so whether to move or delete a linked entity is a decision
  the application must make.
- RESTRICT raises that decision to the application. If the database quietly cleans up,
  the point where the decision would be made disappears.

## Virtual

Built without a row of its own. It exists only as the subject of audit and authorization.

| Entity | Read at |
|---|---|
| app config | the scope being read |

## Out of scope

A virtual entity is the layer that expresses ownership, not an entity.

## Missing foreign keys

Ownership relations with no foreign key declared.

- artifact → artifact registry (`registry_id`, `source_registry_id`)
- artifact registry → huggingface / reservoir registry (`registry_id`, polymorphic)
- deployment revision → deployment (`endpoint`)
- storage namespace → object storage or vfs storage (`storage_id`, polymorphic, no discriminator)
- association_artifacts_storages → artifact revision, storage namespace
- network → project

## Direction: fold identifiers onto the entity axis

Most id types identify an entity or a field, so they are declared in the same file as the
entity type constant. Adding only one of the two then shows up simply by opening the file,
and a file with no type constant becomes a signal in itself — either a field, or not yet
classified.

- A scope identifier is an alias of an entity identifier, so it belongs on this axis.
- A value type that does not identify an entity is not moved along. Values such as an
  architecture name, or an id naming a single execution, stay with the base types.
- Giving each entity a package and splitting the details into files leaves room to move
  related things underneath it later.
