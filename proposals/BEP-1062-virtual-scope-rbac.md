---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-07-14
Created-Version:
Target-Version:
Implemented-Version:
---

# Virtual Scope RBAC Ownership Model

## Related Issues

- Epic **BA-6567** — Introduce Virtual Scope: a generalized RBAC ownership layer
- This BEP: **BA-6568**
- Already-done children (the as-built basis of this BEP):
  - **BA-6603** — Define Virtual Scope domain types (#12419)
  - **BA-6604** — Virtual Scope DB tables (ORM + Alembic) (#12503)
  - **BA-6605** — Virtual Scope DB ops (#12528)
  - **BA-6606** — Virtual-scope-chain permission check function (#12814)
  - **BA-6863** — Covering indexes for virtual-scope permission resolution (#12817)
- Upstream (extended here): **[BEP-1048](BEP-1048-RBAC-entity-relationship-model.md)** — scope-entity relationship model. See also: BEP-1008, BEP-1012 (RBAC), BEP-1056 (references virtual_scope).

## 1. Goal

Replace RBAC permission resolution's **recursive traversal with a non-recursive two-hop ownership model.**
Ownership is expressed as `scope → virtual_scope → entity`, and permissions are resolved over it.

**Why change now.** Today's resolution walks `association_scopes_entities` with a **recursive CTE**
(domain → project → user), inheriting a parent scope's permissions downward. This recursion has two problems:

1. When something breaks, it is **hard to trace which hop leaked a permission.**
2. Pre-materializing the inheritance produces a **connection blow-up on the order of `scope × entity`.**

**Virtual scope is the intermediate layer that solves both at once.** It groups ownership under one
hub node (the virtual scope) per owner, splitting it into two bounded relationships:

- `scope_bindings` — which scope exercises permission through which VS (scope → VS)
- `entity_memberships` — which entity belongs to which VS (VS → entity)

The results:

- Resolution finishes in **one path, one hop** — the recursion is gone.
- Connection count drops from `scope × entity` to `scope × VS` + `VS × entity`.
- BEP-1048's `auto`/`ref` edge distinction is **no longer needed** (3.(e), 3.(h)).

**What is built vs. not.** Virtual scope has **tables, types, DB ops, and a resolution function in code,
but is wired into no production path yet (nothing calls it).** This BEP documents that as-built surface
(section 2), fills the remaining design (sections 3–4), and splits the rest into follow-up issues.

## 2. Current State & Scope, by Area

For each area, separate **✅ what already exists / ➕ what to add**.

### 2.1 Data model (DB tables)

BA-6604 (tables) + BA-6863 (covering indexes) complete the schema.

| | Item |
|---|---|
| ✅ | `virtual_scopes` — one hub node per owner scope. `id` PK, `UNIQUE(scope_type, scope_id)`, `created_at`. **Exactly one VS per scope** |
| ✅ | `scope_bindings` — inbound `scope → VS`. PK `(virtual_scope_id, scope_type, scope_id)`, `permission_cap` (nullable = no ceiling), FK → `virtual_scopes` `ON DELETE CASCADE` |
| ✅ | `entity_memberships` — outbound `VS → entity`. PK `(virtual_scope_id, entity_type, entity_id)`, `permission_cap` (nullable), FK `ON DELETE CASCADE` |
| ✅ | Covering indexes (BA-6863): `ix_entity_memberships_entity (entity_type, entity_id) INCLUDE (virtual_scope_id, permission_cap)`, `ix_scope_bindings_virtual_scope (virtual_scope_id) INCLUDE (scope_type, scope_id, permission_cap)`, `ix_permissions_scope_entity ... INCLUDE (permission, role_id)` — forward/reverse joins served index-only |
| ➕ | Migration rule: move `association_scopes_entities` (auto/ref) + entity-level `permissions` into the three tables (section 4) |

### 2.2 Domain types

| | Item |
|---|---|
| ✅ | `common/entity/types.py` — `ScopeType`/`EntityType` as **open `NewType(str)`**. `ScopeRef`/`EntityRef`. Accepts any owner type without growing a fixed enum (core design) |
| ✅ | `common/data/permission/virtual_scope.py` — `VirtualScopeData`, `ScopeBindingData`, `EntityMembershipData` (frozen) |
| ✅ | `common/identifier/virtual_scope.py` — `VirtualScopeID = NewType(UUID)` |
| ✅ | `manager/data/permission/virtual_scope.py` — `VirtualScopePermissionCheckKey(user_id, entity)` |

### 2.3 DB write ops (BA-6605)

`RBACWriteOps`/`RBACOpsProvider` (`repositories/ops/rbac/provider.py`) has full CRUD. **But every virtual-scope write below has zero callers (not wired in yet).**

| | Item |
|---|---|
| ✅ | Create/delete: `create_scope`/`bulk_create_scopes`/`delete_scope`/`batch_delete_scopes` — materialize the real owner row and its VS node together. `_resolve_virtual_scope_id` raises `VirtualScopeNotFound(500)` when the VS is missing |
| ✅ | Scope binding: `bind_scope(scope, owner, permission_cap)` / `unbind_scope` |
| ✅ | Entity membership: `add_entity_members(scope, entities, permission_cap)` / `remove_entity_members` — invitation is expressed through this too (3.(e)) |
| ✅ | (not virtual) `add_users_to_scope` (enrolls users in a scope + grants auto-assign roles), `bulk_create_scoped` — write `association_scopes_entities`. **The only ops actually wired in today** |
| ➕ | Have the **RBAC ops provider's grant method** own the VS writes (including self scope_binding creation), and have the domain/project/user/resource_group operations use that provider/ops (unwired → wired) |
| ➕ | Rename `add_users_to_scope` to match what it does (enroll + auto-assign role) (2.7, follow-up) |

### 2.4 Permission resolution (read, BA-6606)

Lives in `repositories/permission_controller/db_source/db_source.py`. **But it is called only from a unit test — not exposed on the repository, not connected to any validator (not wired in yet).**

| | Item |
|---|---|
| ✅ | `resolve_effective_permissions_via_virtual_scope(keys)` — joins `entity → entity_memberships → scope_bindings → scope → permissions → roles → user_roles` in **one path, one hop**. Clips with `granted & scope_cap & entity_cap` (nullable = no ceiling), then OR-combines. One query per `(user_id, entity_type)` group |
| ✅ | `check_permission_via_virtual_scope` / `check_bulk_permission_via_virtual_scope` — bitwise checks |
| ✅ | (in use today) recursive scope-walk — `_build_scope_walk_cte(..., recursive=True)` traverses the scope hierarchy recursively |
| ⚠️ | Resolution can only reach through a scope_binding. Ownership (an owner seeing its own entities) is also expressed via a **self scope_binding**, but nothing creates that binding today (3.(c)) |
| ➕ | Reverse lookups: `scope → readable entities`, `entity → authorizing scopes` (RBAC page, 3.(b)) |
| ➕ | Wire into validators + remove the recursive scope-walk (3.(d), section 4) |

### 2.5 Enforcement toggle

| | Item |
|---|---|
| ✅ | `RBACConfig.enforcement_enabled` in `config/unified.py` (default True). Read only by the three action validators |
| ✅ | On → validators run the recursive scope-walk; off → early return (legacy path). **It gates only the recursive scope-walk, independent of virtual scope** |
| ➕ | Add a **separate config for virtual-scope resolution** (e.g. `rbac.resolution_backend`). Do not reuse `enforcement_enabled` — enforcement and resolution strategy are different axes. **This config and the old recursive walk are a temporary switch, both removed after cutover** (section 4) |

### 2.6 possible/impossible relationship model

| | Item |
|---|---|
| ✅ | `VALID_SCOPE_ENTITY_COMBINATIONS` (hand-written dict) in `common/data/permission/scope_entity_combinations.py` → GQL `rbac_scope_entity_combinations` |
| ✅ | Each RBAC action declares `permission_scope()` (scope) + `required_permission()` (entity, operation). `get_permission_matrix` (service.py:412) iterates these into a `scope→entity→operation` table → GQL `rbac_permission_matrix` |
| ➕ | **Define a dedicated dataclass derived from actions**, expose it as fields, access through it, then delete the `VALID_SCOPE_ENTITY_COMBINATIONS` constant. The dataclass **reads and combines** (a) scope reachability (scope actions) and (b) per-entity operations (single-entity actions) (3.(f)) |
| ➕ | Prerequisite: normalize all actions into the 3 RBAC action kinds (2.7) |

### 2.7 Action normalization

| | Item |
|---|---|
| ✅ | The 3 RBAC action/validator kinds exist: `ScopeActionValidator`, `SingleEntityActionValidator`, `BulkActionValidator` (+ `BaseRBACAction.permission_scope()`) |
| ➕ | Normalize every domain action into just these 3 — so permission checks reduce to three lanes (scope target / single-entity target / bulk target) and the possible/impossible derivation (2.6) is complete |

## 3. Implementation Design

**Overall flow.** When an owner entity is created, its VS node and a **self scope_binding** (owner scope → its own VS)
are created together (Scope Creator). Child entities the owner holds become members of that VS (ownership). When a
hierarchy/association relation is formed, the parent/associated scope is bound to the lower VS at that moment. To share
with another scope, the same entity is added as a member of the target's VS with a `permission_cap` (invitation).
Resolution computes `entity → VS → bound scope → that scope's role permissions` in **one path, one hop**.

### (a) Virtual scope graph and binding scenarios

```
scope(self)     ─(self scope_binding, at creation)─┐
scope(parent)   ─(hierarchy binding, at creation)──┼─► virtual_scope(owner S) ─(entity_memberships)─► entity X, Y
scope(assoc.)   ─(association binding)─────────────┘
```

- One VS per owner scope S (`UNIQUE(scope_type, scope_id)`).
- An entity attaches **only to directly-connected VSs** — its own owner's VS (ownership) and any invitee's VS (invitation). It does not propagate VS→VS (no recursion).
- When a `scope_binding` is created:
  - **self**: at scope creation, bound to its own VS (owner sees its own entities).
  - **hierarchy**: creating a project under a domain → `domain → VS_project`; creating a user → `domain → VS_user`; enrolling a user in a project → `project → VS_user`.
  - **association**: a resource group's agents are members of `VS_resource_group`; binding an associated project via `project → VS_resource_group` lets **the project read those agents.**
- When an `entity_membership` is created:
  - **ownership/enrollment**: an entity becomes a member of its owner's VS. **A user belonging to a project is this too** — the user entity is a member of `VS_project`.
  - **invitation**: a specific entity is added to the invitee's VS with a `permission_cap` (3.(e)).

### (b) Non-recursive single-path resolution (forward/reverse)

Resolution is **one path**, with no self/hierarchy/association/invitation branching.

```
entity → entity_memberships → scope_bindings → scope → permissions → roles → user_roles
```

- Thanks to the self scope_binding, ownership (an owner seeing its own entities) also goes through this one path — no special case.
- The RBAC page's bidirectional lookups are the same two-table join (indexes already in 2.1).

| Direction | Path | Use |
|-----------|------|-----|
| Forward | `scope → scope_bindings → VS → entity_memberships → entities` | "entities this scope can see" |
| Reverse | `entity → entity_memberships → VS → scope_bindings → scopes` | "scopes that grant permission on this entity" |

**No recursion.** Every path is a simple join over two or three tables, with no CTE recursion.

**Ownership/visibility and permission are separate axes.** The VS graph (`scope_bindings` + `entity_memberships`)
decides "who can own/see what" (a user belonging to a project is here too). `roles`/`permissions` decide "which operations
are allowed." Resolution reaches a scope through the VS graph, then applies that scope's role permissions — **combining the two.**
So the enrollment record (association) and the permission grant (`user_roles`) do not overlap; each has its own role.

### (c) Scope Creator — VS + self scope_binding at creation

- **Create:** when an owner entity (domain/project/user/resource_group/...) is made, `create_scope` creates the
  real row + VS node + **self scope_binding** (owner scope → its own VS) together (get-or-create, safe to call repeatedly).
- **Why a self scope_binding:** resolution follows scope_bindings (3.(b)). For an owner to see the entities in its own VS,
  it needs one binding to that VS. Adding that single row at creation lets ownership resolve through the **same one path**
  as hierarchy/association/invitation. (Chosen over adding an owner-only special branch to the query.)
- **Delete:** `delete_scope` drops the VS node, and FK `ON DELETE CASCADE` removes its bindings and memberships.
- **Invariant:** every owner scope has a VS (`_resolve_virtual_scope_id` raises 500 otherwise).
- **Where it wires:** VS writes are owned by the RBAC ops provider's grant method, and the domain/project/user/resource_group
  operations use that provider/ops (2.3). No domain code touches the VS tables directly.

### (d) Expressing hierarchy without recursion

Removing recursion is this BEP's goal, so domain→project→user inheritance is expressed **by bindings at creation time, not recursion.**

- Create hierarchy bindings **when the relation is formed**: domain→project creation, domain→user creation, project→user enrollment.
- A lower entity then reaches a parent scope's permissions **still in one hop** via `entity → lower VS → parent scope binding`.
- Because the hub bounds the connection count, even pre-materialized inheritance keeps bindings at roughly `scope × VS`.

### (e) Association vs Invitation — unified as membership

| Link kind | Meaning | Storage | permission_cap |
|-----------|---------|---------|----------------|
| **Association** (ownership) | children the owner holds | `entity_memberships` on its own owner VS | none (no ceiling) |
| **Invitation** (sharing) | grant a specific target access to a specific entity | `entity_memberships` on the **target's VS** | only what was granted (e.g. read\|write) |

- Invitation is not a separate table or a direct-permission layer — it is **adding that entity as a member of the invitee's VS.**
- The invitee sees entities in its own VS via the self-binding path, so once invited it can read the entity immediately.
- `permission_cap` enforces "only what was granted" — even if the target holds a stronger role in its own scope,
  it is clipped by `role permission & entity_cap`, so **permissions do not leak** (the cap replaces BEP-1048's escalation prevention).

### (f) possible/impossible = a dataclass derived from actions

- Express "which operations are possible on this entity from this scope" as a **dedicated dataclass derived from actions**, exposed as fields.
- **Read and combine** two things:
  1. **Scope reachability** — from scope actions, "can this scope reach this entity?"
  2. **Per-entity operations** — from single-entity actions, "which operations exist on this entity?"
- **Why combine:** a scope action often has only READ, not UPDATE/DELETE. But holding scope permission also grants
  individual access, so an UPDATE/DELETE absent from the scope action but present on the entity's single-entity action
  must still be **included** as a possible operation.
- Route access through this dataclass and remove **both** `VALID_SCOPE_ENTITY_COMBINATIONS` (hand-written) and any separate DB table.
- Prerequisite: actions must be normalized to the 3 RBAC action kinds for the derivation to be complete (2.7).

### (g) Ceilings via permission_cap

- `scope_bindings.permission_cap` and `entity_memberships.permission_cap` are the per-hop ceiling (nullable = no ceiling).
- Effective permission = `role-granted permission & scope_cap & entity_cap` (bitwise AND). Multiple paths OR together.
- `Permission` is an `IntFlag` (READ/UPDATE/CREATE/SOFT_DELETE/HARD_DELETE) — all checks are bitwise.

### (h) Removing auto / ref

- BEP-1048's `RelationType` (auto/ref) distinction **disappears** in the virtual scope model.
- auto (permission delegation) → owner VS membership + (for hierarchy/association) scope_binding.
- ref (read-only reference / invitation) → invitee VS membership + `permission_cap` (3.(e)).
- The `association_scopes_entities.relation_type` column and its branching are dropped after migration.

## 4. Migration / Compatibility

**Direction: replace the recursive scope-walk with the non-recursive virtual scope resolution.** All virtual scope
values are internal, so they can be moved in a single backfill.

| Step | Content |
|------|---------|
| 1. Normalize actions | Bring every domain action to the 3 RBAC action kinds (2.7) — prerequisite for checks/derivation |
| 2. Wire Scope Creator | Put VS writes (including self scope_binding) in the RBAC ops provider's grant method, and have domain/project/user/resource_group operations use that provider/ops (3.(c)). Hierarchy bindings at creation (3.(d)) |
| 3. Move data | Backfill `association_scopes_entities` auto→owner VS membership, ref→invitee VS membership (+cap), and parent inheritance→scope_binding, in one pass |
| 4. Wire resolver | Switch validators to virtual scope resolution (one path). Add forward/reverse lookups |
| 5. Remove recursion | Drop the recursive CTE (`_build_scope_walk_cte`) and the recursive walk path; drop the `relation_type` column |
| 6. Cleanup | Delete `VALID_SCOPE_ENTITY_COMBINATIONS`, replace with the action dataclass (3.(f)). Rename `add_users_to_scope` |

**Separate config (temporary switch).** Virtual scope resolution is toggled by a **new config**, not by reusing
`enforcement_enabled` — "whether to enforce" and "which resolution strategy" are different axes and must be tuned
independently during the transition. This config is a **temporary switch**. The order is
(1) implement/wire virtual scope → (2) backfill migration → (3) flip via the config in one step → (4) after verification,
remove the recursive walk path and this config together. Other transition targets follow the same order.

**Equivalence with the old behavior.**

- Ownership/visibility: moving association to owner VS membership + self binding yields the same result.
- Sharing (invitation): moving ref to invitee VS membership + cap yields the same result (the cap prevents escalation).
- Inheritance: replacing recursion with creation-time hierarchy bindings (one hop) yields the same result.

## 5. Decision Summary

| Decision | Content |
|----------|---------|
| Ownership model | `scope → virtual_scope → entity`, two hops. One hub VS per owner |
| Resolution | **No recursion**, one path. Same join for self/hierarchy/association/invitation. Forward/reverse symmetric |
| Scope Creator | Create VS + **self scope_binding** at owner creation, FK CASCADE on delete. VS writes owned by the RBAC ops provider; domain operations use it |
| Hierarchy bindings | Bound at relation-creation time (domain→project, domain→user, project→user) |
| Association vs Invitation | Both `entity_memberships`. Ownership = owner VS (no cap) / invitation = target VS (cap = granted). No separate direct-permission layer |
| possible/impossible | A dataclass derived from actions (scope reachability + per-entity operations combined), exposed as fields. Removes both the hand-written table and any DB table |
| auto/ref | Removed — replaced by membership (+cap) / scope-binding |
| permission_cap | Per-hop ceiling (bitwise AND); paths OR together. Enforces invitation escalation prevention |
| Resolution toggle | Not `enforcement_enabled` — a **new config**, a temporary switch removed with the recursive walk after cutover |
| Action normalization | Bring all actions to the 3 kinds: Scope/SingleEntity/Bulk |

## 6. Open Questions

None — the major design decisions are settled. Implementation-level details (e.g. the `add_users_to_scope` name,
the list of associations that need bindings, the transition config's name/default) are handled in follow-up issues.

## 7. References

- [BEP-1048: RBAC Entity Relationship Model](BEP-1048-RBAC-entity-relationship-model.md)
- [BEP-1008: RBAC](BEP-1008-RBAC.md), [BEP-1012: RBAC](BEP-1012-RBAC.md)
- [BEP-1056: Scope-Linked Metric Catalog](BEP-1056-scope-linked-metric-catalog.md) (handles read permission via virtual_scope RBAC)
