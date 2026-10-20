---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-08-23
Created-Version: 26.8.0
Target-Version: 
Implemented-Version: 
---

# Entity Lifecycle Deletion Management

## Related Issues

- BA-7026 — Epic
- BA-7030 — this BEP
- BA-6807 — absorbed: user and project purge leave the per-scope RBAC roles behind
- BA-6186 — absorbed: cascading purge of scope-owned roles
- BA-7296 — superseded (Not Planned): moving purge orchestration into a lifecycle manager
- BA-4519 — RBAC creator and purger in the storage proxy lifecycle
- BA-6738 — owner delegation on vfolder purge
- BA-3709 — project soft delete
- BA-7285 — virtual scope RBAC
- BEP-1062 — virtual scope RBAC
- BA-7443 — in flight: moving the user purger into models/
- BA-7444 — in flight: moving the resource_group purger into models/
- BA-7449 — in flight: moving the project purger into models/
- BA-8573 — how the API identifies Nodes and relations (delete response rules)

## Goal

Bring the deletion of `domain`, `project`, `user`, `vfolder`, and `image` under one lifecycle.

Today an owning entity's sub-resources are removed **synchronously, inside the same request**. That is right
for association rows that live only in the DB. It does not hold for a vfolder with real bytes on storage, an
endpoint with proxy routes attached, or a session running on an agent: deleting the DB row does not clean those
up, and the cleanup does not fit in one transaction. The current `user` purge only **marks** sessions for
termination and then deletes the user row, so the owner disappears before its sessions actually end.

This BEP settles four things.

1. Which column holds the business state, the soft delete, and the purge progress
2. The **purge progress state transitions** the five entities share, and what each state means
3. Where the controller, the coordinator, and the per-entity-type handlers sit
4. Who owns **failure handling** and **consistency with external resources**, and the API responses

## Current Design & Scope by Area

For each area, separate **✅ what already exists** from **➕ what to add**.

### 2.1 How deletion state is expressed

|  | Item |
| --- | --- |
| ✅ | `domain`, `project`: an `is_active` boolean and a status enum (`active` / `deleted` / `purging` / `purge-error`). Soft delete writes both |
| ✅ | `user`: `UserStatus` (`active` / `inactive` / `deleted` / `before-verification` / `purging` / `purge-error`). Restore always goes back to `active` |
| ✅ | `image`: `ImageStatus` (`ALIVE` / `DELETED` / `PURGING` / `PURGE_ERROR`). A registry rescan revives `DELETED` rows to `ALIVE` |
| ✅ | `vfolder`: one `VFolderOperationStatus` holds both the business state (`ready` … `error`) and the deletion steps (`delete-pending` → `delete-ongoing` → `delete-complete` / `delete-error`) |
| ✅ | `role`: `status` (`active` / `inactive` / `deleted`) and `deleted_at`. Restore always goes back to `active`. `role_preset`: a `deleted` boolean. `artifact`: `availability` (`ALIVE` / `DELETED`) |
| ✅ | The `purging` and `purge-error` values are defined but nothing writes them. Every purge finishes synchronously inside the request |
| ✅ | All five entities have `restore` |
| ➕ | Split the business state, the soft delete, and the purge progress into three columns (3.1) |
| ➕ | Decide soft delete by one `deleted_at` from a shared mixin |
| ➕ | Add a `purge_status` column to the five entities that clean up external resources |
| ➕ | Remove the deletion values (`deleted`, `purging`, `purge-error`, `delete-*`) from the business status enums. `domain` and `project` drop the status enum and `is_active` |

`user`'s soft delete does not touch keypairs. The authentication gate blocks a deleted user's API access (2.2).

### 2.2 Authentication gate

|  | Item |
| --- | --- |
| ✅ | The login (password) path checks `user.status`. `deleted` is rejected |
| ✅ | The API request path (keypair HMAC, JWT) checks `user.status` (`_AUTH_DENIED_USER_STATUSES`). Inactive, deleted, and purging users are rejected |
| ➕ | The gate checks `deleted_at` and `purge_status`. This lands before the deletion values leave the status |

Reversing the order lets a soft-deleted user keep calling the API with their key.

### 2.3 Sub-resource cleanup

The 29 `BatchPurgerSpec` implementations split into two kinds.

| Kind | Targets | Does today's approach work |
| --- | --- | --- |
| Association and attached rows that live only in the DB | resource_group↔domain/project/keypair associations, group_association, vfolder_permission, vfolder_invitation, error_log, keypair, user_role, session_idle_check, session_group | Yes |
| Rows backed by an external resource | endpoint (proxy routes), routing, session (containers on an agent), vfolder (bytes on storage) | No |

|  | Item |
| --- | --- |
| ✅ | Association-row purgers already work as subquery-based bulk deletes and check preconditions through `conflict_checks` |
| ✅ | Only `user` purge is handled procedurally in the service layer: vfolder mount check, shared vfolder migration, endpoint delegation, session termination marking, vfolder deletion, row purge |
| ➕ | A sub-resource backed by an external resource is driven through **that resource's own shutdown path, and its row is removed only after completion is confirmed**. It is not deleted outright |
| ➕ | Declare the cleanup order per entity and take the procedure out of the service method bodies |

### 2.4 Lifecycle machinery

|  | Item |
| --- | --- |
| ✅ | `sokovan/reconciler`: an entity-agnostic lifecycle coordinator. One tick is fetch → execute → classify → apply → post_process, with per-entity retry, give-up and expiry classification, per-stage metrics, and a valkey needed-flag for immediate startup |
| ✅ | `leader/tasks/retention_sweep.py`: a `PeriodicTask` that runs on the leader only. Single execution is guaranteed by leader election, without a distributed lock |
| ✅ | `common/bgtask`: issues a task id and reports success or failure as an event |
| ✅ | Session termination path: after `mark_sessions_for_termination`, the next tick's handler calls `destroy_kernel`, and completion is confirmed by an agent event |
| ➕ | Remove the session scheduling vocabulary from sokovan's reconciler base. The base stays in sokovan (3.2) |
| ➕ | Build a **deletion-specific lifecycle controller and coordinator** on top of it |

The reconciler base is currently tied to session scheduling vocabulary: `SchedulingResult`, `HandlerPolicyResolver`,
and the dependency on `data/session/options`.

### 2.5 RBAC scopes and roles

|  | Item |
| --- | --- |
| ✅ | `RBACEntityPurgerSpec` / `RBACEntityBatchPurgerSpec`: deleting a row also removes what it left in the RBAC graph |
| ➕ | When purging a scope-owning entity (domain, project, user), cascade through the roles auto-provisioned at that scope and their mappings (BA-6807, BA-6186) |

## Implementation Design

### 3.1 Three columns: business state, soft delete, purge progress

**Deletion is not expressed as a business status value.** The three are kept in three columns.

| Column | What it answers | Reversible | Written by | Where it lives |
| --- | --- | --- | --- | --- |
| `status` | What business state the entity is in | By business rules | The entity's business logic | Entities with a business state. Each entity has its own enum |
| `deleted_at timestamptz NULL` | Whether it is soft-deleted | Yes (`restore`) | Soft delete, restore | Every soft-deletable entity. A shared mixin |
| `purge_status` | Whether a purge is cleaning up external resources, or failed | No | The deletion coordinator | Entities that clean up external resources. A shared mixin |

Business state and deletion hold at the same time. A user can be deleted while `inactive`. Kept in one enum,
restore loses the previous state; today's `user` and `role` restore always returning to `active` is that
result. Kubernetes keeps the deletion request (`metadata.deletionTimestamp`), external cleanup (finalizers), and
business state (`status.phase`) in separate places. AIP-216 does not put states that are not mutually
exclusive in one enum.

### Soft delete: `deleted_at`

- Whether a row is soft-deleted is decided by `deleted_at IS NOT NULL` alone. No boolean with the same meaning is kept beside it.
- `deleted_at` comes from a shared mixin next to `models/mixins/timestamp.py`.
- Soft delete writes `deleted_at = now()` and restore writes `deleted_at = NULL`, as constants. The business `status`
  is not touched, so the previous state remains after restore.
- There is one soft delete updater and one restore updater for rows with this mixin. They are not written per entity.

### Purge progress: `purge_status`

- Only on entities whose row can be removed only after external resources are cleaned up: `user`, `project`, `domain`, `vfolder`, `image`.
- A NOT NULL enum. The default value is named. The values are the default, `purging`, and `purge-error`.
- When `purge_status` is not the default, `deleted_at` must be set. A CHECK constraint enforces it.
- When cleanup finishes, the row is removed. There is no finished-state value.
- An entity with no external cleanup has no `purge_status`, and its purge removes the row inside the request.

The coordinator reads one `purge_status` regardless of entity kind. It does not reconcile per-entity values
(`purging`, `PURGING`, `delete-ongoing`).

### Per entity

| Entity | Business `status` | `deleted_at` | `purge_status` | What changes |
| --- | --- | --- | --- | --- |
| `user` | `active` / `inactive` / `before-verification` | yes | yes (sessions, endpoints, vfolders) | `deleted`, `purging`, `purge-error` leave the status |
| `domain` | none | yes | yes (sessions, RBAC) | The status enum and `is_active` are dropped |
| `project` | none | yes | yes (sessions, endpoints, vfolders) | The status enum and `is_active` are dropped |
| `image` | none | yes | yes (registry untag) | `ImageStatus` is dropped. A registry rescan does not touch `deleted_at` |
| `vfolder` | `ready` … `error` | yes (replaces `delete-pending`) | yes (`delete-ongoing` → `purging`, `delete-error` → `purge-error`) | `delete-complete` is dropped |
| `role` | `active` / `inactive` | yes (already present) | no | `deleted` leaves the status |
| `artifact` | none | yes (replaces `availability`) | no | `availability` is dropped |
| `role_preset` | none | yes (replaces `deleted`) | no | `deleted` is dropped |
| session, kernel, deployment, route | execution lifecycle unchanged | no | no | none |
| keypair, resource group, container registry, storage namespace | `is_active` is a business on/off value | no | no | none. Purged without soft delete |
| error log | `is_cleared` is an acknowledgement | no | no | none |

A lifecycle that ends in a status transition is not a soft delete. A session's `TERMINATED` and a deployment's
`DESTROYED` record that execution ended and are not reversed. Retention removes those rows.

### Read rules

| Read | Soft-deleted rows |
| --- | --- |
| Lists (search, scoped search) | Excluded by default. Included through a `deletedAt` filter condition |
| Single reads (get, `node(id:)`, bulk data loader) | Returned |
| Permissions | Soft delete keeps the permission edges. Purge removes them |
| Name unique constraints | Partial indexes `WHERE deleted_at IS NULL`. A restore after a new row took the same name is an integrity error that `integrity_error_checks` maps to a domain error |

### Transitions

While `purge_status` is `purging` or `purge-error`, `delete`, `restore`, and `update` on that entity are rejected.
Something being cleaned up cannot be revived or edited. The only way out of `purge-error` is `force purge` (3.5).

| Transition | Trigger |
| --- | --- |
| `deleted_at`: NULL → timestamp | `delete` request |
| `deleted_at`: timestamp → NULL | `restore` request |
| `purge_status`: default → `purging` | `purge` request (`deleted_at` must be set) |
| row removed | cleanup complete |
| `purge_status`: `purging` → `purge-error` | retries exhausted |
| row removed | `force purge` request (3.5) |

### 3.2 The reconciler base stays in sokovan

The generic ABCs in `sokovan/reconciler` are not moved to `manager/reconciler`. Sokovan is being widened into
tick-based entity lifecycle at large with the deletion lifecycle inside it, so there is no reason to lift the
base out of sokovan (BA-7453).

The deletion coordinator inherits that base from inside sokovan. The changes the base itself needs still stand.

| Item | Change |
| --- | --- |
| `SchedulingResult` | Generalized to a neutral name unrelated to scheduling. Not renamed into deletion vocabulary; scheduling could not use it then |
| `HandlerPolicyResolver` (from `data/session/options`) | Narrowed to an interface supplying retry counts and timeouts, and moved to the base |
| `ReconcilerStageMetadata.transitions` | Success on the last stage must be able to mean **row removal**, not a status transition |
| `LockID` and the distributed lock | Unchanged. Stages that run without a lock stay allowed |
| `ReconcilerMetricObserver` | Unchanged. The labels carry which machinery it is |

Since `transitions` is bound to a single status type, **there is one stage, one reconcile type, and one task
spec per entity kind**. Per-kind failure isolation and per-kind cadence come with that.

History follows sokovan too: `ReconcileHistoryMixin` per entity kind, with the FK on that entity. Attempts, the
phases passed through, and the last error live there.

### 3.3 Controller and coordinator

The request side and the tick side are different things. This follows sokovan's split.

|  | Lifecycle controller | Lifecycle coordinator |
| --- | --- | --- |
| Called by | Services, during request handling | The tick (event or periodic) |
| What it does | Checks the transition is legal, moves `purge_status` to `purging`, and sets the needed-flag | Reads entities whose `purge_status` is `purging` and advances the handler one step |
| Prior art | `RouteController`: a single method | `ReconcilerCoordinator`, `RouteCoordinator` |

**There is one of each, not one per entity.** The handler is the only thing that varies per entity.

- `delete` and `restore` are already generalized. `DeleteSingleEntityOpsAction` and `RestoreSingleEntityOpsAction`
  are shared bases taking a single updater.
- Purge options are all resolved inside the DB at request time. `delegate_endpoint_ownership`, `purge_shared_vfolders`,
  and `cascade_model_card` transfer ownership or drop referencing rows, and touch no external resource.

All the coordinator asks a handler is to **advance one step and report in progress, done, or failed**.
Deletion vocabulary stays out of the coordinator contract.

There is one handler per `EntityType`, and it answers two things.

| What the handler answers | Example for `user` |
| --- | --- |
| The list of cleanup stages | sessions → endpoints → vfolders → association rows → RBAC roles and scope |
| How the entity row is removed | The existing `RBACEntityBatchPurger` |

**Stage registration declares which entities ride this machinery.** There are three cases.

|  | Behavior |
| --- | --- |
| A stage is registered | The purge request moves `purge_status` and the tick advances it |
| No stage is registered | Unchanged. The request finishes inline through the existing purger |
| Declared as riding it, but no handler | A wiring error. The request is rejected |

An unregistered entity is not treated as "just delete the row". More than ten entities declare
`ActionOperationType.PURGE` while five ride this machinery. Defaulting to a row delete would let the rest pass
through silently doing no cleanup, with no way to tell a missing registration from having nothing to clean.

A handler with no cleanup stages is allowed. It finishes with the row delete on the first tick, and that is the
declared intent. A mismatch between the declaration and handler registration is caught by the registry sweep test.

There are two ways it starts.

| Start | Guaranteed | Role |
| --- | --- | --- |
| Long tick | Yes | Picks up whatever is in progress. Correctness comes from here |
| needed-flag | No | Brings the first step forward, right after the `purge` request |

Progress lives on the entity row, so nothing is held between ticks. If the request drops or the manager
restarts, the next long tick picks it up. `post_process` does not run when `apply` raises, so nothing that
carries progress forward is put there.

### 3.4 The cleanup stage contract

A stage answers three things.

| Slot | Example for the session stage |
| --- | --- |
| Is anything not yet terminal | Any session outside `SessionStatus.terminal_statuses()` |
| Drive it terminal (idempotent) | `mark_sessions_for_termination` |
| Remove what is terminal | The existing purger. Kernel rows first, in order |

Each tick the coordinator walks the stages in order. If the first slot is not empty it triggers the second and
ends the tick. If it is empty it runs the third and moves to the next stage. When the last stage finishes, the
entity row is removed.

These three slots are a helper shared by the deletion handlers, not the coordinator contract. The general form
is **is anything different from the goal / push it toward the goal / finalize what arrived**, and the
terminal-based form is its deletion specialization.

Retry and give-up are handled by the base. `ReconcilerStage._classify_outcome` accumulates attempts only while
`last.phase` matches, so **using the stage name as the phase** makes a stage that lingers register as a
give-up, and resets the count once it moves on.

Terminal states are already defined per resource.

| Resource | Terminal |
| --- | --- |
| session, kernel | `SessionStatus.terminal_statuses()`, `KernelStatus.terminal_statuses()` |
| routing, replica group | `RouteStatus.terminal_statuses()`, `ReplicaGroupLifecycle.terminal_statuses()` |
| endpoint | `EndpointLifecycle.DESTROYED` |

Association and attached rows that live only in the DB always have an empty first slot and only the third.
One contract covers both kinds.

**When a sub-resource is itself a managed entity, the owner does not delete it directly.** The owner's stage
asks in the first slot whether any of those rows remain, and in the second slot moves their `purge_status` to
`purging`. Once they are gone, the stage passes on a later tick. The owner's `purge` invokes the sub-entity's
`purge`, not its `delete`, so the sub-entity skips soft delete and has `deleted_at` and `purge_status` written
together.

**Kernels never appear directly in any entity's cleanup stages.** Kernel rows are removed by the session stage,
ahead of the sessions. Owning entities name sessions only.

| Entity | Cleanup order |
| --- | --- |
| `user` | sessions → endpoints released or delegated → vfolders → association and attached rows → RBAC roles and scope |
| `project` | sessions → endpoints released → project vfolders → association rows → RBAC roles and scope |
| `domain` | sessions → association rows → RBAC roles and scope |
| `vfolder` | invitations and permissions → storage deletion |
| `image` | registry untag (only where the registry needs it) → aliases |

Each stage states for itself which column it selects targets by. Sessions are reached through `domain_id`,
`group_id`, and `user_uuid` respectively.

Rejection conditions keep using today's `conflict_checks`. What changes is when they are evaluated: at
**stage execution** rather than at request time.

The registry untag runs only where the registry type requires it and is skipped elsewhere, never rejected.
Untag is currently implemented for Harbor 2 only.

`image`'s `purge_image` and `purge_images` reclaim agent disk space and are not entity deletion. This BEP
covers the row-removing side.

### 3.5 Force purge

An escape hatch that removes the row immediately without waiting for cleanup, **on all five entities**.

|  | Default purge | Force purge |
| --- | --- | --- |
| `purge_status` | Moved to `purging` | Untouched |
| Sub-resource DB rows | Removed stage by stage, with confirmation | Removed all at once |
| External resources | Cleanup requested and completion confirmed | Cleanup is **requested but never confirmed** |
| Entity row | Removed after the last stage | Removed immediately |
| Soft delete first | Required | Not required |

Whether the external resources were actually cleaned up is not guaranteed. That is why it is not the default.

Today's synchronous purge is exactly this behavior. The current code moves onto the force path as-is, and what
is newly built is the default path that runs behind the request.

**Permissions match `purge`.** A caller who can request a purge can request a force purge. Force purge is also
the way to retry from `purge-error`; no separate retry API is added.

### 3.6 Consistency with external resources

**The manager orchestrates.** A cleanup stage owns the storage-proxy, appproxy, and agent calls directly and
confirms their result before moving to the next stage. Having each component clean up its own resources and
report back by event is not adopted: vfolder deletion and session termination are already manager-orchestrated,
and this avoids standing up a new cleanup loop in each component.

Sessions are the one exception, riding their existing termination path. The manager marks termination and the
agent confirms by event, so the cleanup stage only observes that confirmation in its first slot.

The window where the DB row and the external resource disagree cannot be eliminated. For as long as it lasts,
`purge_status` reads `purging` and retries continue; exhausting them surfaces as `purge-error`.

### 3.7 API

| Operation | Today | After |
| --- | --- | --- |
| `delete` | `is_active=False` and status for domain and project, status for user and image | All five write `deleted_at` |
| `restore` | On all five. Resets the business state to the default | Clears `deleted_at` only. The business state stays. Allowed only from the soft-deleted state |
| `purge` | Cleans everything synchronously and answers on completion | v2 does not wait (below). The existing APIs wait for completion |
| `force purge` | Only on vfolder (`force_delete`) | All five. Permissions match `purge` |

### v2 purge responses

Whether the Node still exists at response time decides the response shape. Which case applies is decided by
whether the entity has `purge_status`; the same entity's purge does not answer differently case by case.

| Item | Synchronous purge (no `purge_status`) | Asynchronous purge (`purge_status`) |
| --- | --- | --- |
| What the request does | Finishes through the row removal | Moves `purge_status` to `purging` and returns. The coordinator advances the cleanup on each tick |
| GQL response | `purgedId: ID!` and `entityId` or `fieldId` | The Node (`purgeStatus: PURGING`). No `purgedId` |
| REST response | 200, the UUID | 202 Accepted, the entity |
| Client store | Applies `@deleteEdge` and `@deleteRecord` to the response's `purgedId` | Updates the Node from the response. The record is not removed yet |
| Completion check | Not needed | Done when `node(id:)` returns null |
| Failure | The request ends in an error | `purgeStatus: PURGE_ERROR` on the same Node |
| Other requests while in progress | n/a | update, delete, and restore return 409. A repeated purge returns the same Node |
| Force purge | n/a | Synchronous. GQL returns `purgedId`, REST and the DTO return the UUID |

- Only the GQL layer builds global IDs. Pydantic DTOs carry UUIDs only.
- `purgedId` is the global ID that Relay's `@deleteEdge` and `@deleteRecord` take. It is returned only when the row is actually gone.
- When a row leaves a list needs no handling. Purge comes after soft delete, and soft-deleted rows are already
  out of the default lists.

### Synchronous contract of the existing APIs

**The synchronous contract of the existing APIs (v1, legacy GQL) does not change.** The handler moves the
transition through the controller, subscribes to that entity's cleanup completion, waits, and answers.

**The wait exists only in this API handler.** It is there to honor the existing callers' response contract;
there is no waiting in the controller, the coordinator, or any cleanup stage. Cleanup advances one step per
tick, and the tick ends when that step does. The next step is carried by the next tick.

The wait is bounded at **five minutes**. Stages such as confirming session termination span several ticks and
may not finish within it. Past the bound the request answers with a timeout, but **cleanup keeps running**.

Completion is subscribed through `common/bgtask`'s completion event. A task id for clients to subscribe to
directly is not exposed.

`deletedAt` and `purgeStatus` are exposed as fields on the entity. No join is needed, and their values appear
only in that entity type's schema.

### 3.8 Cascading RBAC scopes and roles

When a scope-owning entity is purged, the roles auto-provisioned at that scope and their user mappings are
removed as one stage of the same flow (absorbing BA-6807 and BA-6186). This touches BEP-1062's virtual scope
work, so the ownership definition of a role follows BEP-1062 and this BEP settles only **when** the cleanup
happens.

### 4. Migration and Compatibility

### Breaking changes

| Item | Effect |
| --- | --- |
| Deletion values removed from business status | Not stored in the DB. The existing APIs' status field exposes a value computed by laying `deleted_at` and `purge_status` over the business status, and is deprecated. New fields `deletedAt` and `purgeStatus` are added |
| v2 `purge` response | An entity with `purge_status` answers without waiting, with the Node (GQL) or 202 (REST) |
| Existing API `purge` response time | The contract is the same, but past five minutes it answers with a timeout. Callers assuming completion must handle that case |
| Business state after `restore` | Not reset to the default; the previous state remains |
| vfolder `delete-complete` | Goes away. Cleanup completion is the row removal |
| `is_active` on `domain`, `project` | Kept as a read-only value derived from `deleted_at`, then dropped after callers move |

### Migration

1. Add `deleted_at` through the shared mixin and fill it from the business status's deletion values. Rows already
  deleted have no known previous business state, so their business status moves to the default (`active`, `ready`).
2. Add `purge_status` to the five entities and fill it with the default. vfolder's `delete-ongoing` moves to
  `purging` and `delete-error` to `purge-error`. Add a reconcile history table per entity kind.
3. Make the authentication gate check `deleted_at` and `purge_status` before the deletion values leave the status.
  **Reversing the order lets a soft-deleted user keep calling the API with their key.**
4. Drive vfolder rows left at `delete-complete` through cleanup to remove them. vfolder's `performing`, `cloning`,
  and `mounted` sitting in the same enum are out of this BEP's scope.
5. Move callers reading `is_active` and the status deletion values onto `deleted_at` and `purge_status`, then drop them.

A defect found during the survey: the vfolder deletion failure event does not reach rows in `delete-ongoing`, so
`delete-error` is never written (`update_vfolder_status` in `repositories/vfolder/deletion.py` updates only
rows in `delete-pending`). It is fixed together with the move to `purge_status`.

### Work in flight

The purger move into `models/` in BA-7443, BA-7444, and BA-7449 **continues as planned**. Of the 29, the
association-row purgers keep the same shape after the move, so it is not rework. Only the purgers backed by an
external resource relocate into this BEP's cleanup stages.

### 5. Implementation Plan

| Step | Content |
| --- | --- |
| 1 | Build the shared `deleted_at` mixin and the soft delete and restore updaters, and move the entities onto them. Remove the deletion values from the business status and expose the existing APIs' status as a derived value |
| 2 | Make the authentication gate check `deleted_at` and `purge_status`. Lands before the status cleanup in step 1 |
| 3 | Move today's synchronous purge onto `force purge` and open it on all five entities. Behavior is unchanged |
| 4 | Split the scheduling vocabulary out of sokovan's reconciler base. The base stays in sokovan |
| 5 | Add `purge_status` and the history tables to the five entities |
| 6 | Build the controller, the coordinator, the cleanup stage contract, and the registry sweep test. Validate the flow on the `domain` handler, which has the shortest stage list |
| 7 | Attach the `vfolder`, `image`, `project`, and `user` handlers and remove the procedural code from the services |
| 8 | Add the cascading RBAC role and scope stage (BA-6807, BA-6186) |
| 9 | Switch v2 purge to the asynchronous response (Node, 202), and switch the existing APIs' purge handler to subscribing for completion |
| 10 | Move callers of `is_active` and the status deletion values, then drop them |

## Decision Summary

| ID | Date | Decision | Rationale | Alternatives Considered |
| --- | --- | --- | --- | --- |
| D1 | 2026-10-20 | Split business state (`status`), soft delete (`deleted_at`), and purge progress (`purge_status`) into three columns. The business status carries no deletion values. | Business state and deletion hold at the same time, and one enum makes restore lose the previous state. The coordinator reads one `purge_status` regardless of entity. | One status enum per entity carrying the deletion and purge progress values (this BEP's previous design). |
| D2 | 2026-10-20 | Soft delete is decided by one nullable `deleted_at`, added by a shared mixin. | The deletion time is the retention reference. A boolean kept beside it can disagree with it. | A `deleted` boolean; both a boolean and a timestamp. |
| D3 | 2026-10-20 | `purge_status` is a NOT NULL enum with a named default, only on entities that clean up external resources. | Without a name for the everyday value, a row in the normal state cannot be told apart. | A nullable `purge_status`. |
| D4 | 2026-10-20 | v2 purge of an entity with `purge_status` answers without waiting, with the Node (GQL) or 202 and the entity (REST). Entities without it and force purge answer synchronously with `purgedId` (GQL) or the UUID. | A response does not report a Node that still exists as deleted. `purgedId` removes a record from the Relay store, so it is returned only when the row is gone. | v2 also waits for completion and answers with `purgedId`. |
| D5 | 2026-10-20 | The field of a purge response holding the removed target's global ID is `purgedId`, for an entity, a field row and a relation alike. | Here delete is a soft delete (`deleted_at`), and a soft delete response returns the Node. The field's verb matches the mutation's verb, `purge`. | `deletedId` — collides with soft delete. A name per type (`purgedRoleId`) — clients handle a different field per payload. |

## Open Questions

| ID | Question |
| --- | --- |
| Q1 | The name of `purge_status`'s default value. |

## References

- [BEP-1062](BEP-1062-virtual-scope-rbac.md): Virtual Scope RBAC Ownership Model. Ownership definition of a role
- [BEP-1063](BEP-1063-db-record-retention.md): DB Record Retention Management. Prior art for the LeaderCron periodic sweep
- [BEP-1054](BEP-1054-reconciler-based-idle-checker.md): Reconciler Based Idle Checker. Prior art for consuming the reconciler base
- [BEP-1061](BEP-1061-agent-kernel-lifecycle.md): Agent Kernel Lifecycle Structuring. The kernel termination confirmation path
- [Kubernetes Finalizers](https://kubernetes.io/docs/concepts/overview/working-with-objects/finalizers/): separation of the deletion request, external cleanup, and business state
- [AIP-164 Soft delete](https://google.aip.dev/164), [AIP-216 States](https://google.aip.dev/216)

<!-- generated by hejo bep render from hejo report bep/entity-lifecycle-deletion (sha256 b9c917b892c57d87); edit the source, or hejo bep import after editing here -->
