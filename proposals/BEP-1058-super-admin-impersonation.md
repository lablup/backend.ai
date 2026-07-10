---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-07-08
Created-Version:
Target-Version:
Implemented-Version:
---

# Super-Admin User Impersonation

## Related Issues

- JIRA: BA-6779 (this BEP)
- Epic: BA-6778 — Super-admin impersonation: separate the trigger identity from the effective-user permission subject

## 1. Goal

Let a super admin **trigger** an operation while that operation **executes under a target user's permission context** — only what that user could do is allowed. At the same time, the audit trail records **both actors**: the super admin who triggered it and the identity it actually ran as.

Use cases: support/debugging (faithfully reproducing "why can't this user do X"), permission verification.

## 2. Motivation

Today Backend.AI treats the **authenticated requester** and the **permission-evaluation subject** as a single identity. `current_user()` is one `ContextVar[UserData]`, populated by the auth middleware from a single keypair. A super admin therefore has no way to reproduce an operation from a given user's viewpoint: they either pass unconditionally via the RBAC bypass (`if user.is_superadmin: return`), or use `owner_access_key` to run **with their own authority** — never **with the target's authority**.

## 3. Current State & Scope, by Area

For each area, separate **✅ what already exists** from **➕ what to add**.

### 3.1 Identity context

| | Item |
|---|---|
| ✅ | A single `current_user() -> UserData \| None` (`common/contexts/user.py`), fields: user_id / is_authorized / is_admin / is_superadmin / role / domain_name |
| ✅ | The only writer: auth middleware `_setup_user_context` (`manager/api/rest/middleware/auth.py`) → `with_user(UserData(...))` |
| ➕ | A dedicated **trigger-user** accessor `triggered_user()` + `with_triggered_user()` (separate ContextVar) |

### 3.2 Auth middleware / impersonation signal

| | Item |
|---|---|
| ✅ | Global middleware authenticates via HMAC / JWT / hook, then pushes the context in `_setup_user_context` |
| ✅ | The existing delegation signal `owner_access_key` is a **request body/query parameter** (handled per-endpoint, only on the session/vfolder/model-serving families) |
| ➕ | A new impersonation signal `X-BackendAI-Act-As` **HTTP header** (target UUID), resolved globally in the middleware right after authentication |

### 3.3 RBAC enforcement

| | Item |
|---|---|
| ✅ | Validators such as `ScopeActionRBACValidator` read `current_user()` and short-circuit with `if user.is_superadmin: return` (`actions/validators/rbac/{scope,single_entity,bulk,legacy}.py`, `auth_validator.py`) |
| ✅ | Scoping: many adapters/resolvers/services/repos use `current_user()` as the "my" scope |
| ➕ | **No code change.** Because `current_user()` points at the target while impersonating, enforcement and scoping become target-based automatically (4.3) |

### 3.4 Attribution

| | Item |
|---|---|
| ✅ | The audit `audit_logs` actor is a **single nullable column** `triggered_by` = `current_user().user_id` (`actions/monitors/audit_log.py`, `models/audit_log/row.py`) |
| ✅ | Session-owner stamping: `assign_user_identity_rule.py` sets the session owner uuid from `current_user()` |
| ✅ | Event propagation: `common/events/dispatcher.py` re-injects `current_user()` into async handlers |
| ➕ | Add a **nullable** `acted_as` column to `audit_logs` and redefine the meaning of `triggered_by` (4.5) |
| ➕ | The event dispatcher also propagates `triggered_user()` (background-audit consistency) |

### 3.5 Existing delegation (owner_access_key)

| | Item |
|---|---|
| ✅ | `resolve_access_key_scope` and `query_userinfo(query_on_behalf_of=...)` fill only the **policy context (resource allocation, etc.)** from the target. The permission-evaluation subject stays the requester, and so does the audit (`manager/utils.py`, `services/auth`) |
| ✅ | The eligibility check `check_if_requester_is_eligible_to_act_as_target_user` performs a role/domain check in the **service-validator layer** |
| ➕ | **Coexists** with impersonation. owner_access_key delegates only policy; this work delegates the acting user itself — the delegation target differs (4.4) |

## 4. Proposed Design

### 4.1 Two-identity context model

Carry two identities in the context.

| Identity | Meaning | Accessor | Normal request | Impersonation |
|----------|---------|----------|----------------|---------------|
| **Effective (acting) user** | Subject of permission and scope; every existing operation keys off this | `current_user()` (kept) | = authenticated | = target |
| **Trigger user** | The authenticated caller | `triggered_user()` (new) | = authenticated | = super admin |

Core contract: **every existing operation runs solely off the effective user.** Since that user is exactly what `current_user()` holds, the existing call sites (dozens of adapters/resolvers/services/repos/RBAC) are **left unchanged**. The two identities point at the same `UserData` in a normal request and diverge only under impersonation.

```python
# common/contexts/user.py — accessor contract (details in the PR)
def current_user() -> UserData | None: ...          # existing: effective (acting) subject
def triggered_user() -> UserData | None: ...          # new: trigger (requesting) subject
def with_triggered_user(user: UserData) -> ...: ...   # new context manager
```

> Naming note: `current_user` means "the current authorization/scope subject" = the effective user, **not** "the caller"; make this explicit in the docstring. (Rename considered — see Decision Log.)

### 4.2 Impersonation signal & middleware ordering

- Signal: the `X-BackendAI-Act-As: <target user UUID>` header. **UUID only** (no convenience identifiers). Being a transport-level signal, it works uniformly across REST v2 and GraphQL and changes no DTO.
- Placement: the **middleware right after user authentication is confirmed**. Because it applies globally, the whole request runs as the target (fail-closed) — no endpoint can leak the super admin's authority.

Middleware ordering (contract):

```
authenticate (HMAC/JWT/hook) → resolve Act-As
  ├ no header  : current_user = triggered_user = authenticated
  └ header set : verify the authenticated caller is superadmin → load target UserData (DB)
                 current_user = target,  triggered_user = authenticated
→ push with_user(current) + with_triggered_user(trigger) → handler
```

- Not superadmin / target not found → reject the request (4.6).

### 4.3 Permission & scope semantics (why the change is minimal)

While impersonating, `current_user()` holds the target's **full `UserData`** (target's role, is_superadmin, domain_name). Therefore:

- The RBAC bypass `if user.is_superadmin: return` is evaluated against the target → if the target is a regular user the bypass disappears and the operation is **constrained to the target's scope-chain permissions** (exactly the intended semantics).
- **`my_*` self-service operations** (e.g. `my_keypairs`, `my_user_v2`) resolve the "my" scope internally via `current_user()`, so under impersonation they operate **on the actor (target) for both reads and writes** → the super admin sees and manipulates the target's screens/resources. When the super admin's own identity is needed, use `triggered_user()`.
- GraphQL `me`/viewer also returns the target (the super admin reproduces the target's viewpoint).

All of this holds by swapping the context value alone; no existing call site — `my_*` included — is modified.

### 4.4 Relationship to owner_access_key

The two mechanisms **delegate different things**. They coexist.

| | Delegation target | Permission subject | Applies via |
|---|-------------------|--------------------|-------------|
| `owner_access_key` | **policy** (resource allocation, etc.) | the requester (super admin), unchanged | per-request parameter |
| impersonation | **the acting user itself** | the target | globally (context) |

- **Do not integrate them.** owner_access_key runs with the requester's authority and merely borrows the target's policy — a distinct operation; this work switches the executing subject itself.
- **They coexist without any special rejection.** While impersonating, `current_user()` is the target, so an accompanying `owner_access_key` is evaluated against the **target's** authority. A regular-user target cannot delegate via owner_access_key (the existing service-validator `check_if_requester_is_eligible_to_act_as_target_user` already forbids it), so the combination is bounded by RBAC exactly like every other operation — no dedicated middleware/handler check is needed.

### 4.5 Audit model

Add one nullable `acted_as` column to `audit_logs` and split the actor record.

| Column | Meaning | Normal request | Impersonation | System trigger |
|--------|---------|----------------|---------------|----------------|
| `triggered_by` (existing, nullable, behavior unchanged) | The person who triggered the request = `triggered_user()` | authenticated | super admin | NULL |
| `acted_as` (new, nullable) | The identity it actually ran as = `current_user()` | authenticated (= triggered_by) | target | NULL |

- The audit monitor reads `triggered_by` from `triggered_user()` and `acted_as` from `current_user()` — a change in one place, `audit_log.py`. The logic that fills `triggered_by` stays as-is.
- `acted_as` is **nullable** because `current_user()` is absent in system-triggered contexts (background tasks / system-initiated actions with no user in context), exactly as `triggered_by` already is.
- No new correlation id; reuse the existing `request_id` (BEP-1035).

### 4.6 Eligibility (who may impersonate)

- **Superadmin only.** The middleware checks `triggered_user().is_superadmin` only.
- Domain admins are not allowed — the domain-scope check lives in the RBAC/service-validator layer, whereas act-as is decided in the middleware layer, so the layers differ. (This is also why owner_access_key's `check_if_requester_is_eligible_to_act_as_target_user` is not reused.)

## 5. Migration / Compatibility

- **Backward compatibility:** without the header, `triggered_user() == current_user()`, so `triggered_by` and `acted_as` hold the same value. Existing behavior and audit meaning are unchanged.
- **DB:** add the `audit_logs.acted_as` nullable column (Alembic). **Backfill existing rows from `triggered_by`** (historically caller == effective); rows with no `triggered_by` (system triggers) stay NULL. Keep migrations idempotent when backporting (`alembic/README.md`).
- **No breaking changes.** The new accessor and header are additive; only the audit column is a schema change.

## 6. Implementation Plan

1. **Context + middleware:** add `triggered_user()`/`with_triggered_user()` and clarify the `current_user` docstring (common); resolve `X-BackendAI-Act-As` (UUID) — in the middleware after authentication, check `is_superadmin` → load target UserData → push both contexts. (The header handling itself is small.)
2. **Event-dispatcher propagation:** `common/events/dispatcher.py` propagates `triggered_user()` alongside `current_user()` into async handlers / background tasks (audit consistency for background work triggered during impersonation).
3. **Audit:** the `acted_as` nullable column (Alembic, backfill existing rows) + the monitor recording `triggered_by`/`acted_as` separately.
4. **Verification:** on a live server, confirm that a super admin impersonating a regular user is constrained to the target's permissions and that the audit records both actors (admin/non-admin).

## 7. Decision Summary

| Decision | Content |
|----------|---------|
| Identity model | Keep `current_user()` = effective (acting); add `triggered_user()` = trigger (requesting). Existing call sites unchanged |
| Signal | `X-BackendAI-Act-As` header (UUID only), resolved globally in the middleware after authentication (fail-closed) |
| Permission semantics | While impersonating, `current_user()` = target's full UserData → RBAC bypass, scoping, and `my_*` all become actor-based automatically |
| Eligibility | Superadmin only (middleware checks is_superadmin). Domain admins not allowed (different layer) |
| owner_access_key | Coexist. Policy delegation vs. acting-user delegation — different delegation target. No special handling: under impersonation an accompanying owner_access_key is bounded by the target's RBAC authority |
| Audit | `triggered_by` (existing, behavior unchanged) = trigger; new nullable `acted_as` = effective user (backfill existing rows; NULL for system triggers) |
| Read/write | Impersonation is actor(target)-based for **both reads and writes**, `my_*` included; writes allowed within the target's permissions (bounded by RBAC) |
| Correlation | Reuse existing `request_id`; no new id |

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-07-08 | Trigger accessor named `triggered_user()` (not `request_user`) | Aligns with the audit column `triggered_by` |
| 2026-07-08 | Keep the `current_user()` name (rename deferred) | Renaming to `acting_user()` would be a repo-wide mechanical change, conflicting with the "minimal, 3-chunk" implementation intent. Can be renamed later if desired |
| 2026-07-08 | `acted_as` is nullable | `current_user()` is absent in system-triggered contexts (no user in context), so `acted_as` must allow NULL, mirroring `triggered_by`. Backfill existing rows from `triggered_by` |
| 2026-07-08 | Eligibility is superadmin only | Allowing domain admins needs a domain-scope check (RBAC/service-validator), but act-as is decided in the middleware layer — different layers |
| 2026-07-08 | Impersonation is actor(target)-based for both reads and writes | Natural since it is scoped through the single `current_user()`; writes allowed within the target's permissions |
| 2026-07-08 | Drop the "reject when `X-BackendAI-Act-As` and `owner_access_key` are both set" rule | Under impersonation `current_user()` is the target, so an accompanying owner_access_key is already evaluated against the target's authority and bounded by RBAC (a regular-user target cannot delegate). A dedicated rejection was redundant and forced the middleware/handlers to know about a per-endpoint parameter |

## 8. Open Questions

- (none)

## 9. References

- [BEP-1008: RBAC](BEP-1008-RBAC.md), [BEP-1048: RBAC Entity Relationship Model](BEP-1048-RBAC-entity-relationship-model.md) — permission evaluation, scope chain
- [BEP-1035: Distributed Request ID Propagation](BEP-1035-request-id-tracing.md) — actor/request tracing
- Prior art (existing delegation): `manager/utils.py`, `services/auth` `resolve_access_key_scope`, `query_userinfo(query_on_behalf_of=...)`
