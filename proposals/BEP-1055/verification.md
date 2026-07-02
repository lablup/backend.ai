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
