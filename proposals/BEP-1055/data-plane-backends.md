<!-- context-for-ai
type: detail-doc
parent: BEP-1055 (Runtime-Neutral Cluster Network with Pluggable Data Plane)
scope: The three data-plane backends (vxlan, host-gw, wireguard), how each realizes cross-node connectivity and per-session isolation, and why no single one fits all environments.
depends-on: [control-plane.md, agent-plugin-v2.md]
key-decisions:
  - vxlan is the portable default; host-gw is the fast path when the fabric allows it; wireguard adds confidentiality.
  - Isolation is per-session: VNI (vxlan), subnet + default-deny (host-gw), peer-restricted + encrypted (wireguard).
-->

# BEP-1055: Data-Plane Backends

## Summary

Each backend satisfies the same control-plane contract (`setup_session_network`, `add_peer`/`del_peer` for node VTEPs, `add_endpoint`/`del_endpoint` for proactively programming per-endpoint forwarding+ARP, `attach_endpoint`, `probe_caps`) but realizes connectivity and isolation differently. No backend wins in every environment, so the backend is selected per session.

## Why pluggable (environment matrix)

| | bare-metal + offload NIC | bare-metal + cheap NIC | VM / cloud |
|---|---|---|---|
| vxlan | fast (HW offload) | slow (no offload) | slow + works everywhere |
| host-gw (native routing) | fast | fast | blocked by vSwitch/VPC anti-spoofing |
| VLAN (802.1Q) | fast (needs switch control) | — | blocked |

`tx-udp_tnl-segmentation: off [fixed]` on a fleet NIC confirms VXLAN cannot be HW-accelerated there; that is a data-plane selection input, not a reason to abandon overlays where the fabric is uncontrolled.

## Backends

### vxlan (portable default)

- **Setup:** `ip link add vxlan-{vni} type vxlan id {vni} dstport 4789 nolearning`, bridge `br-{vni}`, veth attach.
- **Peers (node discovery):** unicast head-end replication via `bridge fdb append 00:00:00:00:00:00 dev vxlan-{vni} dst {peer.vtep_ip}` — driven by etcd `members/` watch, no multicast/gossip. This bootstraps reachability to peer VTEPs.
- **Endpoints (proactive, no flood):** the coordinator watches etcd `endpoints/` (manager-assigned `{ip, mac, agent_id}`) and, for every non-local endpoint, programs the exact forwarding + ARP state: `bridge fdb replace {mac} dev vxlan-{vni} dst {peer.vtep_ip}` (unicast MAC→VTEP) and `ip neigh replace {ip} lladdr {mac} dev br-{vni} nud permanent` (ARP suppression). Known unicast then never floods; the broadcast `members/` FDB entry remains only as a fallback for as-yet-unprogrammed endpoints. This mirrors Docker Swarm's gossip-programmed neighbor tables (Swarm parity) and is what keeps the data plane from O(N²) BUM flooding as clusters grow.
- **Isolation:** per-session VNI = separate L2 segment; immune to switch policy because the fabric only sees host-to-host UDP/4789.
- **Perf notes:** enable tunnel offload where present; otherwise apply software mitigations (RPS/RFS, GRO) and jumbo frames. Not encrypted (see wireguard).
- **Attach:** `NetworkAttachSpec(kind=CNI, cni_config=<bridge to br-{vni}, static IPAM = the manager-assigned endpoint ip>)` — the overlay interface uses the central endpoint IP, not per-node host-local (avoids cross-node collision).

### host-gw (native routing, no encapsulation)

- **Setup:** per-session bridge `br-{sid}`; container gateway on the host; the session subnet is pre-split into per-node `ip_range` (control plane).
- **Peers:** `ip route add {peer.ip_range} via {peer.host_ip}` — peers reachable directly on the shared L2.
- **Isolation:** each session bridge is its own broadcast domain; cross-session traffic blocked by `iptables/eBPF` **default-deny FORWARD**, with routes installed only between same-session members. Software-enforced (weaker than VNI/VLAN L2 separation, but zero encapsulation).
- **Requires:** fabric forwards container-IP frames (dumb L2 OK; IP source guard / VPC src-dst-check breaks it) — captured by `probe_caps().native_routing_ok`.
- **Attach:** `NetworkAttachSpec(kind=CNI, cni_config=<bridge to br-{sid}, host-local IPAM within ip_range>)`.

### wireguard (encrypted)

- **Setup:** wg interface + bridge; host-to-host tunnels between session members.
- **Peers:** `wg set peer …` + route; keys distributed via etcd `members/`.
- **Isolation:** peer-restricted + encrypted; use where capture-resistance (confidentiality) is required, not just reachability.
- **Open question:** standalone backend vs composable underlay flag on vxlan/host-gw.

## Interface roles (all backends)

Every container always gets a **LOCAL** interface: a host-local bridge whose gateway is
the host, so it serves BOTH the agent↔container control channel AND external egress via
NAT. It is **egress-only between containers** (inter-container communication disabled) so
a shared per-node LOCAL bridge cannot become a cross-session channel (same reason Swarm
disables ICC on `docker_gwbridge`); host↔container still works. It carries the default
route. The LOCAL interface is mandatory even for closed sessions (the agent must reach the
kernel); "closed" only disables its outbound NAT, not the interface.

Multi-node sessions additionally get an **OVERLAY** interface (below), which carries
inter-node isolation and installs only the session-subnet route. Single-node sessions have
no OVERLAY at all.

## Security scope & future work

Isolation provided here is **equivalent to Docker Swarm**, no more:

- **In scope:** OVERLAY VNI separation (no direct path between sessions) + LOCAL ICC-off
  (no direct L2 chatter over the shared per-node bridge). This matches what Swarm provides
  via separate overlay networks + `docker_gwbridge` with `enable_icc=false`.
- **Out of scope (recorded, not implemented):** egress network policy to close *indirect*
  paths. These remain open, exactly as they do on Swarm today:
  1. LOCAL egress → **node IP : a sibling's published port** (NAT hairpin).
  2. LOCAL egress → other agent nodes / internal services on the management network.
  3. LOCAL egress → cloud metadata (`169.254.169.254`).
  4. Internet rendezvous (a covert channel; unavoidable while internet egress is allowed).

  Closing 1–3 would require a per-session egress firewall (blacklist the IPAM pool **plus**
  node-IP ranges and link-local, or default-deny RFC1918 + whitelist); 4 additionally
  requires denying internet egress. Since Backend.AI already runs on Swarm with these paths
  open, matching Swarm keeps the security posture unchanged. This is a separable follow-up
  BEP if stronger tenant isolation is later required.

## Isolation vs speed (summary)

```
isolation:  vxlan(VNI, HW L2) ≈ VLAN  >  host-gw(SW policy)  >  flat (rejected)
speed:      host-gw(no encap)  >  vxlan(+offload)  >  vxlan(no offload / SW mitigations)
confidentiality: wireguard only
```

## Implementation Notes

- Each backend implements `AbstractNetworkAgentPluginV2` and emits a CNI conf via `attach_endpoint`; the containerd provisioner performs the CNI ADD.
- `probe_caps` per backend: vxlan always available; host-gw gated by the native-routing probe; wireguard gated by the `wireguard` kernel module.
- Teardown must be idempotent and lease-recoverable (peer routes/FDB cleaned when a member disappears).
