<!-- context-for-ai
type: detail-doc
parent: BEP-1055 (Runtime-Neutral Cluster Network with Pluggable Data Plane)
scope: Reproducible real-infrastructure smoke tests validating the vxlan command builders, the CNI config + runner protocol, and the etcd put_if_absent CAS. Complements the unit tests (which mock the OS/etcd boundary).
depends-on: [agent-plugin-v2.md, data-plane-backends.md, control-plane.md]
-->

# BEP-1055: Real-Infrastructure Verification

Unit tests mock the OS and etcd boundaries. The three pieces that can only be
confirmed on real infrastructure were validated on a Linux 6.8 host (lima VM) with
containerd/CNI plugins and a real etcd. All passed.

## 1. VXLAN data plane (VxlanNetworkPlugin command builders)

Runs the exact argv the backend emits (`vni=4097`, `uplink=eth0`):

```sh
ip link add baivx4097 type vxlan id 4097 dev eth0 dstport 4789 nolearning
ip link add baibr4097 type bridge
ip link set baivx4097 master baibr4097
ip link set baivx4097 up
ip link set baibr4097 up
bridge fdb append 00:00:00:00:00:00 dev baivx4097 dst 10.0.0.2   # add_peer
# teardown
bridge fdb del 00:00:00:00:00:00 dev baivx4097 dst 10.0.0.2
ip link del baibr4097 ; ip link del baivx4097
```

Result: vxlan device (`id 4097 dev eth0 dstport 4789`) created, enslaved to the
bridge, FDB entry present (`00:00:00:00:00:00 dst 10.0.0.2 self permanent`), clean
teardown. ✅

## 2. CNI attach (overlay_cni_config + CniPluginRunner protocol)

Applies the backend's overlay config to a netns exactly as `CniPluginRunner` does
(CNI_* env + config on stdin), using the real `bridge` plugin:

```sh
ip netns add bai-test-ns
CONF='{"cniVersion":"1.0.0","name":"bai-overlay-s1","type":"bridge","bridge":"baibr4097","isGateway":false,"ipMasq":false,"mtu":1450,"ipam":{"type":"host-local","subnet":"10.128.5.0/24"}}'
echo "$CONF" | env CNI_COMMAND=ADD CNI_CONTAINERID=c1 CNI_NETNS=/run/netns/bai-test-ns \
    CNI_IFNAME=baimulti0 CNI_PATH=/usr/local/libexec/cni /usr/local/libexec/cni/bridge
```

Result: `baibr4097` created on host, `baimulti0` created inside the netns with a
session-subnet IP `10.128.5.2` (from `10.128.5.0/24`); `CNI_COMMAND=DEL` cleaned up. ✅

## 3. etcd IPAM CAS (SubnetAllocator / put_if_absent)

Ran `SubnetAllocator` against a real etcd (v3.5) via the client SDK:

- 4 concurrent `acquire()` over a `/24` split into `/26` → 4 **unique** subnets.
- 5th `acquire()` → `NetworkPoolExhausted`.
- `release()` + re-`acquire()` → returns the freed block.
- Direct `put_if_absent` contention on one key → exactly `(True, False)`.

Result: allocation is conflict-free and the CAS grants a key to exactly one caller. ✅

## 4. Two-node cross-host overlay traffic (vxlan data path)

Two network namespaces (`bai-n1`/`bai-n2`) on a shared bridge underlay simulate two
nodes; each runs the backend's exact vxlan setup + `add_peer` FDB (unicast head-end
replication, `nolearning`), with a simulated container endpoint on the overlay bridge:

- node1 `10.128.5.1` ↔ node2 `10.128.5.2` (VNI 4097), peers via FDB `dst <other underlay IP>`.

Result: cross-node overlay ping `10.128.5.1 → 10.128.5.2` = 3/3 received, 0% loss;
`tcpdump` on the underlay shows the traffic is `VXLAN ... vni 4097` over UDP/4789. This
exercises encap → underlay → decap and the broadcast-FDB flood path end-to-end. ✅

## 5. Real containerd task → CNI attach (ContainerNetworkProvisioner flow)

A real containerd container/task (`ctr run alpine sleep`) starts with only `lo` in its
netns. Applying the overlay config to `/proc/<task_pid>/ns/net` (exactly
`netns_path_for_pid(pid)` + the `CniPluginRunner` protocol) via the real `bridge` plugin:

Result: `baimulti0` appears inside the container's netns with session-subnet IP
`10.128.5.3` and the correct on-link route; `CNI_COMMAND=DEL` cleans up. This validates
the exact `ContainerNetworkProvisioner.attach(task_pid=...)` path against live
containerd. ✅

## 6. Orchestrator flow with real containerd (NerdctlRuntimeClient + provisioner)

The `ContainerdKernelOrchestrator` sequence run against live containerd via nerdctl,
using the exact commands `NerdctlRuntimeClient` emits:

```sh
nerdctl --namespace backend-ai create --name c --network none alpine:3.20 sleep 600  # pid=0
nerdctl --namespace backend-ai start c                                               # -> pid
# hand /proc/<pid>/ns/net to the network layer:
echo "$OVERLAY_CONF" | env CNI_COMMAND=ADD CNI_NETNS=/proc/<pid>/ns/net CNI_IFNAME=baimulti0 ... bridge
# terminate: CNI DEL -> nerdctl kill -> nerdctl rm
```

Result: created container has pid 0 (not started); after start the netns has only `lo`;
CNI attach adds `baimulti0` + session IP `10.128.5.4` inside the real container; teardown
is clean. `--network none` keeps nerdctl out of networking, so CNI ownership stays with
the BEP-1055 layer. This validates the runtime↔network separation and the orchestrator
handoff against live containerd. ✅

## 7. Real code end-to-end (the actual classes, not shell mimics)

The actual Python classes were run on the Linux host driving live containerd + CNI (only
`ai.backend.logging` was stubbed; runtime/network modules are the real source):

```python
rt = NerdctlRuntimeClient(subprocess_runner, namespace="backend-ai")
await rt.pull_image(IMAGE)
await rt.create_container(C, image_ref=IMAGE, command=["sleep","600"], oci_spec={})
handle = await rt.start_container(C)                     # -> pid
attacher = CniAttacher(CniPluginRunner(cni_path="/usr/local/libexec/cni"))
await attacher.attach(plan, container_id=C, netns=netns_path_for_pid(handle.pid))
```

Result: `NerdctlRuntimeClient.{image_exists,pull_image,create_container,start_container}`
and `CniAttacher.attach`/`CniPluginRunner` (real `bridge` plugin exec) ran unmodified; the
real container received overlay IP `10.128.5.5/24`; `detach`/`kill_container`/
`remove_container` cleaned up. This validates the actual runtime + CNI code paths, not
just equivalent shell commands. ✅

## 8. Per-session isolation (same node, different sessions)

Two sessions co-located on one host, each with its own overlay bridge + subnet
(session A: `baibr4097` / `10.128.5.0/24`; session B: `baibr5000` / `10.128.6.0/24`):
containers `cA1`, `cA2` in A and `cB` in B, attached via the bridge CNI plugin.

Connectivity matrix (via `ping` from each container's netns):

| from → to | same/cross session | result |
|-----------|--------------------|--------|
| cA1 → cA2 | same | **REACHABLE** |
| cA1 → cB  | cross | **BLOCKED** |
| cB → cA1  | cross | **BLOCKED** |

Same-session containers reach each other; cross-session traffic is blocked even though
both sessions run on the same node — separate session bridges (a container only has an
on-link route to its own session subnet) mean there is no path between sessions. This is
the core multi-tenant requirement (different orgs sharing a node). ✅

Scope: this exercises OVERLAY isolation with pure overlay attachments (no LOCAL/egress
interface). In production the LOCAL interface's egress paths remain per the Swarm-parity
scope (egress firewall is out of scope — see data-plane-backends.md). Cross-*node*
isolation (two VNIs over vxlan on two hosts) uses the same separate-bridge/VNI mechanism
but is not yet exercised end-to-end.

## 9. Egress (LOCAL) + a finding: ICC-off is NOT free with stock bridge CNI

Attaching the LOCAL/egress interface (isGateway + isDefaultGateway + ipMasq) alongside
the overlay:

- **Egress works:** the container gets a default route via the LOCAL bridge gateway and
  reaches the host (bridge gateway IP). (External-internet ICMP is blocked by the lima
  user-mode network, not our config.)
- **Finding — a shared per-node LOCAL bridge leaks across sessions:** two different-session
  containers both attached to one shared `bai-local0` bridge could ping each other
  (`172.30.0.2 ↔ 172.30.0.3` = REACHABLE). The stock CNI `bridge` plugin does **not**
  implement ICC-off (`hairpinMode:false` does not block inter-container traffic); Swarm's
  ICC-off came from Docker's own iptables. So the earlier "LOCAL is egress-only
  (Swarm-parity ICC-off)" claim is **not** satisfied by a shared bridge alone.
- **Fix (verified):** make the LOCAL bridge **per-session** (like the overlay bridge).
  With `bai-localA`/`172.30.5.0/24` for session A and `bai-localB`/`172.30.6.0/24` for
  session B: each container still reaches its gateway (egress ✅) while cross-session
  traffic over LOCAL is **BLOCKED** — the same "separate bridge = isolated" mechanism as
  §8, no ICC-off firewall rules needed.

Consequence: the LOCAL interface is **per session**, not a single node-shared bridge; its
NAT subnet is a node-local per-session allocation (behind NAT, so no cross-node
coordination). See the Decision Log entry.

**Rejected alternative — fold egress into the overlay bridge (option C):** instead of a
separate LOCAL bridge, put the gateway IP + masquerade on the per-session overlay bridge
(one bridge doing overlay + egress). Tested on two nodes: because the overlay subnet is a
single L2 stretched across nodes via vxlan, a **shared** gateway IP (`10.128.5.1` on every
node) is a duplicate IP on that L2 — the container could not stably resolve its gateway.
Per-node **distinct** gateways avoid the duplicate but must be carved from the overlay
subnet per node (consuming overlay IPs) and require the container's default route to point
at its local node's gateway. Option B keeps egress on a node-local (non-stretched) subnet,
sidestepping the conflict entirely; the one extra bridge per session is the price for a
conflict-free, firewall-free egress. B chosen.

## 10. Option B end-to-end (overlay + per-session LOCAL) on real containerd

Real containers (nerdctl `--network none`) each attached to their session's overlay
bridge AND a per-session LOCAL bridge on a node-local subnet (session A:
`baibr4097`/`10.128.5.0/24` + `bailo4097`/`172.30.0.0/24`; session B: `baibr5000` +
`bailo5000`/`172.30.1.0/24`):

- **Dual interface + routing:** each container gets `baimulti0` (overlay) + `eth0`
  (LOCAL) with `default via 172.30.0.1` (its LOCAL gateway). ✅
- **Egress path:** `ipMasq` installs per-container SNAT rules; the container reaches its
  LOCAL gateway (host) and the host's real interface (`192.168.5.15`). ✅ (Full
  public-internet egress was not confirmed — the lima user-mode network double-NATs
  container-subnet traffic; on a real host this is the standard Docker-bridge egress
  path.)
- **Isolation matrix (same node):**

  | from → to | scope | result |
  |-----------|-------|--------|
  | cA1 → cA2 overlay | same session | REACHABLE |
  | cA1 → cB overlay | cross session | BLOCKED |
  | cA1 → cB **LOCAL** | cross session | **BLOCKED** |

Per-session LOCAL bridges give egress + cross-session isolation on both the overlay and
the egress path, with no ICC-off firewall and no stretched-L2 gateway conflict —
confirming option B end to end. ✅

## 11. Real two-host cross-node overlay + VNI isolation (separate VMs)

Two **separate Linux VMs** on a shared L2 (lima socket_vmnet, `192.168.105.20` and
`.10`), each running the backend's vxlan setup with the FDB pointing at the other host:

- **Cross-node overlay (same session):** an endpoint on host A (`10.128.5.10`, VNI 4097)
  pings an endpoint on host B (`10.128.5.20`, VNI 4097): 3/3, 0% loss; `tcpdump` on the
  underlay shows `192.168.105.10 → .20:4789 VXLAN vni 4097`. Real encap/decap between two
  actual hosts. ✅
- **Cross-node VNI isolation (rigorous):** host B also runs session B on a **different
  VNI (5000) but the same subnet** `10.128.5.0/24`, endpoint `10.128.5.30`. From host A's
  session-A endpoint (`10.128.5.10`), pinging `10.128.5.30` is **BLOCKED** despite being
  on-link (same /24), while `10.128.5.20` (same VNI) is REACHABLE. Different VNI ⇒
  different L2 segment ⇒ isolated even with an overlapping subnet, across real hosts. ✅

This upgrades §4 (single-host netns simulation) to two genuine hosts and confirms both
cross-node connectivity and per-session VNI isolation on real infrastructure.

## Notes

- These are manual smoke tests requiring a privileged Linux host (NET_ADMIN),
  CNI plugins under `CNI_PATH`, and a reachable etcd — not part of the unit-test
  suite. Re-run them on the target fleet before enabling `default_driver="cni"`.
- Cross-node vxlan (§4) was validated via two netns over a shared underlay on one host;
  two separate physical/VM hosts on the same L2 remain to be tested but exercise the
  identical data path.
- The full containerd task-lifecycle gRPC client (image scan/pull, container/task create,
  snapshotter, OCI spec generation) is a large separate track — comparable in size to
  DockerAgent — and is being developed on `feat/containerd-agent-prototype` (CRI gRPC
  path). BEP-1055 owns only the network stack; `ContainerdAgent.start_container` will
  create the task there and call `ContainerNetworkProvisioner.attach(task_pid=...)`,
  which §5 already validates against live containerd.
