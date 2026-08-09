---
name: manager-control-plane
type: design-rationale
description: the manager as the component that decides business logic (execution/scaling split out to agent, storage proxy, appproxy), the DB as the single source of truth and the Valkey dependency doubling as the event queue, distributed locks and leader election as shrinking mechanisms, inter-component communication direction principles, the fixed DI staging order
scope: src/ai/backend/manager
keywords: [control-plane, source-of-truth, DistributedLockFactory, leader-election, LeaderCron, DependencyComposer, event_dispatcher, consumer-group]
sources:
  - src/ai/backend/manager/dependencies/composer.py
  - src/ai/backend/manager/dependencies/domain/distributed_lock.py
  - src/ai/backend/manager/dependencies/orchestration/leader_election.py
  - src/ai/backend/manager/event_dispatcher/dispatch.py
generated:
  by: claude-code/fable-5
  at: 2026-08-10
status: stable
---

# Manager — Knowledge

> Rules: `AGENTS.md` in the same directory. Per-layer knowledge lives in each subpackage's `KNOWLEDGE.md`.

## Why this component exists

The manager is **the component that decides business logic**. Work that performs
actual operations and needs scaling is split into separate components — kernel
execution to the agent, files to the storage proxy, traffic to the appproxy.

- If a change appears to require running workloads inside the manager, that work belongs to another component.

## The DB is the single source of truth

- Entity state lives in the DB, and critical paths re-query instead of trusting caches (the scheduler re-reads resource groups every tick).
- Valkey holds cache data and doubles as the event queue — the truth is never lost, but **the event dependency is large enough that most operations can break when Valkey fails** (the availability dependency is high).
- etcd holds only configuration and manager state.
- Transactions are READ COMMITTED plus retry on conflict — concurrent writers are assumed and exclusivity is not.

## Distributed locks are being reduced

- N worker processes per host across many hosts — half of the APIs are symmetric and stateless.
- The distributed-lock dependency is not high, but because the scheduler runs in 2 cycles, the coordinator tick currently uses locks (`DistributedLockFactory`, integer `LockID`).
- This part is planned to be replaced by setting a redis-based flag, and distributed locks keep shrinking.
- In leader election (Valkey lease), the leader runs only the cron emitter (`LeaderCron`) — the leader's job is "publishing", and execution is done by whichever process the queue picks.

## Inter-component communication direction

- manager → agent / storage proxy / appproxy: call directly (RPC, HTTP).
- Direct requests in the reverse direction (component → manager) are discouraged — instead use mechanisms that **share values via redis events or a stateful source**.
- Manager-originated instructions that must not be lost are never sent via broadcast alone — call directly or re-drive them with a reconcile tick.
- Manager processes share one consumer group — an anycast event is handled once per cluster, on any process, so handlers must not depend on process-local state.

## Three execution paths, one domain layer

- API-driven: REST/GQL → adapters → processors.
- Event-driven: the `event_dispatcher/` handler groups.
- Timer-driven: leader cron, coordinator tick, per-process tasks.
- All three converge on the same services/repositories — validation that exists only on the API path is a hole, not a rule.

## DI is a fixed staging order

- `ManagerDependencyComposer` composes 10 stages in a fixed order: bootstrap → infra → components → plugins → messaging → domain → system → agents → orchestration → processing.
- The event dispatcher is registered last — nothing consumes events before every service exists.
- Teardown is exactly the reverse order.
- Add a new dependency to the stage where its consumer lives — not to `server.py`.
