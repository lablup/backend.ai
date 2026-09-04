# Write specs (v2 lineage) — Guardrails

> For the selection table and design rationale, see `KNOWLEDGE.md` in the same directory.

Declarative write specs, colocated with the schema: a spec says *what* to write
(row, membership, checks); executing it is the ops layer's job
(`repositories/ops/v2/`). Specs must NOT touch sessions or issue SQL.

## Every v2-consumed spec lives here

Whatever spec type the v2 actions and ops consume is declared in this package — the
write specs below, plus the read/update declarations (`querier.py`, `lookup.py`,
`searcher.py`, `updater.py`, `pagination.py`, and the batch purge spec in
`purger.py`). `repositories/base/` keeps legacy-compatible views for the transition
only; do not declare a new spec there.

## A relation is neither an entity nor a field

- A row linking two entities belongs to neither: both own it. It is not a field row,
  which has exactly one owner, and it is not an entity, which has a node in the graph.
- Its specs are `RelationCreator` / `RelationLifecycleUpdater` / `RelationPurger`
  (`relation.py`), and they name the pair rather than a row id — a relation row's id
  never leaves the layer that wrote it.
- create 는 새 행만 넣는다. 이미 맺어진 쌍(꺼진 것 포함)은 unique 위반이고, spec 의
  `integrity_error_checks` 가 도메인 오류로 바꾼다. 되살리기는 restore updater 의 일이다.
- 끄기 / 되살리기(`RelationLifecycleUpdater`)는 행의 lifecycle 컬럼만 바꾼다. 서로를 읽는 관계는
  그대로라 꺼진 relation 도 양쪽 목록에 보이고 다시 켤 수 있다. 접근을 지우는 것은 purge 뿐이다.
  lifecycle 컬럼이 있는 relation 만 이 updater 를 선언하고, 방향마다 한 클래스가 상수를 돌려준다.
- Do NOT carry a relation as a field on a `DataUpdater`. A value whose change drags
  other writes along does not belong on the general edit path — the same rule soft
  delete follows.
- Rationale: `proposals/BEP-1075-entity-relation-operations.md`.

## What a spec splits on depends on the operation

A row in the graph is an entity or a field, and which one it is comes from the table
in `KNOWLEDGE.md`. A row outside it is a sidecar — it stands on its own like an entity
and is read through an entity's permission like a field, while belonging to neither.

| Operation | Roots | Why |
|---|---|---|
| creator | `GlobalEntityCreator` / `EntityCreator` / `RoleManagedGlobalEntityCreator` / `RoleManagedEntityCreator` / `FieldCreator` / `SidecarCreator` | only a create settles what a row belongs to |
| purger | `EntityPurger` / `EntityBatchPurger` / `FieldPurger` / `GuardedFieldPurger` / `FieldBatchPurger` | removing an entity removes what it left in the graph; a field row splits further on how it is picked: by id, or by id behind a precondition; the batch roots pick by subquery instead of by id |
| updater | `DataUpdater` / `GuardedDataUpdater` | an update never changes what a row belongs to, so the roots split on how the row is picked: by id, or by id behind a precondition |

The roots are deliberately unrelated. Do NOT extract a common base across them
or type any function against "any creator/purger" — the absence of a common supertype
is the enforcement. Reuse execution logic through ops-layer helpers that take plain
values (`row_class`, `pk_value`, ...).

## An entity answers its own id

- A creator and an upserter answer one hook — `entity_id(row)`. It returns an
  `EntityIdentifier`, which answers its own type, so nothing declares the type
  separately.
- It takes the row because the id does not exist before the insert; the database
  usually fills it.
- Some tables key on something else (a resource policy's primary key is `name` and its
  id is a separate `uuid` column). Which column it is, only the domain knows.

## A global entity is an entity too

`GlobalEntityCreator` merely does not go under another entity; it provisions its own
virtual entity node exactly as `EntityCreator` does. Rows are created under a global
entity too — an image under its container registry — so it has to be namable in the
graph. What it does not have is `created_in`, and the missing hook is what says it
is created in no scope.

## 관계 선언

- 그래프의 관계는 둘이다. **own**: ve 가 entity 를 소유한다 — entity 가 그 ve 의 명단에 오르고 한
  홉에 닿는다. **govern**: scope 가 ve 를 다스린다 — scope 의 role 이 그 ve 가 own 한 것 전부에
  닿는다. govern 이 own 의 상위 개념이다.

| 훅 | own | govern | 뜻 |
|---|---|---|---|
| `EntityCreator.created_in(row)` / `EntityUpserter.created_in(row)` / `RoleManagedEntityCreator.created_in(row)` | 있음 | 있음 | session 은 project 와 user 안에서, project 와 user 는 domain 안에서 만들어진다. 만든 곳이 own 하고 govern 한다. 대상이 없으면 쓰기가 실패한다. `GlobalEntityCreator` / `RoleManagedGlobalEntityCreator` 는 이 훅이 없다 |
| (훅 없음) preset role | 있음 | 없음 | role 은 scope 가 own 만 한다 |
| share write: `replace_share` / `replace_share_fields` … | cap 있음 | 없음 | 공유: cap 이 붙은 own. 받은 scope 에 빌려준 것 |
| share write: `transfer(from_scopes, to_scopes, entity)` | 있음 | 있음 | 소유권 이동: 옛 scope 에서 빠지고 새 scope 에서 만들어진 것처럼 own·govern. 공유가 있던 자리면 own 으로 바뀐다 |
| relation write: `create_relation(creator, scope, target)` / `purge_relation` | target 이 scope 를 cap READ 로 | scope 가 target 을 cap READ 로 | project 는 resource group 과 그것이 own 한 것(agent)을 READ 하고, resource group 은 project 자신만 READ 한다 |

- cap 이 붙는 자리는 둘이고, 한 경로에 하나만 걸린다.

| entity → ve (own 쪽) | ve → scope (govern 쪽) | 허용 |
|---|---|---|
| own, cap 없음 | 자기 govern 또는 타 govern, cap 없음 | 예 (생성) |
| own, cap 없음 | 타 govern, cap 있음 | 예 (relation 의 scope 쪽) |
| 공유, cap 있음 | 자기 govern | 예 (공유, relation 의 target 쪽) |
| 공유, cap 있음 | 타 govern | **아니오** |

- 공유는 받은 scope 에 빌려준 것이다. 그 scope 의 자기 govern 으로만 답하고, 그 ve 를 govern 하는
  다른 scope 에는 답하지 않으며, 공유된 entity 자신에게만 답한다: 공유받은 vfolder 를 scope 로
  삼아 그 아래 초대를 읽을 수 없고, resource group 에 공유된 project 를 그 resource group 을
  govern 하는 다른 project 가 읽을 수 없다.
- 공유는 전 필드와 필드 경로로 나뉘고, 각각 replace / 부분 추가 / 부분 제거를 갖는다.

| | 전 필드 cap | 필드 경로 (READ/UPDATE, 자손 포함) |
|---|---|---|
| replace (이전 것 **전부** 대체) | `replace_share(scope, entity, cap)` — 0 도 cap | `replace_share_fields(scope, entity, {READ: paths, UPDATE: paths})` |
| 부분 추가 | `widen_share` | `widen_share_fields` |
| 부분 제거 | `narrow_share` — 비트의 행을 지움 | `narrow_share_fields` — 경로와 자손을 지우고 빈 행은 삭제 |
| 전부 제거 | `unshare(scope, entities)` — own 은 남긴다 | |

- 전 필드 비트와 경로가 섞인 공유는 replace 하나로 못 적는다: `replace_share(cap)` 뒤에 `widen_share_fields`.

- 초대 수락은 `accept_invitation(updater)`: 초대 행 갱신과 `widen_share` 가 한 트랜잭션. 초대는
  제안 중인 공유이므로 share write 에 있다.
- 세 쌍은 `repositories/AGENTS.md` 의 규칙대로 provider 로만 받는다. 이미 있는 것을 공유하려고
  creator 를 쓰지 않는다.
- Entity types are open strings: types outside the RBAC element enum are accepted, and
  permission-carrying paths convert lazily.
- Do NOT keep module-level declaration instances (no `X_MEMBERSHIP = ...()`).

## Role-managed entities

- Entities that allow role presets implement `RoleManagedGlobalEntityCreator` (domain,
  resource group: created in no scope) or `RoleManagedEntityCreator` (project, user:
  `created_in` a domain) and are executed through the matching ops methods, as the
  plain `GlobalEntityCreator` / `EntityCreator` pair is. The type decides the path;
  there is NO runtime capability check (`isinstance`).
- Neither role-managed root is a subtype of its plain counterpart. `RoleTemplateSource`
  is the only shared base; no write path accepts that type bare.
- Entity specs declare NO roles — the spec contributes only `template_value(row)` for
  the presets' name templates. Restricting which types may carry presets is the
  preset-creation service's validation.
- The plain entity paths never touch roles, even when matching presets exist.
- Enrollment writes graph relations only. Granting a joining user the target's auto_assign
  roles is an explicit ops primitive — never an implicit side effect keyed on the type.

## A batch purge says which kind it removes, and what bounds it

- `EntityBatchPurger` tears down each deleted row's virtual entity, memberships and
  permissions, as `EntityPurger` does for one; `FieldBatchPurger` does not, because a
  field row holds nothing in the graph.
- The two are unrelated roots, so an entity spec cannot flow through the field path and
  leave its graph rows behind. There is no unmarked batch purge.
- What bounds the sweep follows the same axis every other write does: an entity batch is
  bounded by the scopes the ops call names, a field batch by the owner it is given —
  `build_subquery(owner_id)`, like `create_field(owner_id, ...)`. No field operation is
  scoped, and this one is not either.
- `EntityBatchPurger.entity_id(row)` takes the row: a batch names a subquery, not an id.

## Values left for the database to compute

- A creator may put a SQL expression on a column in `build_row()`; the value is then
  computed inside the INSERT, with no lock and no SELECT before it. A rank asking for
  "one past the last" is what this is for.
- Concurrent inserts can land on the same value. Do NOT use it where the order has to
  be deterministic.
- Such a column is read back once after the insert. ops works that out from the row, so
  a spec declares nothing.

## A field row's owner

- A field row carries no membership of its own. What it belongs to is only knowable
  through the entity that owns it, so an operation naming a field row has to read that
  entity before it has anything to validate and record against.
- `FieldOwnerLookup` declares that read: from a field row's id to its owning entity's
  id. A query rather than conditions, so an owner reached through a join is
  expressible; it selects the pair (row id, owner id), so one spec serves a single row
  and a batch alike.
- It takes two type parameters, so the type `field_id()` answers and the type this
  lookup handles cannot come apart.
- `FieldOwnerKeyLookup` reads the same thing from the other end: a caller-facing key to
  the owner. `FieldKeyLookup` reads the row's id and the owner's from that key in one
  query — an operation naming the row takes its id, so the key has to become one
  somewhere.
- Do NOT pre-read the owner to check existence. Declare the FK violation in
  `integrity_error_checks()` mapped to the domain error; preconditions beyond
  existence (e.g. lifecycle) belong to the service layer as EXISTS checks.

## Soft delete belongs to its own updaters

- The lifecycle column a domain deletes by — `deleted`, `status`, whichever carries
  the removed state — is NOT exposed on the general `DataUpdater`. With no field for
  it, the ordinary edit path cannot make the transition at all.
- Soft delete and restore each get their own updater, and `build_values()` returns a
  constant. A transition value taken as an argument is a value that can be passed
  wrong.
- Naming: `<Entity>SoftDeleteUpdater` / `<Entity>RestoreUpdater`, carried by a
  `Delete*` and a `Restore*` action base respectively.
- A domain that offers soft delete offers restore.
- ops executes both as an update — the DB operation is an UPDATE, so no delete
  operation exists to generalize. What records the run as a delete is the action's
  `operation_type()`; see `../../actions/AGENTS.md`.

## Naming: what is written vs where a read looks

`…_global_entity` / `…_entity` / `…_field_entity` methods name **what is written**;
`…_in_global` / `…_in_scopes` name the **operation scope** (where a read looks). Never
conflate the two axes.
