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

### Name source: reuse the per-session `endpoints/` table

The resolver reads the **existing** control-plane data, not a new table. The manager already writes per-endpoint overlay IPs to `network/session/{session_id}/endpoints/{container_id}`; enriched with each endpoint's **`cluster_hostname`** (the manager knows it at IP-assignment time) that record *is* the `hostname → IP` the resolver needs.

> **Multi-node only.** Only the MULTI_NODE overlay path writes `endpoints/` (the manager's `create_network`); a **single-node** multi-kernel session takes the agent-local bridge path (`create_local_network`) and computes peer IPs locally with `cluster_host_ips`, writing nothing to etcd. So the coordinator-backed name source resolves **multi-node** sessions only. Single-node sessions resolve peers purely via `/etc/hosts` today — which is fine while `/etc/hosts` stays full (phase 4), but is a hard prerequisite for phase 5: removing the peer map must first give the single-node path its own resolver name source (feed the agent's `cluster_host_ips` map into a `ClusterNameSource`), or keep `/etc/hosts` for single-node. The agent's `SessionNetworkCoordinator` already watches this per-session prefix to program FDB/ARP, so it maintains a live `hostname → IP` map for free on the same watch — a kernel restart updates one key and every peer's next query sees the new address (the dynamic-membership property the static file lacks). This resolves the earlier open question "reuse `endpoints/` vs a thin `hosts/` projection" in favour of **enriching `endpoints/`**.

### Names are session-scoped, never global — no collision

Every multi-node session names its kernels the same way (`main1`, `sub1`, …), so cluster hostnames are unique **only within a session**. Moving them into etcd does **not** make them a global namespace, because the control plane is already session-partitioned end to end:

| Layer | Scoping | Consequence |
|---|---|---|
| etcd keys | `network/session/{session_id}/endpoints/…` — no flat `hosts/` | session A's `main1` and session B's `main1` are different keys |
| coordinator | per-`session_id` watch + `hostname → IP` map | each session's name map is isolated in memory |
| privnet LOCAL subnet / gateway | `local_subnets.allocate(session_id)` — a distinct gateway per session | a container talks to *its* session's gateway only |
| resolver instance | one per session, bound to that session's gateway, reads only that session's map | different sessions' identical names are answered by different resolvers |

So resolution is **per-session, not per-node** — the resolver a container reaches only ever knows that container's own session. This is the same isolation the per-container static `/etc/hosts` had (each file was session-local); the only change is *where* the map lives (session-scoped etcd + a session-scoped resolver instead of a bind-mounted file). A `resolve_cluster_name(session_id, hostname)` lookup keys on the session, so a missing session or unknown name simply falls through to upstream forwarding.

### Backend unification

- **containerd** → this resolver (etcd-backed, dynamic) replaces the static file for peers.
- **Docker** → already has Swarm embedded DNS (dynamic).

Both converge on dynamic DNS; the resolver brings containerd to parity **without** a Swarm-style manager. The per-backend hardening divergence collapses into one resolution path for the containerd side.

## Interface / API

- **etcd schema (settled):** the resolver resolves `hostname → IP` from `network/session/{session_id}/endpoints/{container_id}`, whose value now carries `cluster_hostname` alongside `ip`/`mac`/`agent_id`. `EndpointAddr.to_etcd_payload`/`from_etcd_payload` single-source the wire format; `cluster_hostname` is nullable so pre-existing/name-less endpoints decode unchanged. The coordinator rebuilds the per-session `hostname → IP` map from the **full** table (own + remote endpoints — a co-located peer must resolve too, unlike the remote-only FDB view) on every reconcile, so a departed kernel drops out. Delete semantics match endpoint withdrawal so a dead kernel's name expires.
- **Resolver contract:** authoritative for the session's cluster names; forwards all other queries to the node upstream resolver; short TTL so membership changes propagate; etcd watch may back a local cache to bound query load.
- **Container config:** `/etc/hosts` = localhost + self only; `/etc/resolv.conf` nameserver = the LOCAL/overlay gateway the network layer owns.

## Implementation Notes

**Phasing (backward-compatible):**

1. **Hardening of the static path — done.** own-in-map validation for both cluster modes, no loopback for cluster members, refuse an unresolvable listed peer, single-source hostname derivation, atomic write. (Regression tests in `tests/unit/agent/containerd/test_context.py::TestEtcHosts`.)
2. **Resolver core — done.** Split-horizon resolve logic + UDP server built on `dnspython` (`agent/network/privnet/resolver.py`): cluster name → `ClusterNameSource` (an injected interface) → authoritative `A`/NODATA; anything else → `make_upstream_forwarder`; SERVFAIL (not NXDOMAIN) on total upstream failure so the client can retry. Unit-tested + **live-validated in a real fatpod multi-node session**: bound on the LOCAL gateway (`172.30.0.1`) a kernel routes through, a CinC's `getent` resolved a peer name absent from `/etc/hosts` to its overlay IP, that IP reached the peer's sshd cross-node over the VXLAN overlay, and a non-cluster name forwarded to the cluster resolver. The name source (in-memory here) and daemon wiring (who starts it / writes resolv.conf) are still injected, not yet bound in privnet.
3. **Name availability in etcd — done.** `EndpointAddr` carries `cluster_hostname`; the manager writes it (`EndpointAllocator.assign` ← launcher's `cluster_hostname_of`), and the coordinator maintains a per-session `hostname → IP` map exposed via `resolve_cluster_name(session_id, hostname)` (case-insensitive, session-scoped). Backward-compatible (nullable field). Unit-tested (`test_types.py::TestEndpointAddr`, `test_coordinator.py::TestClusterNameResolution`, `test_cni.py`).
4. **Daemon wiring — done, live-validated.** `ContainerdSessionNetwork` starts one `ClusterDNSServer` per session on that session's LOCAL gateway (`local_gateway_of` = first host of the session's LOCAL subnet), with `SessionClusterNames(coordinator, session_id)` as the source and the container-DNS upstreams as the forwarder; it is torn down with the coordinator. The container's `/etc/resolv.conf` lists the gateway **first**, then the upstreams. It runs **alongside the full static `/etc/hosts`** (nsswitch `files` before `dns`), so if the resolver is absent nothing regresses.
   - **Ordering (found in live validation):** in privnet mode the session's LOCAL block — hence its gateway — is not allocated until the **first container attaches**, so the resolver cannot start at `ensure_session` (gateway unknown then). `ensure_cluster_dns(session_id)` is therefore idempotent and called **post-attach** (only the first attach on a node binds), plus on resume/adopt where devices already exist. Likewise the gateway is prepended to `/etc/resolv.conf` post-attach (`_point_resolv_conf_at_resolver`); the file is bind-mounted, so an in-place rewrite is picked up on the container's next lookup. Best-effort throughout — a missing gateway or failed bind is logged, never fatal.
   - **Validated live** on a 2-node fatpod MULTI_NODE session (main1@node-A, sub1@node-B): the manager wrote `cluster_hostname` into `endpoints/`; each agent auto-started the resolver on its LOCAL gateway (`172.30.0.1:53`); the CinC's `resolv.conf` listed it first; and **from inside main1's container, `sub1` resolved to its overlay IP (10.128.7.1) via the resolver and connected cross-node**, while non-cluster names forwarded to CoreDNS. Unit-tested (`test_session_network_dns.py`, `test_coordinator.py`).
5. **Remove the static peer map from `/etc/hosts` — done, live-validated.** `/etc/hosts` keeps only `localhost` + self (own name → its real overlay/LOCAL address); the peer map is no longer written. Peers resolve through the resolver — the Docker model (embedded DNS + `Aliases`, no static peer file). `_peer_host_map` still computes the map to register names / pin the single-node address / derive `own_ip`.
   - **Single-node name source (settled):** single-node sessions have no `endpoints/` table, so the agent registers the locally-computed `cluster_host_ips` with the coordinator (`register_static_names`) — the analog of Docker's `Aliases`. `resolve_cluster_name` checks the dynamic etcd map first, then these static names.
   - **Live-validated 2-node.** *Multi-node* (main1@node-A, sub1@node-B): the CinC's `/etc/hosts` held only `localhost`+`main1`, yet `getent hosts sub1` returned its cross-node overlay IP via the resolver. *Single-node cluster* (main1+sub1 co-located, bridge backend, no etcd endpoints): `/etc/hosts` held only self, and `getent hosts sub1` resolved via the resolver from the registered `cluster_host_ips`. Both use resolv.conf → the session gateway, resolver auto-started post-attach.
   - **Known limitation (follow-up):** *node-level resolver ownership* — two agents on one node share one gateway, so only one can bind `:53`. Best-effort bind handles the conflict; making the resolver a node-level singleton (or re-owning it on withdraw) is future work. Unlike dockerd's always-on embedded DNS, this resolver is best-effort, but every containerd cluster session has a LOCAL gateway so it reliably starts (validated).

**Costs / risks:**
- The resolver must **forward** non-cluster names (a bare `NXDOMAIN` stops the client from trying the next nameserver), i.e. a small split-horizon forwarding resolver — the one genuinely new piece.
- TTL vs query-load tradeoff; an etcd-watch cache mitigates.
- Requires the network layer to bind UDP/TCP 53 on the gateway it owns.

**Non-goals:** replacing Docker/Swarm's embedded DNS (already dynamic); a cluster-wide DNS zone / service-discovery records beyond flat `hostname → A`.
