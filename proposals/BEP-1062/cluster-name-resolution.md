<!-- context-for-ai
type: detail-doc
parent: BEP-1062 (Runtime-Neutral Cluster Network with Pluggable Data Plane)
scope: How a cluster session's containers resolve peer hostnames (main1, sub1, …) to addresses — the static /etc/hosts approach today and its evolution to a decentralized etcd-backed resolver for dynamic membership and backend unification.
depends-on: [control-plane.md, data-plane-backends.md]
key-decisions:
  - Keep /etc/hosts for localhost + self; resolve peers via a per-node resolver (hybrid).
  - The resolver reuses the existing control-plane etcd endpoint table; no new consensus, no central DNS component (privnet-style decentralization).
  - Container resolv.conf points at the LOCAL/overlay gateway the network layer already owns; the resolver is split-horizon (cluster names → etcd, everything else → forward upstream).
-->

# BEP-1062: Cluster Name Resolution

## Summary

A multi-node session's containers reach each other by hostname (`main1`, `sub1`, …) — torchrun/c10d, MPI, and NCCL all resolve peer names before opening rank connections. This document defines how that resolution works: the **static `/etc/hosts`** the agent writes today, its inherent rigidity, and the evolution to a **decentralized etcd-backed resolver** that gives containerd the dynamic name resolution the Docker/Swarm backend already has — without Swarm's manager, reusing the existing etcd.

## Current Design

containerd/runc synthesizes no `/etc/hosts` and provides no cluster DNS (unlike dockerd/Swarm). So the agent writes the file itself and bind-mounts it read-only into each container.

| Area | State |
|---|---|
| localhost + own hostname | ✅ Always written (`agent/containerd/agent.py::_write_etc_hosts`) |
| Peer map (hostname→IP) | ✅ Multi-node: manager's `cluster_hosts` (central IPAM, `endpoints/`). Single-node: agent lays peers out deterministically in the session LOCAL subnet (`cluster_host_ips`) |
| Consistency guarantees | ✅ Hardened (see below): own-in-map validated for both cluster modes; a clustered kernel's own name never falls back to loopback; a rank-list peer absent from the IP map is refused; hostname derivation single-sourced (`cluster_hostname_of`); atomic write |
| Dynamic membership | ❌ Static file, written once as a read-only bind mount |
| Backend uniformity | ❌ containerd writes a file; Docker relies on Swarm embedded DNS + `ExtraHosts` — the resolution mechanism (and the hardening above) diverges per backend |

### Why the static file is rigid

- **Static** — written once at container creation; membership changes (kernel restart with a new address, elastic scale) cannot be reflected without recreating the container or rewriting a live bind-mounted file (fragile: `os.replace` swaps the inode the mount pins).
- **Coupled to the container FS lifecycle** — the map lives as a bind mount, not a query; changing form means unpicking that coupling.
- **Read-only** — the container cannot add its own `/etc/hosts` entries.
- **Backend-divergent** — the same logical need has two implementations, so a fix on one path (this BEP's hardening) does not apply to the other.

The static file is the right tradeoff for **statically-sized, batch-created** cluster sessions (all kernels created together, living together) — which is what Backend.AI sessions are today: zero extra infrastructure, fully decentralized (each kernel computes the same map independently), works where the runtime gives nothing. It becomes wrong once membership is **dynamic/elastic**.

## Proposed Design

Move peer resolution from a static file to a **per-node split-horizon resolver** backed by etcd, keeping a minimal `/etc/hosts`. This gives containerd the dynamic DNS that Docker/Swarm already provides, but decentralized via etcd instead of Swarm's Raft managers — consistent with BEP-1062's "reuse etcd, no new coordination" principle.

### Hybrid: file for self, resolver for peers

| Name | Resolved by | Nature |
|---|---|---|
| `localhost`, **own hostname** (own overlay/LOCAL IP) | `/etc/hosts` (nsswitch `files`) | static, always correct at creation |
| **peers** (`sub1`, `main1`, …) | **DNS → per-node resolver → etcd** | dynamic |

nsswitch `hosts: files dns` splits these naturally. Self and localhost stay in `/etc/hosts` — `gethostbyname(gethostname())` never depends on DNS being up, and a clustered kernel's own name is authoritatively its real address (the loopback-fallback class of bug disappears structurally, not by validation).

### The resolver is the network layer, not a new component

The per-node network daemon (the privnet/coordinator that already owns the LOCAL/overlay **gateway** address and talks to etcd) answers DNS on that gateway. The container's `resolv.conf` nameserver is that gateway — an address the network layer already programs, so no new listener address and no new component. Split-horizon: **cluster names → etcd lookup; everything else → forward to the host's upstream resolver.**

### Name source: reuse the control-plane etcd table

The resolver reads the **existing** control-plane data, not a new table where avoidable. The manager already writes per-endpoint overlay IPs to `endpoints/` (see control-plane.md, decision 2026-07-06); joined with each kernel's cluster hostname that is exactly the `hostname → IP` the resolver needs. Publication stays **decentralized and per-kernel** (each agent/coordinator owns its kernels' entries, mirroring VTEP publication), so a kernel restart updates one key and every peer's next query sees the new address — the dynamic-membership property the static file lacks.

### Backend unification

- **containerd** → this resolver (etcd-backed, dynamic) replaces the static file for peers.
- **Docker** → already has Swarm embedded DNS (dynamic).

Both converge on dynamic DNS; the resolver brings containerd to parity **without** a Swarm-style manager. The per-backend hardening divergence collapses into one resolution path for the containerd side.

## Interface / API

- **etcd (read):** the resolver resolves `hostname → IP` from the session's endpoint/hosts view under the control-plane prefix (reuse `endpoints/` + hostname; a thin `hosts/` projection only if a join at query time is impractical). Lease/teardown semantics match VTEP withdrawal so a dead kernel's name expires.
- **Resolver contract:** authoritative for the session's cluster names; forwards all other queries to the node upstream resolver; short TTL so membership changes propagate; etcd watch may back a local cache to bound query load.
- **Container config:** `/etc/hosts` = localhost + self only; `/etc/resolv.conf` nameserver = the LOCAL/overlay gateway the network layer owns.

## Implementation Notes

**Phasing (backward-compatible):**

1. **Hardening of the static path — done.** own-in-map validation for both cluster modes, no loopback for cluster members, refuse an unresolvable listed peer, single-source hostname derivation, atomic write. (Regression tests in `tests/unit/agent/containerd/test_context.py::TestEtcHosts`.)
2. **Resolver core — done.** Split-horizon resolve logic + UDP server built on `dnspython` (`agent/network/privnet/resolver.py`): cluster name → `ClusterNameSource` (an injected interface) → authoritative `A`/NODATA; anything else → `make_upstream_forwarder`; SERVFAIL (not NXDOMAIN) on total upstream failure so the client can retry. Unit-tested + **live-validated in a real fatpod multi-node session**: bound on the LOCAL gateway (`172.30.0.1`) a kernel routes through, a CinC's `getent` resolved a peer name absent from `/etc/hosts` to its overlay IP, that IP reached the peer's sshd cross-node over the VXLAN overlay, and a non-cluster name forwarded to the cluster resolver. The name source (in-memory here) and daemon wiring (who starts it / writes resolv.conf) are still injected, not yet bound in privnet.
3. **Name availability in etcd** — implement `ClusterNameSource` over the control-plane tables (reuse `endpoints/` vs a thin `hosts/` projection is the open question; per-kernel publication/withdrawal decentralized).
4. **Daemon wiring** — the privnet starts `ClusterDNSServer` on the LOCAL/overlay gateway it owns; container `/etc/resolv.conf` nameserver points there. Runs alongside the full static `/etc/hosts` first (`files` before `dns`) so the resolver is validated risk-free. Needs live multi-node infra.
5. **Shrink `/etc/hosts`** to localhost + self; peers resolve via the resolver. Dynamic membership is now live.

**Costs / risks:**
- The resolver must **forward** non-cluster names (a bare `NXDOMAIN` stops the client from trying the next nameserver), i.e. a small split-horizon forwarding resolver — the one genuinely new piece.
- TTL vs query-load tradeoff; an etcd-watch cache mitigates.
- Requires the network layer to bind UDP/TCP 53 on the gateway it owns.

**Non-goals:** replacing Docker/Swarm's embedded DNS (already dynamic); a cluster-wide DNS zone / service-discovery records beyond flat `hostname → A`.
