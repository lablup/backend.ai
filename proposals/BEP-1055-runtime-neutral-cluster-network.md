---
Author: Daemyung Kang (daemyung@lablup.com)
Status: Draft
Created: 2026-07-01
Created-Version: 25.14.0
Target-Version:
Implemented-Version:
---

<!-- context-for-ai
type: master-bep
scope: Replace Docker Swarm overlay for multi-node sessions with a runtime-neutral, pluggable cluster-network data plane coordinated via etcd, so containerd (and other host-native runtimes) can provide the same isolated cross-node connectivity without Kubernetes.
detail-docs: [control-plane.md, agent-plugin-v2.md, data-plane-backends.md, migration.md, verification.md]
key-constraints:
  - Agents run host-native; no Kubernetes.
  - Reuse existing etcd; introduce no new coordination infrastructure.
  - Per-session isolation is mandatory (different orgs may share a node), scoped to Docker Swarm parity (VNI separation + LOCAL ICC-off); egress firewall policy is out of scope / future work.
  - Must work across bare-metal, VM, uncontrolled switches, and NICs lacking VXLAN tunnel offload.
  - Docker path (v1 plugins) must keep working unchanged during rollout.
key-decisions:
  - Runtime neutrality belongs to the agent plugin only; the manager plugin is already runtime-neutral.
  - Control plane (session->subnet/VNI/backend mapping + IPAM) is a single etcd-based implementation, independent of data plane.
  - Data plane is pluggable: vxlan (portable default), host-gw (native routing), wireguard (encrypted).
  - Backend is chosen per session from agent capabilities; operator may force it via config.
phases: 8
-->

# BEP-1055: Runtime-Neutral Cluster Network with Pluggable Data Plane

## Related Issues

- JIRA: BA-XXXX (to be created)
- GitHub: #XXXX
- Related: [BEP-1002 Agent Architecture](BEP-1002-agent-architecture.md), [BEP-1028 Kubernetes Bridge](BEP-1028-kubernetes-bridge.md), [BEP-1051 Kata Containers Agent](BEP-1051-kata-containers-agent.md)

## Motivation

Multi-node (cluster) sessions today get cross-node connectivity from **Docker Swarm overlay networks**. Two problems block the move to a containerd-based, host-native agent:

1. **Swarm is tied to the Docker daemon.** Removing Docker removes the overlay driver, service discovery, and global IPAM that cluster sessions depend on.
2. **Swarm overlay is slow in our fleet.** The dominant causes are not encryption but: VXLAN tunnel offload being unavailable on common NICs (`tx-udp_tnl-segmentation: off [fixed]`), single-queue softirq bottlenecks, and the IPVS service mesh / gossip overhead Swarm adds on top.

We need the same capability — **isolated L2/L3 connectivity between the containers of one cluster session, spanning nodes** — provided by a host-native mechanism that:

- works without Kubernetes and without the Docker daemon,
- reuses our existing etcd for coordination,
- keeps per-session isolation (different organizations may land on the same node),
- and is fast enough across heterogeneous environments (bare-metal, VM, uncontrolled switches, NICs without tunnel offload).

No single data plane wins in every environment (see [data-plane-backends](./BEP-1055/data-plane-backends.md)). Therefore the design separates a **single control plane** from a **pluggable data plane**, and makes the agent-side plugin **runtime-neutral** so the same backend attaches containers under Docker or containerd.

## Current Design

- **Manager plugin** `AbstractNetworkManagerPlugin.create_network()/destroy_network()` (`manager/plugin/network.py`) — already runtime-neutral (returns `NetworkInfo(network_id, options)`). Current impl `OverlayNetworkPlugin` (`manager/network/overlay.py`) calls Docker/Swarm.
- **Agent plugin** `AbstractNetworkAgentPlugin.join_network()` (`agent/plugin/network.py`) — **Docker-coupled**: returns a Docker container config dict (`NetworkMode`, `HostConfig`). Impl in `agent/docker/intrinsic.py`.
- **Wiring**: `SessionLauncher._setup_network_configuration()` selects the plugin by `network.inter_container.default_driver` (default `"overlay"`) and calls `create_network(identifier=session_id)`; agent attaches via `NetworkProvisioner._prepare_plugin_network()`.
- No CNI/containerd networking exists yet.

## Proposed Design

Three pillars, detailed in the sub-documents:

| Pillar | Summary | Document |
|--------|---------|----------|
| Control plane | etcd schema (`network/…`) for session→{subnet, vni, backend} mapping, CAS-based IPAM/VNI allocation, capability-driven backend selection, agent watch/membership | [control-plane](./BEP-1055/control-plane.md) |
| Runtime-neutral agent plugin (v2) | New `backendai_network_agent_v2` group; splits host-level **session-network lifecycle** from runtime-specific **endpoint attach**; returns a neutral `NetworkAttachSpec` consumed by Docker or containerd provisioners | [agent-plugin-v2](./BEP-1055/agent-plugin-v2.md) |
| Pluggable data plane | `vxlan` (portable default), `host-gw` (native routing, no encapsulation), `wireguard` (encrypted); each realizes the same control-plane contract with its own isolation mechanism | [data-plane-backends](./BEP-1055/data-plane-backends.md) |

The **manager plugin stays as-is**; a new `CNINetworkPlugin` implements it and does control-plane allocation. Runtime neutrality is therefore an **agent-only** change.

## Document Index

| Document | Description |
|----------|-------------|
| [control-plane](./BEP-1055/control-plane.md) | etcd schema, IPAM/VNI allocation, backend selection, watch/membership |
| [agent-plugin-v2](./BEP-1055/agent-plugin-v2.md) | Runtime-neutral v2 agent plugin interface and attach spec |
| [data-plane-backends](./BEP-1055/data-plane-backends.md) | vxlan / host-gw / wireguard backends and isolation |
| [migration](./BEP-1055/migration.md) | Rollout, compatibility, config switches |
| [verification](./BEP-1055/verification.md) | Real-infra smoke tests (vxlan / CNI / etcd CAS) |

## Migration / Compatibility

- v1 Docker plugins (`backendai_network_agent_v1`, `OverlayNetworkPlugin`) are untouched; `default_driver="overlay"` keeps current behavior.
- New `default_driver="cni"` opts a deployment into the v2 path. `forced_backend` optionally pins a data plane; unset ⇒ capability-based auto-selection.
- Full detail: [migration](./BEP-1055/migration.md).

## Implementation Plan

| Phase | Scope |
|-------|-------|
| P0 | This BEP (design). |
| P1 | `common/network/types.py`, `agent/plugin/network_v2.py`, `forced_backend` config, `CNINetworkPlugin` skeleton (no behavior change). |
| P2 | Control-plane wiring: `CNINetworkPlugin.create_network` allocates via etcd; `launcher` passes `member_agents`. |
| P3 | Containerd `NetworkProvisioner` + v2 plugin consuming `NetworkAttachSpec` via CNI. |
| P4 | `vxlan` backend + CNI conf → 2-node ping (Swarm-overlay minimum replacement). |
| P5 | Isolation verification (two sessions, same node, mutual block). |
| P6 | `host-gw` backend + capability probe + per-session backend selection. |
| P7 | `wireguard` backend (encrypted option). |
| P8 | Failure/GC: lease-driven peer cleanup, node-crash recovery. |

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-07-01 | Runtime neutrality is agent-only; manager plugin unchanged | Manager plugin already returns a neutral `NetworkInfo`; only `join_network()` is Docker-coupled. |
| 2026-07-01 | Single etcd control plane, pluggable data plane | No environment-agnostic data plane exists; isolate the varying part behind a stable contract. |
| 2026-07-01 | vxlan is the default backend | Works on uncontrolled switches and VMs where native routing / VLAN are blocked; portability beats peak speed for a shipped product. |
| 2026-07-01 | Backend chosen per session from capabilities; `forced_backend` overrides | Heterogeneous fleets mix bare-metal/VM; a per-session choice adapts while operators retain control. |
| 2026-07-01 | Reuse etcd + existing agent liveness lease | No new coordination infra; membership via `members/` watch replaces Swarm gossip. |
| 2026-07-01 | A per-session `SessionNetworkCoordinator` (agent) owns the `members/` watch; the v2 plugin stays a stateless data-plane executor and does NOT start its own watch | Watch/reconcile is backend-invariant (avoids duplication across backends) and session-scoped (not per-container, so it doesn't belong in the per-container provisioner). Backend-specific work stays in idempotent `add_peer`/`del_peer`. |
| 2026-07-01 | `attach_endpoint` returns an `EndpointPlan` (interface chain), not a single spec | A container needs distinct interfaces for distinct purposes; modeling them as an ordered chain keeps the shape explicit and runtime-neutral. |
| 2026-07-02 | Two interface roles: LOCAL (always) + OVERLAY (multi-node only). The LOCAL interface serves BOTH the agent↔container control channel AND external egress, because the host (agent) is the LOCAL bridge's gateway | Avoids a redundant separate "agent-control" interface. Single-node sessions need only LOCAL; multi-node adds one OVERLAY for cross-node traffic. The LOCAL interface is mandatory even for closed sessions (agent must control the kernel) — only its NAT/egress is optional policy. |
| 2026-07-02 | The LOCAL interface is egress-only between containers (inter-container communication disabled); host↔container still works | A shared per-node LOCAL bridge would otherwise bridge two different sessions on the same node, breaking isolation — the same reason Swarm disables ICC on `docker_gwbridge`. Default route rides LOCAL; OVERLAY installs only the session-subnet route. |
| 2026-07-02 | Isolation scope = **Docker Swarm equivalent** (OVERLAY VNI separation + LOCAL ICC-off). Egress network policy (blocking indirect paths — published-port hairpin, node IPs, cloud metadata, internet rendezvous) is explicitly **out of scope**, recorded as future work | Swarm itself does not close these egress paths, and Backend.AI already ships on Swarm today; matching Swarm keeps the security posture unchanged while enabling the containerd migration. Going beyond Swarm is a separable, later effort — see "Security scope & future work" in data-plane-backends.md. |
| 2026-07-02 | **containerd and CNI are managed separately; their only contract is the container network namespace (`/proc/{task_pid}/ns/net`).** ContainerdAgent owns container lifecycle via the **low-level containerd API** (containers/tasks/images/snapshots), NOT CRI `RunPodSandbox` | CRI's `RunPodSandbox` makes containerd auto-invoke the node CNI, coupling runtime and network and assuming a cluster-owned CNI. BEP-1055 owns the network itself (self-managed vxlan/host-gw), so the runtime must create the task with its own empty netns and let our network subsystem attach it — keeping runtime and network independently versioned/verified/replaceable. This is the "path B" resolution of the earlier CRI-vs-low-level question. |
| 2026-07-02 | The prototype's **CRI gRPC client is not reused**; a low-level containerd runtime client is needed instead | The CRI client (`feat/containerd-agent-prototype`) is built around the sandbox→auto-CNI model, which conflicts with separate CNI ownership. Only the netns/PID contract crosses the boundary, so the runtime client must expose task creation + PID, not CRI sandboxes. |
| 2026-07-02 | **Runtime management and network management are two completely separate classes**; the agent is the sole composition point. `ContainerdRuntimeClient` (containerd only — no network imports) and the network subsystem (`SessionNetworkCoordinator`/`ContainerNetworkProvisioner`, containerd-agnostic) never reference each other. `ContainerdAgent` composes them and hands the task's netns/PID from the runtime to the network layer | Enforces the separation as a code-level invariant, not just a convention: either side can be tested, versioned, or replaced in isolation, and the coupling is confined to one orchestration method. |

## Open Questions

- Should `wireguard` be a standalone backend or a composable underlay flag on `vxlan`/`host-gw`?
- Capability probe cadence: boot-only vs periodic re-probe when NIC/topology changes.
- IPAM pool defaults and per-scaling-group override semantics.

## References

- `manager/plugin/network.py`, `manager/network/overlay.py`
- `agent/plugin/network.py`, `agent/docker/intrinsic.py`, `agent/stage/kernel_lifecycle/docker/network.py`
- `common/etcd.py`, `agent/etcd.py`
- Flannel backends (vxlan/host-gw/wireguard), Calico (vxlan/ipip/bgp) — prior art for pluggable data planes without Kubernetes.
