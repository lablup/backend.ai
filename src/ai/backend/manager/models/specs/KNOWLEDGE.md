---
name: write-spec-design
type: design-rationale
description: write-spec selection criteria (Entity/Global/Field/Sidecar/Relation), why a row two entities own belongs to neither position and declares its own conflict handling, why the roots share no common ABC, what a sidecar row is and why it belongs to neither position, why the role-managed root is not an EntityCreator subtype, why a global entity is provisioned in the graph, how a field row's owner is read, the two graph relations (own, govern), how created_in combines them, relation and cap-based sharing, open entity-type strings
scope: src/ai/backend/manager/models/specs
keywords: [RelationCreator, RelationPurger, RelationLifecycleUpdater, EntityCreator, GlobalEntityCreator, FieldCreator, RoleManagedEntityCreator, SidecarCreator, FieldOwnerLookup, RoleTemplateSource, created_in, create_relation, entity_id, virtual-entity, preset-role, DataUpdater, soft-delete]
sources:
  - src/ai/backend/manager/models/specs/creator.py
  - src/ai/backend/manager/models/specs/lookup.py
  - src/ai/backend/manager/models/specs/role_template.py
  - src/ai/backend/manager/repositories/ops/v2
generated:
  by: claude-code/opus-5
  at: 2026-08-18
status: stable
---

# Write specs — Knowledge

> Rules: `AGENTS.md` in the same directory.

## Why this package exists

Write specs turn "what to write" (rows, memberships, integrity checks) into
declarations next to the schema, while execution is owned by the ops layer. It
exists so that the RBAC side effects of a write — provisioning in the graph,
registering memberships — are decided by the **spec's type**, not by the
execution path.

## Spec selection: the only remaining question is "is it an entity"

**Every entity has a node in the graph** — it can own memberships and can be shared.

| Spec | Criterion | Write behavior |
|---|---|---|
| Entity | First-class entity (vfolder/session/...) | create provisions the node (it owns and governs itself) and is owned and governed by each `created_in()` scope; purge tears down symmetrically; upsert stays idempotent |
| Global, role-managed | Entities that grant preset roles, created in no scope (domain, resource group) | Global behavior + preset role creation — `RoleManagedGlobalEntityCreator` |
| Entity, role-managed | Entities that grant preset roles, created in a scope (project, user) | Entity behavior + preset role creation — `RoleManagedEntityCreator`, `created_in()` the domain |
| Global | An entity that goes under no other entity | Entity behavior minus `created_in` — the node is provisioned the same way |
| Field | A row another entity owns (even with its own get/delete API) | create requires `owner_id`; purge is a plain delete |
| Sidecar | A row outside the graph — an audit record, an event log | create inserts and nothing else; the entity it names is read by, not belonged to |

## A relation belongs to both, so it belongs to neither position

- The write specs split on ownership, and both positions assume it is zero or one: an
  entity owns itself, a field is owned by exactly one entity. A row linking two entities
  is owned by both, which neither position can say.
- Ownership is read off the schema, not off the call site: what deletes the row when it
  goes is what owns it. A polymorphic reference carries no foreign key, so ownership
  there is a fact about the code that cleans up rather than about a constraint.
- The relation roots therefore name the pair, never a row id. Nothing outside the layer
  that wrote the row holds that id, and a read answers with the entities the relation
  reaches rather than the row between them.
- Conflict handling is the spec's because it is the table's. A unique constraint on the
  bare pair means a soft-deleted row still occupies it, so an insert that did nothing
  would leave the relation switched off; a partial index on (pair, alive) admits a new
  row and keeps the history. One rule cannot serve both, so `build_conflict_values()`
  declares which.
- Full rationale: `proposals/BEP-1075-entity-relation-operations.md`.

## A sidecar belongs to neither position

- An entity can stand on its own and is woven to other entities through virtual entities;
  a field cannot stand on its own and is an extension of its owner's value, handled with
  the owner's permission.
- A sidecar takes the diagonal: it stands on its own, yet carries no node and is read
  through an entity's permission the way a field is. An audit record outlives the entity
  it is about, and some name no entity at all.
- So its create settles nothing — no node, no owner. The entity it names is a value a
  reader is authorized by, which is why the read is scope-shaped on that entity while
  the row belongs to no one.

## The absence of a common ABC is itself the enforcement mechanism

- With a shared supertype, an entity spec passed to an execution path that provisions
  nothing would pass type checking and silently skip it — exactly the bug this lineage
  is meant to prevent.
- Duplicating method declarations across roots is the price of making that path
  inexpressible.
- Execution-logic reuse happens via ops helpers that take plain values.

## The role-managed root not being a subtype is the same mechanism

- If `RoleManagedEntityCreator` were a subtype of `EntityCreator`, it would pass type
  checking on the plain `create_entity` path and silently skip preset roles.
- The entity hooks are duplicated onto the combined root so that the only path that
  accepts it is the role-managed path.
- `RoleTemplateSource` remains the sole shared base because no write path accepts it
  on its own.

## Why a global entity is provisioned too

Rows are created under a global entity as well — an image under its container
registry. Without a node those rows have nothing to point their membership at, and
the global entity itself is reachable by nobody but a super-admin.

The delete side always tore the node down (`purge_entity` calls `_teardown_entity`).
The create side removed the asymmetry of tearing down what was never built.

## A field row carries an id of its own

- A row with exactly one owning entity is a field row. How it points at that owner —
  a cascading FK, or a polymorphic `(entity_type, entity_id)` pair — is not the test,
  and neither is whether an API names one individually today.
- So such a table gets an `id` uuid. Where the primary key is composite it stays as it
  is and `id` is added as a unique column: every existing query and index survives, and
  a `FieldIdentifier` becomes expressible.
- The five tables recording one slot's amount per owner (agent / session / model card /
  deployment preset / deployment revision) are this shape.

## Which end the operation starts from decides the check

| Starting point | Owner known | Shape | Checked against |
|---|---|---|---|
| a field row's id | no | field | the owning entity, read first |
| an entity's id | yes | scope | that entity, as the scope |

- A read that comes back with several of that entity's field rows started from the
  entity, so it names where to look rather than what to touch — the scope shape, with
  the owner as the scope.
- Creating a field row takes the owning entity's id for the same reason.
- The rules: `../../actions/AGENTS.md`.

## A field row's membership is only knowable through its owner

- A field row carries no membership of its own, so an operation naming one has nothing
  to validate and nothing to record against. `FieldOwnerLookup` fills that in: from a
  field row's id to its owning entity's id.
- It declares a query rather than conditions for two reasons. An owner may be reachable
  only through a join, and selecting the pair (row id, owner id) is what keeps a batch
  from losing which row each owner belongs to.
- It is generic because `Select`'s type parameter is invariant: a concrete column type
  does not match a loosely declared one, so the implementation states both of its own.
  `DataBatchPurger` is generic over its row type for the same reason.

## Soft delete is guarded by the absence of a field

The same mechanism as the spec roots: what stops a write is the shape of the
declaration, not a check at execution time.

A soft delete is an UPDATE at the DB, so ops cannot tell it apart from an edit — there
is no delete operation to generalize and no place there to enforce anything. What
separates them is the action's `operation_type()`, which decides the RBAC permission
and the audit row's `operation`.

That leaves one hole: an ordinary edit that writes the lifecycle column would be
recorded as `UPDATE`, and the deletion would never appear in the trail. Removing the
field from the general updater closes it — the edit path has nothing to make the
transition with. Splitting delete and restore into their own updaters with constant
`build_values()` closes the rest: a transition value taken as an argument is a value
that can be passed wrong.

Which column carries the state is domain knowledge and varies (`deleted` on a role
preset, `status` on a vfolder or user), which is why this is a rule about the general
updater's fields rather than about a column name.

## own 과 govern 은 다른 관계이고, 생성은 둘을 조합한다

- own: ve 가 entity 를 소유한다. entity 가 그 ve 의 명단에 오르고("조회 = 등재") 한 홉에 닿는다.
- govern: scope 가 ve 를 다스린다. scope 의 role 이 그 ve 가 own 한 것 전부에 닿는다. own 보다
  큰 관계다.
- 해석기는 `entity → 그 entity 를 own 한 ve → 그 ve 를 govern 한 scope → role` 로 한 홉 걷는다.
  모든 entity 는 자기 ve 가 자기를 own 하고 자기 scope 가 자기 ve 를 govern 한다(`_provision_entities`).
- `created_in`(session → project·user): 만든 곳이 own 하고 govern 한다. own 으로 project role 이
  session 에 닿고 목록에 오르며, govern 으로 session 이 own 한 것(초대)에도 닿는다. domain 은 user
  ve 를 govern 하므로 user 가 own 한 session 에 닿는다.
- project·user 도 `created_in`(domain) 이다. domain 이 own 하고 govern 한다. own 은 해석에 더해
  주는 것이 없지만(자기 own + govern 으로 이미 닿음) 무해하고, scope 와 리소스 entity 를 한 규칙으로
  만든다. user 의 ve 는 자기 domain 만 govern 한다 — project 가 govern 하면 user 가 own 한 것이
  project 로 샌다(BEP-1077).
- 예전 `member_of` 도 둘을 한꺼번에 썼다. 이름이 own 하나만 말해서 govern 이 숨어 있었다.
- 공유(`EntityGrant`)는 cap 이 붙은 own 이고 govern 이 없다. 그래서 공유받은 entity 가 own 한
  것에는 닿지 않고, 해석기는 공유를 공유된 entity 의 타입에 대해서만 통과시킨다(공유받은 vfolder
  를 scope 로 삼아 초대를 읽을 수 없다).
- relation(`create_relation`): project 와 resource group 이 서로를 READ cap 으로 own 한다. govern 이
  없으니 상대가 own 한 것에는 닿지 않는다.
- 두 축으로 root 넷: `created_in` 유무(Global / Entity) × preset 역할 유무(plain / RoleManaged).
  role-managed 는 preset 을 만드는 것 외에 plain 과 같은 관계를 맺는다.
- 한계: govern 은 한 홉이라 domain → user → session → 초대 처럼 세 단계면 domain 이 초대에 못 닿는다.
  필요해지면 govern 을 쓸 때 상위 scope 의 govern 을 함께 복사하는 방식으로 닫는다.

## Entity type is an open string

- This is so a new type can register members before the permission layer knows about
  it — only permission-carrying paths convert lazily and reject there.
- The registration-time integrity guarantee is: "a write against a target with no node
  fails".
- The axis that separated scope type from entity type is gone from the spec hooks.
  Every entity has a node, so there was nothing left to separate.
