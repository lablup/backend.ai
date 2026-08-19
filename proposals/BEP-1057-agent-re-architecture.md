---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-07-07
Created-Version:
Target-Version:
Implemented-Version:
---

# Agent Re-architecture

## Related Issues

- Epic **BA-6684**, this BEP **BA-6686**
- Kernel lifecycle (referenced, not expanded): **[BEP-1002](BEP-1002-agent-architecture.md)** (runner model), **BA-6074**/BEP-1687 (execution)
- Adjacent: BEP-1024 (RPC pool), BEP-1028 (K8s bridge), BEP-1044 (device split), BEP-1051 (Kata)

## 1. Goal

Re-architect the Agent in three phases.

| Phase | Work | Done when |
|-------|------|-----------|
| **1. Backend abstraction** | Separate the backend from the god-class; generic parameters → a single `ComputeBackend` interface. Since **VMs (not only containers) are in scope**, the name avoids "container". Service decomposition exposes runtime/resource state **as Manager events**. | External RPC contract unchanged (behavior-invariant); visibility egress in place |
| **2. Controller / Worker split** | Split along the network boundary into a controller (**owns network handling**) and worker (runs the backend). The controller entry point is an **HTTP endpoint**, not Callosum RPC. | Network ownership moved to the controller; Manager↔Agent over HTTP |
| **3. containerd migration** | Add a containerd impl of `ComputeBackend`. **The interface stays**, but networking cannot use Swarm, so a non-Swarm network driver is needed. | containerd backend + non-Swarm overlay working |

**Scope boundary** — anything inside a single kernel's create→terminate belongs to BEP-1002/BA-6074; how the Agent as a whole is assembled, layered, and split belongs here. BEP-1002's **runner is consumed as a black box**.

## 2. Current State & Scope, by Area

Per area, **✅ exists / ➕ to add**.

### 2.1 Agent core & backend abstraction (Phase 1)

| | Item |
|---|---|
| ✅ | `AbstractAgent[KernelType, CtxType](aobject)` — `agent.py` ~3,700 lines, one class owning 30-odd fields and 100-odd methods |
| ✅ | Docker/K8s/Dummy re-implement the full surface via **generic parameters** (`docker/agent.py` ~2,300 lines) |
| ✅ | Target-structure seeds exist: `stage/`, `kernel_registry/`, `tasks/`, `health/` |
| ➕ | Generics → a single `ComputeBackend` ABC (container/VM common), selected at composition time (3.a) |
| ➕ | Extract method clusters into `KernelService`/`ImageService`/`ResourceService`/`StatsService`/`LifecycleService`; the Agent becomes a thin coordinator (3.a) |
| ➕ | Composer builds the whole graph; replace the `aiodocker.Docker` hardcode in `infrastructure/composer.py` with backend selection; retire `__ainit__` (3.a) |

### 2.2 Visibility (Manager egress, Phase 1)

| | Item |
|---|---|
| ✅ | AGENTS.md declares "Agent→Manager via the event system only"; heartbeat exists |
| ✅ | Runtime/resource state is scattered across `AbstractAgent` fields — unobservable beyond heartbeat |
| ➕ | `ObservabilityProducer` single egress — publish resource allocation/usage/runtime state (container/VM common) as Manager events (3.a) |

### 2.3 Resource lifecycle & recovery (Phase 1, cross-cut)

**Acquisition/release** of side resources taken at instance creation (network attach, port reservation, `alloc_map` allocation, scratch, …) and **recovery on agent restart**.

| | Item |
|---|---|
| ✅ | Recovery is centralized in `AbstractAgent` — `_load_kernel_registry_from_recovery` (**pickle-based**), `reconstruct_resource_usage()` (rebuilds alloc from containers), `_restore_ports()`, dangling cleanup (`registered - alive`), `OrphanKernelCleanupObserver` |
| ✅ | This is what BEP-1002 aims to replace with **structural teardown + label-based dangling recovery** (pickle removal is BA-6074's) |
| ➕ | `ComputeBackend` owns instances only — **resources (network/port/alloc) have separate managers with symmetric acquire/release**; ordering is BEP-1002's runner (3.a) |
| ➕ | On restart each manager recovers independently by correlating `list_instances()` on kernel id; `LifecycleService` reports orphan/dangling as Manager events (3.d) |

### 2.4 Entry / RPC & network topology (Phase 2)

| | Item |
|---|---|
| ✅ | Manager↔Agent is **Callosum RPC** (`AgentRPCServer(aobject)` ~1,800 lines), business logic inline in handlers, **two registries coexist** (V1+V2). RPC connection pooling = BEP-1024 |
| ✅ | One process handles both networking and workload execution |
| ✅ | Network is **already a plugin** (`agent/plugin/network.py` + manager `OverlayNetworkPlugin`), but orchestration is inlined in the Agent |
| ➕ | Split into controller (**HTTP endpoint** ingress, routing, network ownership, single egress) / worker (runs the backend). Replace the RPC entry point with HTTP → Manager's agent client migrates RPC→HTTP (3.b) |

### 2.5 Network driver (Phase 3)

| | Item |
|---|---|
| ✅ | Multi-node cluster-session overlay is **Docker Swarm-based** (`swarm-manager/host`, `swarm-worker/token`; `docker_gwbridge`) |
| ✅ | Part of network setup lives in `stage/kernel_lifecycle/docker/network.py` (BA-6074 territory) |
| ➕ | With a containerd backend, a **non-Swarm cross-node network** driver (CNI, etc.) to replace the Swarm overlay — a new impl behind the existing network plugin interface (3.c) |

## 3. Implementation Design

### (a) Phase 1 — Backend abstraction + service decomposition + visibility

- Service calls are lightweight `service.method(args)` (no Manager-style Action/ActionResult — the Agent has no processor layer).
- `KernelService` only drives BEP-1002's `runner` (black box). Keeping the runner contract stable lets BA-6074 proceed in parallel.
- **Naming**: not tied to "container" — `ComputeBackend` (tentative). **Network is excluded from the backend interface** — the controller owns it in Phase 2, so the backend is responsible only for instance lifecycle.

```python
class ComputeBackend(ABC):  # name is an Open Question — container/VM common
    async def create_instance(self, spec: InstanceSpec) -> InstanceHandle: ...
    async def destroy_instance(self, handle: InstanceHandle) -> None: ...  # idempotent
    async def inspect_instance(self, handle: InstanceHandle) -> InstanceInfo: ...
    async def list_instances(self) -> Sequence[InstanceInfo]: ...  # self-described by labels
    async def collect_stats(self, handle: InstanceHandle) -> InstanceStat: ...
```

- impls: `docker/`, `kubernetes/`, `dummy/`, (future) `containerd/`, `vm/`. Dummy is updated in lockstep per the AGENTS.md rule.
- **The backend is responsible for instance create/destroy only** — network, port, `alloc_map`, and scratch are owned by **separate managers** (ResourceService, network plugin). The backend does not manage resources internally.
- It does stamp a **kernel-id correlation key** on the instance so separate managers can match running instances on restart. `destroy_instance` is idempotent (callable from orphan cleanup with just the handle).

**Resource acquire/release interface** — Phase 1 also organizes the other resource managers as injected services alongside the backend. No new common interface is introduced; the existing symmetric primitives are used as-is:

| Resource | Acquire / Release | Manager |
|----------|-------------------|---------|
| instance | `create_instance` / `destroy_instance` | `ComputeBackend` |
| alloc | `alloc_map.allocate` / `free` | `ResourceService` |
| port | allocate / free | `PortPool` |
| network | `join_network` / `leave_network` | `NetworkPlugin` (controller-owned in Phase 2) |

Acquire in order → release in reverse on termination, with rollback on failure, is orchestrated by BEP-1002's `Provisioner`/`Stage` (setup/teardown). `release` is idempotent, so re-invocation during recovery is safe.

### (b) Phase 2 — Controller / Worker split (HTTP endpoint · network on the controller)

```
Manager ──HTTP(ingress) / events(egress)── Controller (HTTP endpoint · networking · worker routing · single egress)
                                                │ controller↔worker channel
                                                ▼
                                            Worker 1..N (runs services → ComputeBackend)
```

- Switch the controller entry point from **Callosum RPC to an HTTP endpoint** (REST). Phase 1's thin handlers move behind HTTP routes as `service.method(args)` delegation, and the V1/V2 RPC registries are retired.
- Only the Manager→Agent direction is HTTP. **Agent→Manager egress stays on the event system** (AGENTS.md rule).
- **Network ownership moves to the controller** — it invokes the existing network-plugin orchestration; workers deal only with backend instances.
- Since Manager's agent client changes RPC→HTTP, **a Manager-side change is entailed**. BEP-1024 RPC pooling is superseded/revisited as HTTP connection handling.

### (c) Phase 3 — containerd migration

- Add a containerd impl of `ComputeBackend` — **the interface is unchanged** (thanks to 3.a).
- containerd has no Swarm, so **replace the overlay network with a controller-owned non-Swarm driver**. Since Phase 2 already moved networking to the controller, the replacement is confined to the controller / network plugin (ordering dependency).

### (d) Restart recovery & teardown boundary (cross-cut)

On termination/restart, resources must be **released and recovered without leaks**. Acquire/release managers are in (a), ordering and structural teardown belong to BEP-1002's runner, and this BEP handles recovery:

| Concern | Owner | How |
|---------|-------|-----|
| Ordering & structural teardown | **BEP-1002 runner** | Register each resource with the runner; on termination, cancel to release all in reverse (no scattered cleanup) |
| Restart recovery | `ResourceService`·`LifecycleService` (this BEP) | Each manager recovers **independently** by correlating `list_instances()` on kernel id — alloc from device bindings (`reconstruct_resource_usage`), ports from port bindings (`_restore_ports`). Dangling is reported to the Manager **as events** (replacing pickle · `OrphanKernelCleanupObserver`) |

### (e) Rewrite workflow (behavior-invariant)

| Step | Content | Gate |
|------|---------|------|
| Phase 0 | Characterization tests for current RPC behavior (BEP-1002 Phase 1, never done) | Parity baseline for all later steps |
| Phase 1 | composition root → `ComputeBackend` → service extraction (flag) → visibility egress → thin entry / registry unification | Parity each step, RPC contract unchanged |
| Phase 2 | controller/worker split + network ownership move | Minimal Manager-side change |
| Phase 3 | containerd backend + non-Swarm network | Functional parity |

## 4. Decision Summary

| Decision | Content |
|----------|---------|
| BEP form | New BEP-1057. BEP-1002 cited as the runner model |
| Backend scope | `ComputeBackend` (tentative) does instance create/destroy only. Container/VM common. Network and resources excluded |
| Phases | 1) backend abstraction → 2) controller/worker split (+network, HTTP endpoint) → 3) containerd migration |
| Transport | Controller entry = HTTP (REST). Only Manager→Agent is HTTP; egress stays events. BEP-1024 pooling superseded |
| Call convention | Lightweight `service.method(args)` |
| Safety net | Phase 0 characterization tests + feature-flag dual-run. RPC contract unchanged |
| Resource reclaim | Per-resource symmetric acquire/release managers (alloc_map, PortPool, NetworkPlugin, ComputeBackend); ordering/teardown by BEP-1002 runner |
| Boundary | Kernel stage & resource teardown = BEP-1002/BA-6074; device split = BEP-1044 |

## 5. Open Questions

- `ComputeBackend` naming and abstraction level — container/VM common minimum vs per-backend extension. Distinguish Kata (containers-in-VM) from full VM.
- backend/network as entrypoint plugins vs compile-time impls (BEP-1051/1028).
- Phase 2 network ownership vs BA-6074's network stage boundary.
- Phase 3 non-Swarm cross-node overlay approach (CNI vs custom).
- Resource teardown execution ownership (BEP-1002 runner) vs manager-provided (this BEP).
- Scope of per-backend image APIs (containerd CRI) in `ImageService`.
- Visibility event schema (extend heartbeat vs new types; container/VM common).

## 6. References

- [BEP-1002](BEP-1002-agent-architecture.md) — kernel-runner/Provisioner/Stage model (upstream)
- [BEP-1024](BEP-1024-agent-rpc-connection-pooling.md), [BEP-1028](BEP-1028-kubernetes-bridge.md), [BEP-1044](BEP-1044-multi-agent-device-split.md), [BEP-1051](BEP-1051-kata-containers-agent.md)
- `src/ai/backend/agent/plugin/network.py`, manager `OverlayNetworkPlugin` — existing network plugin (Swarm overlay)
- `src/ai/backend/agent/AGENTS.md` — declared target rules (`stage/`, `health/`, event-only egress, `alloc_map`)
