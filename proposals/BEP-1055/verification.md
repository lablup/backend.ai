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

## Notes

- These are manual smoke tests requiring a privileged Linux host (NET_ADMIN),
  CNI plugins under `CNI_PATH`, and a reachable etcd — not part of the unit-test
  suite. Re-run them on the target fleet before enabling `default_driver="cni"`.
- Not yet exercised end-to-end: multi-node cross-host traffic between two real hosts
  (requires two nodes on the same L2) and the containerd task -> netns wiring in
  `ContainerNetworkProvisioner` against a live containerd.
