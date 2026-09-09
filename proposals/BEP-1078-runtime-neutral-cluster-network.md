---
Author: Daemyung Jang (daemyung@lablup.com)
Status: Draft
Created: 2026-09-06
Created-Version: 26.9.0
Target-Version:
Implemented-Version:
---

# Runtime-Neutral Cluster Network

## Related Issues

- BEP-1057 (Agent Re-architecture)
- BEP-1061 (Agent Kernel Lifecycle Structuring)

## 1. Motivation

A multi-node cluster session needs one L2 domain across its kernels. Today that domain is a
Docker Swarm overlay network, which ties the feature to one container runtime: an agent running
containerd, enroot or apptainer has no way to join a session's network, and Swarm's IPAM and VNI
allocation are internal to a daemon the manager does not control.

This proposal moves the cluster network out of the runtime. The manager allocates the session's
address space and tunnel identity; each agent programs its own node's data plane through a CNI
plugin chain, driven by a backend that a runtime-neutral seam selects. The runtime's only role is
to hand over a container's network namespace.

## 2. Design

### 2.1 Layers

| Layer | Owner | Responsibility |
|-------|-------|----------------|
| Control plane | manager | subnet, VNI, per-endpoint IP, encryption key, membership |
| Agent plugin | agent | node data plane: devices, FDB/ARP, firewall, XFRM |
| Backend | agent | how the L2 domain is realized (`vxlan`, `bridge`) |
| Runtime seam | agent | netns of a container, by PID |

Docker is the only supported runtime in the initial implementation. It is the only agent discovery
that supplies a container locator and publishes cluster-network capabilities. Containerd, enroot,
and singularity remain planned until their discoveries implement both contracts. A member agent
without a fresh, matching capability record is refused a CNI cluster-network session.

An agent joins a session by publishing a member record; it removes that record only once its
teardown has completed, which is what the manager reads before it reuses an allocation.

### 2.2 Control plane

Allocation state lives in etcd under `network/ipam/*` and `network/session/{id}/*`, claimed with
compare-and-swap.

| Key | Holds |
|-----|-------|
| `network/ipam/allocated/{block}` | the session that owns a unit block of the pool |
| `network/ipam/vni/{vni}` | the session that owns a VNI |
| `network/session/{id}/meta` | generation, subnet, VNI, backend, MTU, VXLAN port, key and key id |
| `network/session/{id}/ipam/{ip}` | the container that holds an overlay address |
| `network/session/{id}/endpoints/{container}` | ip, mac, agent, cluster hostname |
| `network/session/{id}/members/{agent}` | an agent's VTEP, and its teardown acknowledgement |
| `network/agent/{id}/caps` | what the node's data plane can do |

`create_network` is idempotent on the session id and uses a generation token to fence a reused
identifier. Claims and publications use compare-and-swap. A retried start converges on its existing
allocation, and cleanup releases an allocation only after every member acknowledges teardown.

Managers reconcile paginated etcd scans under a leased leader lock. Reconciliation retains bounded
state, repairs missing claims and stale partial creates, and never deletes unreadable records. The
scheduler requeue and network rollback state transition commits in one database transaction.

Central IPAM — rather than host-local IPAM per node — is what guarantees disjoint addresses on a
subnet stretched across nodes, and the endpoints table is also the input each agent programs
FDB and ARP from.

### 2.3 Agent plugin

The plugin exposes the node's half of a session:

| Verb | Contract |
|------|----------|
| `setup_session_network` | make the node ready to carry the session |
| `attach` | put a container's netns on the session's L2 |
| `detach` | free the host veth, the host-local address, the MASQ rule |
| `add_peer` / `del_peer` | program one remote endpoint; both idempotent |
| `teardown_session_network` | leave nothing of this session on the node |

A node's privileged operations can be delegated to a separate `privnet` daemon, so the agent
itself needs no `CAP_NET_ADMIN`. That is opt-in: `network-privnet-socket` selects it, and with it
unset the agent performs the work in-process. Each agent owns one configured daemon socket; etcd
claims still prevent two agents on one host from programming conflicting session state.

#### 2.3.1 One daemon per node (planned)

Today a node running several agents runs several daemons, one per agent. The target is one daemon
per node serving every agent on it: the daemon exists to concentrate privilege, and N daemons are N
copies of `CAP_NET_ADMIN`, N journals and N sockets. The three node-wide claim stores (VNI
registry, ESP pair journal, LOCAL subnet) exist only because privilege is currently fragmented per
agent.

The one thing that must not be shared is identity. Every node-wide claim carries an owner, and a
daemon serving N agents must stamp each with the agent that asked, not with its own name -- a
reclaim that judged one runtime's containers by another runtime's listing takes a live kernel's
published ports away.

| Concern | Contract |
|---|---|
| Caller identity | One socket per agent, bound to an agent id in the daemon's config. A request field naming the agent is not accepted: any caller could then claim another's rules. |
| Boundary strength | Distinct uid per agent makes the binding kernel-enforced. Agents sharing a uid are one principal to the kernel and can reach each other's sockets regardless, so the binding is an integrity boundary, not a security one. The daemon logs which it has. |
| Ownership stamping | Every use of the daemon's own agent id becomes the caller's: VNI claims, ESP pair claims, port-forward tags, `owner_agent_id` comparisons. |
| Container liveness | One `ContainerLocator` per agent. "Is this container still here" is only answerable by that agent's own runtime. |
| Per-agent state | Sessions, journal and LOCAL subnet allocator are held per agent, not per daemon. |
| LOCAL blocks | Stay per agent. A session spanning two co-located agents keeps a block, a `bailo` bridge and a subnet per agent, exactly as two daemons give it today. |
| Journal layout | `<state_dir>/<agent_id>/...`. A pre-existing root is adopted into the single agent that wrote it; a daemon that cannot find its records recovers nothing. |

Unchanged: the agent still holds no network privilege, and the node-wide claim stores keep their
current on-disk shape and their owner tags -- the owner simply comes from the caller.

### 2.4 Cluster name resolution

Each session gets a resolver on the node that answers `cluster_hostname -> overlay ip` from the
endpoints table, so a kernel reaches its peers by name without a shared `/etc/hosts` write.

### 2.5 Encryption

The VXLAN backend encrypts the overlay by default, in ESP transport mode with
`rfc4106(gcm(aes))`, ESN and a replay window. The key is cluster-wide because ESP policies select
on the outer packet, which carries no session identifier. The lifecycle record exposes only a
fingerprint and key id. Rotation uses the same leased lock as network creation and fails unless all
encrypted sessions are drained, so one session cannot publish the previous key during rotation.

The manager disables encryption only when policy is `prefer` and a member lacks the advertised
profile. Policy `required` refuses the session instead.

## 3. Compatibility

The Swarm overlay plugin stays. `network.inter_container.default-driver` selects between them,
and an operator can pin a backend with `forced_backend`.

| Runtime backend | Swarm `overlay` | BEP-1078 `cni` |
|-----------------|-----------------|----------------|
| Docker | Supported | Supported |
| containerd | Not supported | Planned |
| enroot / singularity | Not supported | Planned |
| Kubernetes | Out of scope | Out of scope |

Published runtime identity and boot identity fence stale capability advertisements. Older agents
that publish no identity remain compatible with the Swarm path, but fail closed on the CNI path.

## 4. Operations

- `backend.ai mgr network audit` reports corrupt records, orphaned claims, and key mismatches
  without returning stored values or secrets.
- `backend.ai mgr network audit --repair` runs one CAS-guarded reconciliation pass.
- `backend.ai mgr network quarantine` copies a CAS-verified orphan to a retained quarantine key
  before deletion; session metadata cannot be quarantined.
- `backend.ai mgr network overlay-key-status` reports only the active key id and lifecycle times.
- `backend.ai mgr network rotate-overlay-key --confirm-drained` rotates only after the manager
  verifies that no encrypted session exists and older managers have been stopped.

The agent distribution includes `backendai-privnet.service`. Startup refuses symlinks, foreign
sockets, non-socket paths, and an already-live daemon; it removes only a stale owned socket.

Prometheus rules alert on allocation exhaustion, invalid records, reconciliation failure, and a
stalled reconciler. The shipped Grafana dashboard shows allocator and reconciliation health.

## 5. Release Gates

Production promotion requires all of the following:

1. Unit and real-etcd tests pass, including pagination, compare-and-swap races, leases, stale
   generations, scheduler rollback, key rotation, audit, repair, and quarantine.
2. The privileged multi-node data-plane suite runs on Docker with
   `BAI_REQUIRE_DATAPLANE=1`, `BAI_DATAPLANE_PRIVNET_MODE=1`, and a reachable privnet socket on
   every node; missing inventory, credentials, or placement is a failure, not a skip.
3. The suite verifies encrypted cross-node traffic, DNS, MTU, agent restart convergence, teardown,
   and absence of leaked links, rules, XFRM state, addresses, subnet claims, and VNIs.
4. Formatting, lint, type checks, and tests pass against the complete branch diff.

This document remains Draft until maintainers approve it. `Target-Version` and
`Implemented-Version` become authoritative only through the status transitions in
`proposals/README.md`; code on an unmerged implementation branch does not make the BEP Implemented.
