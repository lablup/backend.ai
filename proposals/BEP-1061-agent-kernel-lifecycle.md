---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-07-12
Created-Version: 26.8.0
Target-Version:
Implemented-Version:
---

# Agent Kernel Lifecycle Structuring

## Related Issues

- Epic **BA-6074**, this BEP **BA-6687**
- Children: **BA-6075** (task management structure), **BA-6077** (create stage), **BA-6078** (prepare stage), **BA-6079** (terminate stage)
- Upstream (referenced, not expanded): **[BEP-1002](BEP-1002-agent-architecture.md)** (runner/Provisioner/Stage), **[BEP-1057](BEP-1057-agent-re-architecture.md)** (agent re-architecture, ComputeBackend, LifecycleService)
- Pattern reference: **[BEP-1030](BEP-1030-sokovan-scheduler-status-transition.md)** (sokovan status transition), `kernel_scheduling_history`

## 1. Goal

Structure the Agent's imperative kernel lifecycle (today inline in `agent.py`'s `create_kernel`) along three axes:

| Axis | Content |
|---|---|
| Async trigger contract | Long-running triggers return an ack immediately; progress/completion/failure is delivered via events only |
| Execution vs event separation | Stage handlers execute an operation and return a response only; transition-event emission is a separate layer |
| Unified transition event | A lightweight `(from, to)` event drives both the Manager's kernel-history recording and the status transition |

**Key redefinition:** the authoritative kernel status **state machine lives only in Manager sokovan**. The Agent does not own it; it tracks its local execution phase and *reports* transitions. Transition validation, retry, timeout, and reschedule are sokovan's responsibility. This refines the Epic's "agent state-machine handlers" framing.

**Boundary:** kernel-internal resource setup/teardown ordering belongs to BEP-1002, instance primitives to BEP-1057, status authority to sokovan. This BEP is the orchestration above them (async execution structuring + transition events).

## 2. Current State & Scope, by Area

Per area, **✅ exists / ➕ to add**.

### 2.1 Lifecycle execution (prepare / create / terminate)

| | Item |
|---|---|
| ✅ | `create_kernel` (agent.py:2528) runs pull/resource/scratch/container inline and synchronously. Abstract `prepare_*`/`start_container`/`destroy_kernel`/`clean_kernel` |
| ✅ | `stage/kernel_lifecycle/docker/` has per-resource `Provisioner`/`Stage` drafts (on `common/stage/types.py`) but they are **not wired into the live path** — no runner/DAG sequences them |
| ✅ | `compute_backend/` `ComputeBackend`/`ComputeInstance` (BEP-1057 Phase 1 in progress) |
| ➕ | Prepare/Create/Terminate handlers that sequence the stages and return a response (3.b) |

### 2.2 State representation / transition events

| | Item |
|---|---|
| ✅ | Informal `KernelLifecycleStatus{PREPARING,RUNNING,TERMINATING}` (mutable attribute) + `LifecycleEvent` IntEnum + `container_lifecycle_queue` (not a formal state machine) |
| ✅ | Granular `Kernel*AnycastEvent` (Preparing/Pulling/Creating/Started/Terminating/Terminated, status-driving, anycast = at-least-once) + `Kernel*BroadcastEvent` (UI/streaming) |
| ✅ | Manager sokovan owns the kernel status state machine + retry/reschedule (`ScheduleCoordinator.handle_kernel_running -> mark_kernel_running`) |
| ➕ | A lightweight unified `KernelStatusTransitionAnycastEvent(kernel_id, from, to, reason)` replacing the granular anycast lifecycle events (3.c, 3.d) |

### 2.3 History storage

| | Item |
|---|---|
| ✅ | `KernelRow.status_history` (JSONB, status -> timestamp) |
| ✅ | `kernel_scheduling_history` table: `kernel_id, phase, from_status, to_status, result, error_code, message, attempts, sub_steps`. sokovan uses it for its own scheduling-phase records |
| ➕ | Record the Agent-reported transitions into **`kernel_scheduling_history`** (no new store, 3.e) |

### 2.4 Task management / async trigger

| | Item |
|---|---|
| ✅ | `tasks/` `PeriodicTask`/`LocalCron` (`SyncContainerLifecyclesTask`, etc.), `kernel_registry/` container-label loader/writer (non-pickle recovery path) |
| ✅ | The current create is a synchronous path; a long-running operation blocks the caller |
| ➕ | An async trigger entry + executor + a separate transition-event layer (3.a, 3.c) |

## 3. Implementation Design

### (a) Async trigger contract (hard rule)

Every lifecycle trigger (prepare/create/terminate) follows the same contract:

1. The entry point (RPC/HTTP) validates the request and enqueues the work.
2. It returns an **ack (Accepted) immediately** — it never blocks on the operation.
3. Progress/completion/failure is delivered to the Manager via events only.

This generalizes today's `container_lifecycle_queue` into the universal entry contract and removes the synchronous `create_kernel` path. It composes with BEP-1057 Phase 2 (HTTP entry): the HTTP route returns the ack and the executor runs the work.

```
Manager --trigger--> Agent entry (validate, enqueue, return ack)
                          |
                    [async] Executor -> stage handler (prepare/create/terminate)
                          |  returns response (result)
                          v
                    Transition-event layer (separate): update local phase -> emit transition event
                          |
                    anycast --> Manager (record kernel history + apply from -> to)
```

### (b) Execution layer — stage handlers (BA-6077/78/79)

Handlers are the execution units of the kernel lifecycle. Each consumes BEP-1002 `Provisioner`/`Stage` and calls BEP-1057 `ComputeBackend` to perform its operation, and **returns a response only (no event emission)**. It does not own retry — on failure it tears down acquired resources in reverse order and returns a failure response, and sokovan decides the reschedule. It follows sokovan's "one handler = one file" rule.

| Handler | Local phase transition(s) | Internal work (agent-local) | Story |
|---|---|---|---|
| PrepareHandler | `-> PREPARING`, `PREPARING -> PULLING` | pull_image, prepare_scratch, prepare_resource, prepare_network, prepare_mounts | BA-6078 |
| CreateHandler | `-> CREATING`, `CREATING -> RUNNING` | create_container, start_container | BA-6077 |
| TerminateHandler | `-> TERMINATING`, `TERMINATING -> TERMINATED` | stop_container, cleanup_scratch, release_resources | BA-6079 |

- `from`/`to` use sokovan `KernelStatus` values, so the emitted transition maps directly onto sokovan's status machine.
- **Internal work is agent-local (local logging/metrics) and is not carried in events.** Only status transitions are reported to the Manager.
- On failure, after local cleanup, the handler **reports an agent processing failure** (transition event `result=FAILED` + `error_code`/`message`). **CANCELLED/reschedule is not a kernel-history concern but belongs to sokovan's session scheduling** — the Agent does not emit a CANCELLED transition.
- Handlers must be safe to re-run for the same kernel (a reconciliation sweep or a Manager re-trigger may re-invoke): teardown steps are idempotent, and create steps detect an existing instance by the kernel-id correlation key (BEP-1057).

### (c) Transition-event layer (separate, BA-6075)

A layer separate from execution: it receives the handler response, (1) advances the local phase `from -> to`, and (2) emits the unified transition event. It is the single Agent->Manager egress for lifecycle transitions. The local phase is not authoritative state but progress tracking (sequencing stages, avoiding duplicate work, filling the transition's `from`).

### (d) Unified transition event

Replaces the granular anycast lifecycle events with one lightweight type. **It carries no phase/step payload** — only the transition and its processing result.

| Field | Meaning |
|---|---|
| `kernel_id` | Target kernel |
| `from_status` | `KernelStatus` before the transition (the Agent's local phase) |
| `to_status` | Attempted `KernelStatus` after the transition |
| `reason` | Transition reason (existing `KernelLifecycleEventReason`) |
| `result` | Agent processing result: `SUCCESS` / `FAILED` |
| `error_code`, `message` | Detail on failure (empty on success) |

- The Agent reports only `SUCCESS`/`FAILED` — the retry/timeout/give_up classification of a failure is sokovan's decision (same as the sokovan model where the handler returns success/failure and the coordinator classifies).
- The Manager applies `from -> to` generically instead of one handler per granular event (matching sokovan's declarative transition model).
- `from_status` lets the Manager reject a duplicate/stale transition idempotently.
- **Broadcast granular events are retained** — UI/streaming relies on typed per-phase payloads. (Future direction: emit anycast only and derive broadcast from it; out of scope here.)

### (e) Manager recording / apply contract

On receiving `KernelStatusTransitionAnycastEvent`:

1. **Record history**: record the transition into `kernel_scheduling_history`, mapping the Agent's `KernelStatus` transition and processing result onto the table's phase/from_status/to_status/result/error_code/message columns. **No new store is created.** `sub_steps` is for sokovan's own steps and the Agent does not populate it.
2. **Apply status**: apply `from -> to`, honoring sokovan's transition validation. Retry/timeout/reschedule stay in sokovan.

Existing consumers that updated kernel status on the granular events are migrated to the single transition handler.

### (f) Restart independence

An Agent restart is **independent of (has no effect on) kernel lifecycle and kernel history**. On restart the local phase is reconstructed from `kernel_registry` container labels, but purely for driving; the restart itself neither emits events nor touches history. Genuine state changes (such as a container that is actually gone) are detected by the reconciliation sweep (3.g) independently of restart and reported as normal transition events. Pickle is excluded.

### (g) Delivery guarantee

The "event emission per transition" guarantee is provided by layers, not a new ack protocol:

1. **Structural emission**: the transition-event layer emits the transition event as a non-skippable step after receiving the handler response. A transition is never applied without emitting its event.
2. **At-least-once transport**: anycast is a Redis Stream with consumer groups (ack + re-claim).
3. **Convergence**: the periodic reconciliation sweep (`SyncContainerLifecyclesTask`, extended) re-derives from actual container state and re-emits transitions the Manager may have missed. The Manager applies idempotently via `from_status`, so re-emission is safe. (No heartbeat digest is introduced.)

This mirrors sokovan's guarantee model (history recorded + at-least-once events + sweep convergence). It is not exactly-once.

## 4. Decision Summary

| Decision | Content |
|---|---|
| State machine authority | Only in Manager sokovan. The Agent tracks local phase and reports transitions |
| Trigger | Async ack first, results via events |
| Separation of concerns | Execution (returns response) vs transition event (separate layer) |
| Unified event | Lightweight `KernelStatusTransitionAnycastEvent(kernel_id, from, to, reason, result, error_code, message)` replaces the anycast lifecycle events. No phase/step payload. Broadcast granular retained |
| History storage | Record into `kernel_scheduling_history`. No new store |
| Restart | Independent of kernel/history (no effect). Only the local phase is reconstructed from container labels |
| Failure/cancel | Agent processing failure is reported as transition `result=FAILED` + error. CANCELLED/reschedule belongs to sokovan session scheduling |
| Retry | Not owned by the Agent. sokovan give_up/expired -> reschedule |
| Delivery guarantee | Structural emission + at-least-once + sweep convergence (no heartbeat / no restart events). Not exactly-once |
| Boundary | Resource ordering/teardown = BEP-1002, instance = BEP-1057, status authority = sokovan |

## 5. Open Questions

- Scope of the reconciliation sweep: whether extending `SyncContainerLifecyclesTask` suffices or a dedicated reconciliation task is needed.

## 6. References

- [BEP-1002](BEP-1002-agent-architecture.md), [BEP-1057](BEP-1057-agent-re-architecture.md), [BEP-1030](BEP-1030-sokovan-scheduler-status-transition.md)
- `src/ai/backend/manager/models/scheduling_history/row.py` — the `kernel_scheduling_history` table
- `src/ai/backend/manager/models/kernel/` — `KernelRow.status_history`
- `src/ai/backend/common/events/event_types/kernel/` — existing kernel anycast/broadcast events
- `src/ai/backend/agent/AGENTS.md` — event-only egress, `stage/` state-machine rule
