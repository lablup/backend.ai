# Agent — Guardrails

> For a full component overview, see `src/ai/backend/agent/README.md`.

## Exceptions

- Define new exceptions in `agent/errors/` — `agent/exception.py` is legacy.

## Container lifecycle

- Container state transitions must go through the state machine in `agent/stage/`.
- Do NOT make direct Docker/K8s API calls that change container state outside the lifecycle handlers.
- Put health-check and heartbeat logic in `agent/health/` — do NOT inline it in the main loop.

## Infrastructure implementations (Docker / Kubernetes / Dummy)

- Always check the abstract base classes in `agent/` before implementing.
- The Dummy implementation must be updated together with Docker/Kubernetes changes.
- Put new infrastructure-specific code in the corresponding sub-directory (`agent/docker/`, `agent/kubernetes/`, `agent/dummy/`).

## Manager communication

- Agent → Manager communication uses the event system only.
- Direct RPC calls to the Manager are allowed only from the designated RPC Server entry points.
- Do NOT add new direct HTTP calls to the Manager inside Agent business logic.

## Resource tracking

- Resource allocation/deallocation must go through `alloc_map.py`.
- Do NOT manipulate resource counters directly outside `alloc_map.py`.
