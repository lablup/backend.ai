# Agent — Guardrails

> For full component overview, see `src/ai/backend/agent/README.md`.

## Exceptions

- Every exception raised in business logic MUST inherit from `BackendAIError`.
- NEVER raise `RuntimeError`, `ValueError`, or other built-ins directly in business logic.
- Define new exceptions in `agent/errors/` — NOT in `agent/exception.py` (that file is legacy).

## Async Rules

- All I/O MUST use `async`/`await`.
- `time.sleep()` is forbidden — use `asyncio.sleep()`.
- Blocking calls inside async functions are forbidden — use `asyncio.to_thread()` if unavoidable.

## Container Lifecycle

- Container state transitions MUST go through the defined state machine in `agent/stage/`.
- Direct Docker/K8s API calls that change container state outside the lifecycle handler are forbidden.
- Health check and heartbeat logic belongs in `agent/health/` — do not inline it into the main loop.

## Infrastructure Implementations (Docker / Kubernetes / Dummy)

- Always check the abstract base class in `agent/` before implementing.
- The Dummy implementation must be updated alongside Docker/Kubernetes changes.
- New infrastructure-specific code goes in the corresponding subdirectory
  (`agent/docker/`, `agent/kubernetes/`, `agent/dummy/`).

## Manager Communication

- Agent → Manager communication uses the event system only.
- Direct Manager RPC calls are allowed only from the designated RPC Server entry point.
- Do NOT add new direct HTTP calls to the Manager from inside Agent business logic.

## Resource Tracking

- Resource allocation / deallocation MUST go through `alloc_map.py`.
- Do NOT manipulate resource counters directly outside `alloc_map.py`.
