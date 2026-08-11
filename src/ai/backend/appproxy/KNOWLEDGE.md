---
name: appproxy-coordinator-worker
type: design-rationale
description: The app/deployment routing component that forwards external requests to kernels, the coordinator/worker split, the coordinator DB slated for removal and treated as schema-frozen, circuit pushes over the event bus, stateless workers, a single shared API secret
scope: src/ai/backend/appproxy
keywords: [coordinator, worker, circuit, SerializableCircuit, alembic, advisory-lock, traefik, stateless]
sources:
  - src/ai/backend/appproxy/coordinator
  - src/ai/backend/appproxy/worker
generated:
  by: claude-code/fable-5
  at: 2026-08-10
status: stable
---

# App Proxy — Knowledge

> There is no `AGENTS.md` here yet. This document carries the assumptions.

## Why this component exists

It is the traffic path that forwards external requests to kernels (a session's
service ports) — it handles routing for app connections and deployment
(model-serving) requests.

- **coordinator**: receives requests from the manager and performs routing work (circuit creation/destruction, worker assignment).
- **worker**: receives the actual traffic and forwards it to kernels.
- **traefik mode**: traffic forwarding is handled by the **Traefik component** instead of workers — the coordinator publishes routes for Traefik to read.

## The coordinator DB is slated for removal

- The long-term direction is to make the coordinator stateless and remove its own DB entirely.
- As part of that, work is planned to **switch workers, like Traefik, to reading a routing source directly for traffic forwarding** — querying the source instead of holding circuits received via push.
- Therefore any change that grows the schema runs against that direction — the root reason for the freeze treatment below.

## Treat the schema as frozen

- The coordinator persists circuits and worker registrations in its own DB, separate from the manager.
- Migrations are never applied at startup — they are a manual operator task, and production environments may never run them at all.
- As a result it can boot on an old schema and fail at query time — **no adding tables/columns**; if unavoidable, only nullable/defaulted columns plus an operator-coordinated rollout.
- Native ENUM columns are banned outright (use `StrEnumType`).

## Circuits travel over the event bus — moving to stateful-source sharing

- Today: the coordinator pushes circuit updates as broadcast events carrying `SerializableCircuit`, and workers filter by their own authority.
- Any attribute workers must see also has to be added to `SerializableCircuit` — older workers silently ignore it, so backward compatibility is mandatory.
- Direction: circuit sharing will change to **stateful-source lookup, the same way Traefik works** — workers read routing state from the source instead of holding pushed circuits (the same stream of work as the DB removal above).

## Workers are stateless

- Identity is the configured `authority` string — re-register plus re-fetch circuits at boot, deregister at shutdown.
- Liveness is a worker→coordinator ping, not a probe.
- Nothing in a worker survives a restart — that is the designed behavior.

## One shared secret, no caller distinction

- manager→coordinator and worker→coordinator both authenticate with the same API secret — the declared auth scope is metadata only.
- The v1/v2 API module pairs coexist because managers of different versions talk to the same coordinator — keep both.

## Coordinator replicas

- Multiple replicas are assumed — singleton work (port collection, Traefik route reconciliation) runs under a DB advisory lock.
