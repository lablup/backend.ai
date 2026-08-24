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

- Epic **BA-7026**, this BEP **BA-7030**
- Absorbs: **BA-6807** (user/project purge leaves the per-scope RBAC roles behind), **BA-6186** (cascading purge of scope-owned roles)
- Supersedes: **BA-7296** (Not Planned) — the direction to move purge orchestration into a lifecycle manager
- Related: **BA-4519** (RBAC creator/purger in the storage proxy lifecycle), **BA-6738** (owner delegation on vfolder purge), **BA-3709** (project soft delete), **BA-7285** / [BEP-1062](BEP-1062-virtual-scope-rbac.md) (virtual scope RBAC)
- In flight: **BA-7443** (user), **BA-7444** (resource_group), **BA-7449** (project) — moving purgers into `models/`

## 1. Goal

Bring the deletion of `domain`, `project`, `user`, `vfolder`, and `image` under one lifecycle.

Today an owning entity's sub-resources are removed **synchronously, inside the same request**. That is right for association rows that live only in the DB. It does not hold for a vfolder with real bytes on storage, an endpoint with proxy routes attached, or a session running on an agent: deleting the DB row does not clean those up, and the cleanup does not fit in one transaction. The current `user` purge only **marks** sessions for termination and then deletes the user row, so the owner disappears before its sessions actually die.

This BEP settles three things.

1. The **deletion state transitions** the five entities share, and what each state means
2. **Where that state is stored**, and where the controller, coordinator, and per-entity-type handlers sit
3. Who owns **failure handling** and **consistency with external resources**

## 2. Current State & Scope, by Area

For each area, separate **✅ what already exists** from **➕ what to add**.

### 2.1 How deletion state is expressed

| | Item |
|---|---|
| ✅ | `domain`, `project` — an `is_active` boolean. Delete sets `is_active=False` through `DomainSoftDeleteUpdater`; restore does the reverse |
| ✅ | `user` — `UserStatus` (`ACTIVE` / `INACTIVE` / `DELETED` / `BEFORE_VERIFICATION`) |
| ✅ | `image` — `ImageStatus` (`ALIVE` / `DELETED`). `forget` sets `DELETED`, `purge_image_by_id` removes the row |
| ✅ | `vfolder` — `VFolderOperationStatus` is the only multi-step one: `DELETE_PENDING` → `DELETE_ONGOING` → `DELETE_COMPLETE` / `DELETE_ERROR` |
| ✅ | `restore` — only on `domain`, `project`, and `vfolder` |
| ➕ | Open `restore` on all five entities |
| ➕ | Add the cleanup-progress values (`purging`, `purge-error`) to each entity's one status enum |
| ➕ | Introduce a status enum on `domain` and `project`. A boolean cannot name its default value |

Only `user`'s soft delete is more than a state transition — it also deactivates every keypair the user owns. That is also why `user` has no `restore`.

### 2.2 Authentication gate

| | Item |
|---|---|
| ✅ | The login (password) path checks `user.status`. `DELETED` is rejected |
| ✅ | The API request path (keypair HMAC / JWT) checks **only `KeyPairRow.is_active`**. It never reads `user.status` |
| ➕ | Add a `user.status` gate to the credential lookup on the API request path |

This has to land before soft delete stops touching keypairs. Keypair deactivation is currently the **only** thing blocking a soft-deleted user's API access.

### 2.3 Sub-resource cleanup

The 29 `BatchPurgerSpec` implementations split into two kinds.

| Kind | Targets | Does today's approach work |
|---|---|---|
| Association and attached rows that live only in the DB | resource_group↔domain/project/keypair associations, group_association, vfolder_permission, vfolder_invitation, error_log, keypair, user_role, session_idle_check, session_group | Yes |
| Rows backed by an external resource | endpoint (proxy routes), routing, session (containers on an agent), vfolder (bytes on storage) | No |

| | Item |
|---|---|
| ✅ | Association-row purgers already work as subquery-based bulk deletes and check preconditions through `conflict_checks` |
| ✅ | Only `user` purge is handled procedurally in the service layer — vfolder mount check, shared vfolder migration, endpoint delegation, session termination marking, vfolder deletion, row purge |
| ➕ | A sub-resource backed by an external resource is driven through **that resource's own shutdown path, and its row is removed only after completion is confirmed** — not deleted outright |
| ➕ | Declare the cleanup order per entity and take the procedure out of the service method bodies |

### 2.4 Lifecycle machinery

| | Item |
|---|---|
| ✅ | `sokovan/reconciler` — an entity-agnostic lifecycle coordinator. One tick is fetch → execute → classify → apply → post_process, with per-entity retry / give-up / expiry classification, per-stage metrics, and a valkey needed-flag for immediate startup |
| ✅ | `leader/tasks/retention_sweep.py` — a `PeriodicTask` that runs on the leader only. Single execution is guaranteed by leader election, without a distributed lock |
| ✅ | `common/bgtask` — issues a task id and reports success or failure as an event |
| ✅ | Session termination path — `mark_sessions_for_termination`, then the next tick's handler calls `destroy_kernel`, and completion is confirmed by an agent event |
| ➕ | Move the generic reconciler base out of `sokovan` into a **`manager/reconciler`** package |
| ➕ | Build a **deletion-specific lifecycle controller and coordinator** on top of it. A sibling of sokovan that shares no scheduling vocabulary |

The reconciler base is currently tied to session scheduling vocabulary — `SchedulingResult`, `HandlerPolicyResolver`, and the dependency on `data/session/options`. The move includes generalizing that vocabulary.

### 2.5 RBAC scopes and roles

| | Item |
|---|---|
| ✅ | `RBACEntityPurgerSpec` / `RBACEntityBatchPurgerSpec` — deleting a row also removes what it left in the RBAC graph |
| ➕ | When purging a scope-owning entity (domain, project, user), cascade through the roles auto-provisioned at that scope and their mappings (BA-6807, BA-6186) |

## 3. Implementation Design

### 3.1 One status enum and where it lives

**Each entity has one status enum, and that enum lives on the entity row.** Cleanup progress is carried as values in the same enum.

| entity | enum | Values |
|---|---|---|
| `domain` | `DomainStatus` | `active`, `deleted`, `purging`, `purge-error` |
| `project` | `ProjectStatus` | `active`, `deleted`, `purging`, `purge-error` |
| `user` | `UserStatus` | `active`, `inactive`, `deleted`, `before-verification`, `purging`, `purge-error` |
| `image` | `ImageStatus` | `ALIVE`, `DELETED`, `PURGING`, `PURGE_ERROR` |
| `vfolder` | `VFolderOperationStatus` | `ready`, `performing`, `cloning`, `mounted`, `error`, `delete-pending`, `delete-ongoing`, `delete-complete`, `delete-error` |

Cleanup progress is not split into a column of its own. A row being cleaned up is already soft deleted, and once cleanup finishes the row is gone. No combination of the two holds at once, so one enum carries both.

`vfolder` gains no new values. `delete-ongoing` and `delete-error` are where the other entities' `purging` and `purge-error` sit. `performing`, `cloning`, and `mounted` sharing that enum is out of this BEP's scope.

`domain` and `project` gain a status enum over the `is_active` boolean. `is_active` stays as a read-only value derived from the enum and is dropped once callers move.

**Where state is stored is decided by the reading side.** Three questions decide it.

| Question | Entity row | Central |
|---|---|---|
| Does anyone query and filter on it | Yes | No |
| Whose vocabulary is the value | That entity's domain | Shared across entities |
| Does it disappear with the entity | Yes | It may outlive it |

Cleanup progress answers all three on the entity-row side. Users see and filter on it in listings (that is what vfolder's `delete-ongoing` is today), the vocabulary belongs to that entity, and it disappears with the entity. **So no separate work table is introduced.** This matches sokovan keeping `SessionStatus`, `EndpointLifecycle`, and `RouteStatus` on their own rows.

Each entity defines its own enum. No shared vocabulary is created, so an `image` rescan value would grow that enum alone and leave the other entities untouched.

Granularity is also the domain's call. Deletion does not split progress into separate values — the remaining resources are observable, so there is nothing to carry. An operation whose progress cannot be observed puts its steps into its own enum.

**The default value is named** — `active`, `ALIVE`, `ready`. Leaving the everyday value unnamed makes it impossible to tell whether a row is normal. The column is not nullable, and every existing row is backfilled with the default when the column is added.

While status is `purging` or `purge-error`, `delete`, `restore`, and `update` on that entity are rejected. Something being cleaned up cannot be revived or edited.

A successful cleanup removes the row, so there is no transition back to the default. The only way out of `purge-error` is `force purge` (3.5).

These are all the transitions.

| Transition | Trigger |
|---|---|
| `active` → `deleted` | `delete` request |
| `deleted` → `active` | `restore` request |
| → `purging` | `purge` request |
| row removed | cleanup complete |
| `purging` → `purge-error` | retries exhausted |
| row removed | `force purge` request (3.5) |

All five entities get `restore`. `user`'s keypair deactivation is removed from soft delete, and the authentication gate (2.2) blocks a soft-deleted user's API access instead.

### 3.2 The reconciler base stays in sokovan

The generic ABCs in `sokovan/reconciler` are not moved to `manager/reconciler`. Sokovan is being widened into tick-based entity lifecycle at large with the deletion lifecycle inside it, so there is no longer a reason to lift the base out of sokovan (BA-7453).

The deletion coordinator inherits that base from inside sokovan. The changes the base itself needs still stand.

| Item | Change |
|---|---|
| `SchedulingResult` | Generalized to a neutral name unrelated to scheduling. Not renamed into deletion vocabulary — scheduling could not use it then |
| `HandlerPolicyResolver` (from `data/session/options`) | Narrowed to an interface supplying retry counts and timeouts, and moved to the base |
| `ReconcilerStageMetadata.transitions` | Success on the last stage must be able to mean **row removal**, not a status transition |
| `LockID` and the distributed lock | Unchanged. Stages that run without a lock stay allowed |
| `ReconcilerMetricObserver` | Unchanged. The labels carry which machinery it is |

Since `transitions` is bound to a single status type, **there is one stage, one reconcile type, and one task spec per entity kind**. Per-kind failure isolation and per-kind cadence come with that.

History follows sokovan too — `ReconcileHistoryMixin` per entity kind, with the FK on that entity. Attempts, the phases passed through, and the last error live there.

### 3.3 Controller and coordinator

The request side and the tick side are different things. This follows sokovan's split.

| | Lifecycle controller | Lifecycle coordinator |
|---|---|---|
| Called by | Services, during request handling | The tick (event or periodic) |
| What it does | Checks the transition is legal, moves the operation axis, and sets the needed-flag | Reads entities whose operation axis is cleanup-in-progress and advances the handler one step |
| Prior art | `RouteController` — a single method | `ReconcilerCoordinator`, `RouteCoordinator` |

**There is one of each, not one per entity.** The handler is the only thing that varies per entity.

- `delete` and `restore` are already generalized. `DeleteSingleEntityOpsAction` and `RestoreSingleEntityOpsAction` are shared bases taking a single updater.
- Purge options are all resolved inside the DB at request time. `delegate_endpoint_ownership`, `purge_shared_vfolders`, and `cascade_model_card` transfer ownership or drop referencing rows, and touch no external resource.

All the coordinator asks a handler is to **advance one step and report in progress, done, or failed**. Deletion-specific vocabulary stays out of the coordinator contract.

There is one handler per `EntityType`, and it answers two things.

| What the handler answers | Example for `user` |
|---|---|
| The list of cleanup stages | sessions → endpoints → vfolders → association rows → RBAC roles and scope |
| How the entity row is removed | The existing `RBACEntityBatchPurger` |

**Stage registration declares which entities ride this machinery.** There are three cases.

| | Behavior |
|---|---|
| A stage is registered | The purge request moves the operation axis and the tick advances it |
| No stage is registered | Unchanged. The request finishes inline through the existing purger |
| Declared as riding it, but no handler | A wiring error. The request is rejected |

An unregistered entity is not treated as "just delete the row". More than ten entities already declare `ActionOperationType.PURGE` while five ride this machinery. Defaulting to a row delete would let the rest pass through silently doing no cleanup, with no way to tell a missing registration from having nothing to clean.

A handler with no cleanup stages is allowed. It finishes with the row delete on the first tick, and that is a declared intent. A mismatch between the declaration and handler registration is caught by the registry sweep test.

There are two ways it starts.

| Start | Guaranteed | Role |
|---|---|---|
| Long tick | Yes | Picks up whatever is in progress. Correctness comes from here |
| needed-flag | No | Brings the first step forward, right after the `purge` request |

Progress lives on the entity row, so nothing is held between ticks. If the request drops or the manager restarts, the next long tick picks it up. `post_process` does not run when `apply` raises, so nothing that carries progress forward is put there.

### 3.4 The cleanup stage contract

A stage answers three things.

| Slot | Example for the session stage |
|---|---|
| Is anything not yet terminal | Any session outside `SessionStatus.terminal_statuses()` |
| Drive it terminal (idempotent) | `mark_sessions_for_termination` |
| Remove what is terminal | The existing purger — kernel rows first, in order |

Each tick the coordinator walks the stages in order. If the first slot is not empty it triggers the second and ends the tick. If it is empty it runs the third and moves to the next stage. When the last stage finishes, the entity row is removed.

These three slots are a helper shared by the deletion handlers, not the coordinator contract. The general form is **is anything different from the goal / push it toward the goal / finalize what arrived**, and the terminal-based form is its deletion specialization.

Retry and give-up are handled by the base. `ReconcilerStage._classify_outcome` accumulates attempts only while `last.phase` matches, so **using the stage name as the phase** makes a stage that lingers register as a give-up, and resets the count once it moves on.

Terminal states are already defined per resource.

| Resource | Terminal |
|---|---|
| session, kernel | `SessionStatus.terminal_statuses()`, `KernelStatus.terminal_statuses()` |
| routing, replica group | `RouteStatus.terminal_statuses()`, `ReplicaGroupLifecycle.terminal_statuses()` |
| endpoint | `EndpointLifecycle.DESTROYED` |

Association and attached rows that live only in the DB always have an empty first slot and only the third. One contract covers both kinds.

**When a sub-resource is itself a managed entity, the owner does not delete it directly.** The owner's stage asks in the first slot whether any of those rows remain, and in the second slot moves their operation axis to cleanup-in-progress. Once they are gone, the stage passes on a later tick. The owner's `purge` invokes the sub-entity's `purge`, not its `delete`, so the sub-entity does not pass through soft delete.

**Kernels never appear directly in any entity's cleanup stages.** Kernel rows are removed by the session stage, ahead of the sessions. Owning entities name sessions only.

| Entity | Cleanup order |
|---|---|
| `user` | sessions → endpoints released or delegated → vfolders → association and attached rows → RBAC roles and scope |
| `project` | sessions → endpoints released → project vfolders → association rows → RBAC roles and scope |
| `domain` | sessions → association rows → RBAC roles and scope |
| `vfolder` | invitations and permissions → storage deletion |
| `image` | registry untag (only where the registry needs it) → aliases |

Each stage states for itself which column it selects targets by. Sessions are reached through `domain_id`, `group_id`, and `user_uuid` respectively.

Rejection conditions keep using today's `conflict_checks`. What changes is when they are evaluated: at **stage execution** rather than at request time.

The registry untag runs only where the registry type requires it and is skipped elsewhere, never rejected. Untag is currently implemented for Harbor 2 only.

`image`'s `purge_image` and `purge_images` reclaim agent disk space and are not entity deletion. This BEP covers the row-removing side.

### 3.5 Force purge

An escape hatch that removes the row immediately without waiting for cleanup, **on all five entities**.

| | Default purge | Force purge |
|---|---|---|
| Operation axis | Moved to cleanup-in-progress | Untouched |
| Sub-resource DB rows | Removed stage by stage, with confirmation | Removed all at once |
| External resources | Cleanup requested and completion confirmed | Cleanup is **triggered but never confirmed** |
| Entity row | Removed after the last stage | Removed immediately |
| Soft delete first | Required | Not required |

Whether the external resources were actually cleaned up is not guaranteed. That is what this path is, and why it is not the default.

Today's synchronous purge is exactly this behavior. The current code moves onto the force path as-is, and what is newly built is the default path that runs behind the request.

**Permissions match `purge`.** A caller who can request a purge can request a force purge. Force purge is also the way to retry from the cleanup-failed state; no separate retry-resume API is added.

### 3.6 Consistency with external resources

**The manager orchestrates.** A cleanup stage owns the storage-proxy, appproxy, and agent calls directly and confirms their result before moving to the next stage. Having each component clean up its own resources and report back by event is not adopted — vfolder deletion and session termination are already manager-orchestrated today, and this avoids standing up a new cleanup loop in each component.

Sessions are the one exception, riding their existing termination path. The manager marks termination and the agent confirms by event, so the cleanup stage merely observes that confirmation in its first slot.

The window where the DB row and the external resource disagree cannot be eliminated. Instead, the operation axis reads as cleanup-in-progress for as long as it lasts, retries continue, and exhausting them surfaces as cleanup-failed.

### 3.7 API surface

| Operation | Today | After |
|---|---|---|
| `delete` | `is_active=False` for domain and project, status plus keypair deactivation for user, status for image | All five move status to `deleted` |
| `restore` | Only on domain, project, vfolder | All five. Allowed only from the soft-deleted state |
| `purge` | Cleans everything synchronously and answers on completion | **Contract kept.** Moves status to `purging`, subscribes to completion, and answers |
| `force purge` | Only on vfolder (`force_delete`) | All five. Permissions match `purge` |

**The existing API's synchronous contract does not change.** The handler moves the transition through the controller, subscribes to that entity's cleanup completion, waits, and answers.

**The wait exists only in this API handler.** It is there to honor the existing callers' response contract; there is no waiting in the controller, the coordinator, or any cleanup stage. Cleanup advances one step per tick, and the tick ends when that step does. The next step is carried by the next tick.

The wait is bounded at **five minutes**. Stages such as confirming session termination span several ticks and may not finish within it. Past the bound the request answers with a timeout, but **cleanup keeps running**.

Completion is subscribed through `common/bgtask`'s completion event. Exposing a task id for clients to subscribe to directly is not offered.

Status is exposed as a field on the entity. No join is needed, and its values appear only in that entity type's schema.

### 3.8 Cascading RBAC scopes and roles

When a scope-owning entity is purged, the roles auto-provisioned at that scope and their user mappings are cleaned up as one stage of the same flow (absorbing BA-6807 and BA-6186). This touches BEP-1062's virtual scope work, so the ownership definition of a role follows BEP-1062 and this BEP settles only **when** the cleanup happens.

## 4. Migration and Compatibility

### Breaking changes

| Item | Effect |
|---|---|
| `purge` response time | The contract is the same, but past five minutes it answers with a timeout. Callers assuming completion must handle that case |
| `user` soft delete | No longer deactivates keypairs. The authentication gate takes that role |
| vfolder `delete-ongoing`, `delete-error` | The values stay. They are read as the other entities' `purging` and `purge-error` |
| vfolder `delete-complete` | Goes away. Cleanup completion is the row removal |
| `is_active` on `domain`, `project` | Becomes derived from the status enum, then is dropped |

`UserStatus` and `ImageStatus` keep their values and gain `purging` and `purge-error`. `is_active` on `domain` and `project` stays as a read-only value derived from the status enum, so the GraphQL and REST filters and the WebUI that read it are not affected right away; it is dropped after callers move.

### Migration

1. Add `purging` and `purge-error` to each of the five entities' status enum. `domain` and `project` gain a status enum column and carry `is_active` values over; while both exist the enum is authoritative and `is_active` is derived. Add a reconcile history table per entity kind.
3. Add the `user.status` gate to API request authentication, and only then remove keypair deactivation from soft delete. **Reversing the order lets a soft-deleted user keep making API requests with their key.**
4. Users already soft-deleted with keypairs off are left as they are. `restore` only reverts the user row.
5. Read vfolder's `delete-ongoing` and `delete-error` as the other entities' `purging` and `purge-error`, and drive rows left at `delete-complete` through cleanup to finish removing them. `performing`, `cloning`, and `mounted` sitting in the same enum are out of scope here.
6. Move callers reading `is_active` onto the status enum, then drop the column.

### Work in flight

The purger move into `models/` in BA-7443, BA-7444, and BA-7449 **continues as planned**. Of the 29, the association-row purgers keep the same shape after the move, so it is not rework. Only the purgers backed by an external resource relocate into this BEP's cleanup stages.

## 5. Implementation Plan

| Step | Content |
|---|---|
| 1 | Add the `user.status` gate to API request authentication. Independent of the rest and can land first |
| 2 | Open `restore` on `user` and `image`, and remove keypair deactivation from `user` soft delete |
| 3 | Move today's synchronous purge onto `force purge` and open it on all five entities. Behavior is unchanged |
| 4 | Split the scheduling vocabulary out of sokovan's generic reconciler base. The base stays in sokovan |
| 5 | Add the cleanup-progress values to the five entities' status enum and add the history tables. `domain` and `project` gain a status enum |
| 6 | Build the controller, the coordinator, the cleanup stage contract, and the registry sweep test. Validate the flow on the `domain` handler, which has the shortest stage list |
| 7 | Attach the `vfolder`, `image`, `project`, and `user` handlers and remove the procedural code from the services |
| 8 | Add the cascading RBAC role and scope stage (BA-6807, BA-6186) |
| 9 | Switch the `purge` handler to subscribing for completion. The response contract stays the same |
| 10 | Move `is_active` callers onto the status enum and drop the column |

## 6. Open Questions

None.

## 7. References

- [BEP-1062](BEP-1062-virtual-scope-rbac.md) — Virtual Scope RBAC Ownership Model. Ownership definition of a role
- [BEP-1063](BEP-1063-db-record-retention.md) — DB Record Retention Management. Prior art for the LeaderCron periodic sweep
- [BEP-1054](BEP-1054-reconciler-based-idle-checker.md) — Reconciler Based Idle Checker. Prior art for consuming the reconciler base
- [BEP-1061](BEP-1061-agent-kernel-lifecycle.md) — Agent Kernel Lifecycle Structuring. The kernel termination confirmation path
