<!-- context-for-ai
type: detail-doc
parent: BEP-1062 (Runtime-Neutral Cluster Network with Pluggable Data Plane)
scope: etcd schema, CAS-based IPAM/VNI allocation, capability-driven backend selection, and agent watch/membership that replaces Swarm gossip.
depends-on: [data-plane-backends.md]
key-decisions:
  - Single etcd control plane, independent of data plane.
  - Membership via etcd `members/` watch replaces Swarm gossip.
  - Reuse existing agent liveness lease for GC.
-->

# BEP-1062: Control Plane

## Summary

A single, data-plane-independent control plane maps each cluster session to a `{subnet, vni, backend}` tuple in etcd, allocates addresses without conflict via compare-and-swap, and lets participating agents discover each other by watching a membership prefix. This replaces Swarm's internal raft KV, global IPAM, and gossip with our existing etcd.

## Current Design

- Swarm owns IPAM, VNI, and membership internally; the manager only asks Docker to `create_network`.
- Backend.AI stores coordination state in etcd via `AsyncEtcd` (`common/etcd.py`) and `AgentEtcdClientView` (`agent/etcd.py`), already exposing `put_dict`, `get_prefix`, `watch_prefix`, `delete_prefix`.
- Agent liveness already tracked (agent registers `ip` under `nodes/agents/{id}`, plus heartbeats).

## Proposed Design

### etcd schema (under `ConfigScopes.GLOBAL`)

```
network/config/{default-backend, ipam-pool, ipam-block-size, vni-range}
network/ipam/allocated/{subnet}          -> {session_id, allocated_at}
network/ipam/cursor                      -> next-block hint
network/session/{session_id}/meta        -> {subnet, vni, backend, mtu, created_at}
network/session/{session_id}/members/{agent_id}
                                         -> {host_ip, vtep_ip, ip_range, state}
network/session/{session_id}/endpoints/{container_id}
                                         -> {ip, mac, agent_id, veth}
network/agent/{agent_id}/caps            -> {tunnel_offload, native_routing_ok, backends[]}
```

- `meta` is the source of truth consumed by every data-plane backend.
- Each agent writes only its own `members/{self}`; peers discover each other by watching `members/`. `vtep_ip` (vxlan peer) and `ip_range` (host-gw owned range) are backend-specific fields.
- Agent liveness reuses the **existing** heartbeat/lease; no new lease. When an agent dies, its `members/` entries are GC'd and peers react via watch.

### IPAM / VNI allocation (conflict-safe)

- **Session subnet (variable prefix).** `SubnetAllocator.acquire(host_count)` picks a block prefix large enough to hold `host_count` endpoints (default cap `/24` = 254; a bigger cluster gets `/23`, `/22`, … up to the pool limit), then claims the first free block of that size from `ipam-pool` (default `/12`) with an etcd **transaction** (compare `allocated/{block}` absent → put). A fixed `/24` would cap a session at ~254 endpoints regardless of node count; sizing by `cluster_size` (known at `create_network`) removes that ceiling. Advances `cursor`.
- **Endpoint IPs are assigned centrally by the manager, per endpoint** (populating `network/session/{sid}/endpoints/{container_id} = {ip, mac, agent_id}`), **not agent-locally.** Per-node host-local IPAM would give every node the same first address on the stretched overlay subnet → duplicate-IP collision (see Decision Log 2026-07-06). The manager already owns subnet/VNI allocation and knows kernel placement, so it is the single authority that guarantees disjoint IPs; the `endpoints/` table it writes is also the input to proactive FDB/ARP programming (no BUM flood — see [data-plane-backends](./data-plane-backends.md)). `host-gw` continues to use per-node `ip_range` (native routes are per-range, not per-endpoint).
- `VNIAllocator` mirrors the block claim over `vni-range`, only when `backend == "vxlan"`.
- Exhaustion raises a `BackendAIError` subclass (`NetworkPoolExhausted`).

### Backend selection

```
backend = config.forced_backend or select_backend(members)
select_backend: all(members.caps.native_routing_ok) ? "host-gw" : "vxlan"
```

- Operator override (`network.inter_container.forced_backend`) wins; unset ⇒ capability-based.
- One non-native member (VM / filtering switch) pins the whole session to `vxlan` for consistency.

### Sequences

**Session create (manager):** size + allocate subnet from `cluster_size` (+VNI), select backend, write `meta`, assign a per-endpoint overlay `ip` (+`mac`) to each kernel and write `endpoints/{container_id}` (overlay backends), (host-gw) pre-split `ip_range` per member, then instruct/allow agents to join.

**Agent join:** read `meta` → load backend → `setup_session_network` → write `members/{self}=ready` → watch `members/` for peers → `add_peer`/`del_peer`. Barrier on all-ready before container start.

**Teardown:** `destroy_network` deletes `network/session/{id}` prefix and releases IPAM/VNI; lease expiry is the backup GC path.

## Interface / API

```python
class SubnetAllocator:
    async def acquire(self, session_id, *, host_count=1) -> str  # sizes prefix to host_count, CAS-guarded CIDR
    async def release(self, subnet) -> None

class EndpointAllocator:
    async def assign(self, session_id, container_id, subnet) -> EndpointAddr  # per-endpoint {ip, mac}, CAS-guarded
    async def release(self, session_id, container_id) -> None

class VNIAllocator:
    async def acquire(self, session_id) -> int
    async def release(self, vni) -> None

# CNINetworkPlugin(AbstractNetworkManagerPlugin):
async def create_network(self, *, identifier, options) -> NetworkInfo   # allocates + writes meta
async def destroy_network(self, network_id) -> None                     # frees + deletes prefix
```

`create_network` receives `options["member_agents"]` (the scheduler-placed nodes) from `SessionLauncher`.

## Implementation Notes

- Belongs to manager layers per `manager/CLAUDE.md`: allocation logic is scheduling-adjacent; keep it in `manager/network/` invoked from the launcher, not inside API handlers.
- All etcd writes go through the existing wrappers; no direct etcd3 usage.
- Errors: define `NetworkPoolExhausted` and friends under `manager/errors/`.
