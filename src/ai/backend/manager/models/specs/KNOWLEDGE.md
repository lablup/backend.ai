---
name: write-spec-design
type: design-rationale
description: write-spec selection criteria (Entity/Global/Field/Sidecar/Relation), why a row two entities own belongs to neither position, why switching a relation off keeps both reads, why the roots share no common ABC, what a sidecar row is and why it belongs to neither position, why the role-managed root is not an EntityCreator subtype, why a global entity is provisioned in the graph, how a field row's owner is read, the two graph relations (own, govern), how created_in combines them, relation and cap-based sharing, open entity-type strings
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
- 끄기는 접근이 아니라 상태다. project 에서 resource group 을 임시 제외해도 양쪽이 서로를 읽는
  관계는 남아야 "제외됨" 을 보여주고 다시 켤 수 있다(Kubernetes cordon, GitLab archive 와 같은
  선택). 그래서 lifecycle 전이는 행만 바꾸고, 그래프는 create 와 purge 만 움직인다. create 가 꺼진
  행을 되살리는 upsert 를 갖지 않는 이유도 같다 — 되살리기는 restore 하나의 일이다.
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
- 공유(`replace_share` / `replace_share_fields`)는 cap 이 붙은 own 이고, 받은 scope 에 빌려준 것이다. own 은 ve 에 넣는 것이라
  ve 를 govern 하는 모든 scope 의 것이 되지만, 공유는 그 ve 의 scope 하나에 준 것이라 그 scope 의 자기
  govern 으로만 답한다. 해석기는 그래서 공유를 (1) 공유된 entity 의 타입에 대해서만, (2) 자기 govern
  을 통해서만 통과시킨다. 공유받은 vfolder 를 scope 로 삼아 초대를 읽을 수 없고, resource group 에
  공유된 project 를 그 resource group 을 govern 하는 다른 project 가 읽을 수 없다.
- relation(`create_relation(scope, target)`): scope 가 target 을 READ cap 으로 govern 하고, target 은
  scope 를 READ cap 으로 공유받는다. project 는 resource group 과 그것이 own 한 agent 를 읽고,
  resource group 은 project 자신만 읽는다 — project 가 own 한 user·session·vfolder 는 드러나지
  않는다. govern 쪽 cap(`scope_bindings.permission_cap`)을 쓰는 것은 relation 뿐이다; 자기 govern 과
  `created_in` 의 govern 은 cap 이 없다.
- resource group 이 session·deployment 를 보는 것은 relation 이 아니라 스케줄 시 그 session 을
  resource group 에 READ 로 공유하는 것으로 답한다(후속). 다른 project 가 resource group 을 govern
  해도 공유는 그쪽에 답하지 않으므로 새지 않는다.
- 두 축으로 root 넷: `created_in` 유무(Global / Entity) × preset 역할 유무(plain / RoleManaged).
  role-managed 는 preset 을 만드는 것 외에 plain 과 같은 관계를 맺는다.
- 전 필드 공유와 필드 경로 공유는 뜻이 달라 메소드도 다르다. 저장은 같은 cap 행 트리(비트별 행,
  경로 행)이지만 선언에서 섞지 않는다. replace 는 이전 것을 전부 대체하고(조회 없이 지우고 붙임), widen 은 있는 것을 읽어 더하기만,
  narrow 는 빼기만 한다. 섞인 공유는 replace 뒤 widen 으로 적는다.
- 관계 ops 의 배치. private 프리미티브는 `V2GraphWriteOpsBase` 하나에 있고 어떤 provider 도 내주지
  않는다. public 은 세 provider / ops 쌍이다.

| 관계 | 쓰기 | 되돌리기 | 쓰는 곳 |
|---|---|---|---|
| 노드 | `_provision(entities)` — 노드 + 자기 own + 자기 govern | `_teardown(entity)` — 나머지 관계는 FK cascade | 생성 / purge |
| own | `_own(owners, entity)` — 공유가 있던 자리면 own 으로 | `_disown(owners, entity)` | preset role |
| govern | `_govern(scopes, entity, cap)` | `_ungovern(scopes, entity)` | relation (cap READ) |
| own + govern | `_created_in(scopes, entity)` — 노드 조회 한 번 | `_removed_from(scopes, entity)` | 생성, 소유권 이동 |
| 공유 (cap own) | `_share(scope, entity, cap)` — 전 필드 | `_unshare(scope, entities)` | relation, share write |

| 쌍 | provider / ops | 메소드 |
|---|---|---|
| entity write | `V2DBOpsProvider` / `V2WriteOps` | create / upsert / purge / update / field / batch. 생성 시 `_created_in`, purge 시 `_teardown` |
| relation write | `RelationOpsProvider` / `V2RelationWriteOps` | `create_relation(creator, scope, target)` / `purge_relation` — `_govern(cap READ)` + `_share(READ)` |
| share write | `ShareOpsProvider` / `V2ShareWriteOps` | `replace_share` / `replace_share_fields` / `widen_*` / `narrow_*` / `unshare` / `transfer` / `accept_invitation` |

  두 쌍의 ops 는 `V2WriteOps` 를 상속하므로 행 쓰기와 관계 쓰기가 한 트랜잭션에 놓인다(vfolder 의
  permission 행 + share, 초대 행 갱신 + share). "grant" 는 role 의 permission 을 주는 뜻과 겹쳐 쓰지
  않는다.
- 한계: govern 은 한 홉이라 domain → user → session → 초대 처럼 세 단계면 domain 이 초대에 못 닿는다.
  필요해지면 govern 을 쓸 때 상위 scope 의 govern 을 함께 복사하는 방식으로 닫는다.

## Entity type is an open string

- This is so a new type can register members before the permission layer knows about
  it — only permission-carrying paths convert lazily and reject there.
- The registration-time integrity guarantee is: "a write against a target with no node
  fails".
- The axis that separated scope type from entity type is gone from the spec hooks.
  Every entity has a node, so there was nothing left to separate.
