<!-- context-for-ai
type: detail-doc
parent: BEP-1049 (Kata Containers Agent Backend)
scope: Multi-container networking for Kata VMs — Calico CNI integration, inter-VM communication, network policy, service port exposure
depends-on: [kata-agent-backend.md, configuration-deployment.md]
key-decisions:
  - Calico CNI for inter-VM networking (multi-host routing, network policy enforcement)
  - TC filter mechanism provides transparent veth-to-tap redirection (Kata built-in)
  - DNS resolution via /etc/hosts injection (no Docker DNS available)
  - Service port exposure via host port mapping on tap interfaces
  - No host network mode support (architectural limitation of VM isolation)
  - Calico standalone mode with etcd datastore for non-Kubernetes deployments
-->

# BEP-1049: Multi-Container Networking

## Summary

Backend.AI supports multi-container sessions (clusters) where containers communicate via a shared bridge network with hostname-based DNS resolution. For KataAgent, each container runs in its own VM, so inter-container networking becomes inter-VM networking. This document analyzes Kata's networking model, specifies Calico CNI as the required networking layer, and details the integration design for both standalone containerd and Kubernetes deployments.

## Current Design: DockerAgent Networking

DockerAgent uses Docker bridge networks for container communication. For single-container sessions, the default bridge provides connectivity with service ports (SSH, ttyd, Jupyter) mapped to host ports from a configured range (default: 30000-31000). For multi-container sessions, a dedicated bridge is created per cluster via `create_local_network()` (`src/ai/backend/agent/agent.py:3496`), and containers join with cluster hostnames as DNS aliases (`src/ai/backend/agent/docker/agent.py:680`). Docker's embedded DNS resolves these hostnames for inter-container communication.

Backend.AI has a network plugin system (`src/ai/backend/agent/plugin/network.py`) with `AbstractNetworkAgentPlugin` supporting `join_network()`, `leave_network()`, and `expose_ports()`. Built-in plugins include `OverlayNetworkPlugin` (Docker overlay for multi-host) and `HostNetworkPlugin` (host network mode).

## Kata Containers Networking Model

### Per-VM Network Path

Kata transparently bridges the host-side network namespace into the guest VM using TC (Traffic Control) filter redirection:

```
                   HOST SIDE                        │  GUEST VM SIDE
                                                    │
  CNI assigns IP to container namespace             │
  ┌──────────┐                                      │
  │  eth0    │  (veth pair, container namespace)     │
  │  (veth)  │                                      │
  └────┬─────┘                                      │
       │  TC filter: eth0 ingress → tap0 egress     │
       │  TC filter: tap0 ingress → eth0 egress     │
  ┌────┴─────┐                                      │
  │ tap0_kata│  (TAP device)                        │
  └────┬─────┘                                      │
───────┼────────────────────────────────────────────┼──── VM boundary (KVM)
       │  virtio-net                                │
  ┌────┴─────┐                                      │
  │   eth0   │  (guest interface, same IP as host   │
  │          │   veth — transparent to CNI)          │
  └──────────┘                                      │
```

This TC filter mechanism is Kata's default and requires no additional configuration. The guest VM's `eth0` gets the same IP address that the CNI assigned to the host-side veth, making the VM transparent to the network infrastructure.

### Sandbox Model: Multiple Containers Per VM

A Kata **sandbox** is a single VM instance. The kata-agent inside the guest can manage multiple containers within the same sandbox — each container gets its own PID namespace (via libcontainer) but **shares the VM's network namespace**. All containers in the same sandbox communicate via `localhost`, consistent with Kubernetes pod semantics.

The flow for multi-container sandboxes:
1. CRI creates a sandbox → Kata boots the VM, kata-agent starts
2. CRI calls `CreateContainer` → kata-agent creates a container inside the existing VM (image rootfs shared via virtio-fs or hot-plugged as a block device)
3. Additional `CreateContainer` calls → more containers in the same VM, sharing network

For Backend.AI's **multi-container sessions** (cluster mode), the mapping depends on deployment model:
- **Single-host cluster**: All containers in the session can share one Kata sandbox (one VM) using the containerd Sandbox API (`sandbox.v1`, containerd v2+). The agent calls `create_sandbox()` first, then adds containers into it via `create_container(sandbox_id=...)`. Containers share `localhost` and the VM's network namespace. Note: the standard `containers.v1` / `tasks.v1` APIs create one VM per container — the Sandbox API is required for sharing.
- **Multi-host cluster**: Each host runs a separate Kata sandbox (separate VM). Containers across VMs communicate via Calico CNI — each VM gets its own IP, and inter-VM traffic flows through BGP/VXLAN routing. This is the expected model for distributed training workloads.

### What Kata Provides Built-In

| Feature | Support | Notes |
|---------|---------|-------|
| TC filter veth↔tap redirection | Built-in (default) | Transparent to CNI plugins |
| MACVTAP mode | Built-in (legacy) | Alternative to TC filter, similar performance |
| virtio-net device | Built-in | Para-virtualized NIC inside guest |
| CNI plugin compatibility | Full | Works with Calico, Cilium, Flannel, bridge |
| Multi-container sandbox | Supported | Containers share VM network namespace via kata-agent |
| `--net=host` | **Not supported** | VM isolation prevents host network access |
| `--net=container:<id>` | **Not supported** | Cannot share network namespace across VMs |
| Docker Compose custom networks | **Limited** | Docker DNS service not fully compatible |

### What Kata Does NOT Provide

Kata has **no built-in inter-VM networking solution**. Each VM is an isolated network endpoint. Inter-VM communication depends entirely on the underlying CNI plugin — with Kubernetes, the cluster's CNI handles pod-to-pod networking transparently; without Kubernetes, a CNI plugin must be configured explicitly on each host.

### CNI Compatibility Assessment

| CNI Plugin | Kata Compatibility | Multi-Host | Network Policy | Assessment |
|------------|-------------------|------------|---------------|------------|
| **Calico** | Works with TC filter | BGP / VXLAN / IPIP | Full (L3/L4) | **Selected** — multi-host + policy + standalone support |
| Cilium | Known [MTU mismatch](https://docs.cilium.io/en/stable/network/kubernetes/kata/) | VXLAN / Geneve | Full (L3/L4/L7) | MTU issues with Kata; eBPF requires Kubernetes |
| Flannel | Works with TC filter | VXLAN | None | No network policy; insufficient for multi-tenant isolation |
| CNI bridge | Works with TC filter | **Single-host only** | None | Development/testing only |

## Proposed Design: Calico CNI Integration

### Why Calico

KataAgent requires Calico as the CNI networking layer for the following reasons:

1. **Multi-host networking**: Production deployments span multiple agent hosts. Calico provides cross-host routing via BGP (direct peering or route reflectors) or VXLAN overlay — containers on different hosts can communicate transparently.
2. **Network policy enforcement**: In a multi-tenant GPU environment, sessions from different users must be isolated at the network level. Calico's Felix agent programs iptables/eBPF rules to enforce `NetworkPolicy`-style rules between Kata VMs, preventing unauthorized inter-session traffic.
3. **Kata TC filter transparency**: Calico creates veth pairs in the container network namespace. Kata's TC filter redirects traffic from the veth to a tap device and into the VM. From Calico's perspective, the Kata VM is indistinguishable from a regular container — no special integration needed.
4. **Standalone containerd support**: Calico supports non-Kubernetes deployments using etcd as its datastore. The `calico-node` agent (Felix + BIRD) runs on each host, and the Calico CNI plugin is invoked by containerd. This matches KataAgent's containerd-based architecture.
5. **Kubernetes compatibility**: When KataAgent is deployed on Kubernetes, the cluster's existing Calico installation handles networking — no additional configuration needed. This provides a consistent networking model across deployment modes.

### Calico Architecture with Kata

```
  Agent Host A                              Agent Host B
 ┌─────────────────────────────────┐      ┌─────────────────────────────────┐
 │  ┌──────────┐   ┌──────────┐   │      │  ┌──────────┐   ┌──────────┐   │
 │  │ Kata VM  │   │ Kata VM  │   │      │  │ Kata VM  │   │ Kata VM  │   │
 │  │ (sess-1) │   │ (sess-2) │   │      │  │ (sess-3) │   │ (sess-4) │   │
 │  └──┬───────┘   └──┬───────┘   │      │  └──┬───────┘   └──┬───────┘   │
 │     │ virtio-net    │           │      │     │              │           │
 │  ┌──┴───┐       ┌──┴───┐       │      │  ┌──┴───┐       ┌──┴───┐       │
 │  │ tap0 │       │ tap0 │       │      │  │ tap0 │       │ tap0 │       │
 │  └──┬───┘       └──┬───┘       │      │  └──┬───┘       └──┬───┘       │
 │     │ TC filter     │           │      │     │              │           │
 │  ┌──┴───┐       ┌──┴───┐       │      │  ┌──┴───┐       ┌──┴───┐       │
 │  │ veth │       │ veth │       │      │  │ veth │       │ veth │       │
 │  └──┬───┘       └──┬───┘       │      │  └──┬───┘       └──┬───┘       │
 │     └───────┬───────┘           │      │     └───────┬───────┘           │
 │         ┌───┴────┐              │      │         ┌───┴────┐              │
 │         │ Felix  │ (policy)     │      │         │ Felix  │ (policy)     │
 │         │ BIRD   │ (BGP)       │      │         │ BIRD   │ (BGP)       │
 │         └───┬────┘              │      │         └───┬────┘              │
 └─────────────┼───────────────────┘      └─────────────┼───────────────────┘
               │         BGP peering / VXLAN            │
               └────────────────────────────────────────┘
```

**Felix** programs iptables rules on each host to enforce network policies between Kata VMs. **BIRD** exchanges routing information so that VMs on Host A can reach VMs on Host B via BGP or VXLAN encapsulation.

### Deployment Modes

#### Standalone containerd (non-Kubernetes)

Calico runs in standalone mode with etcd as the datastore:

**Components per host:**
- `calico-node` service (Felix + BIRD daemons)
- Calico CNI plugin binary (`/opt/cni/bin/calico`)
- Calico IPAM plugin binary (`/opt/cni/bin/calico-ipam`)

**Infrastructure:**
- etcd cluster (can share Backend.AI's existing etcd, or separate)
- `calicoctl` CLI for IP pool and network policy management

**CNI configuration** (`/etc/cni/net.d/10-calico.conflist`):

```json
{
  "name": "kata-calico",
  "cniVersion": "1.0.0",
  "plugins": [
    {
      "type": "calico",
      "datastore_type": "etcdv3",
      "etcd_endpoints": "http://127.0.0.1:2379",
      "ipam": {
        "type": "calico-ipam",
        "assign_ipv4": "true"
      },
      "policy_type": "calico",
      "log_level": "info"
    },
    {
      "type": "portmap",
      "capabilities": {"portMappings": true},
      "snat": true
    }
  ]
}
```

**IP pool configuration** (via `calicoctl`):

```yaml
apiVersion: projectcalico.org/v3
kind: IPPool
metadata:
  name: kata-sessions
spec:
  cidr: 10.244.0.0/16
  ipipMode: Never
  vxlanMode: CrossSubnet    # VXLAN for cross-subnet, direct for same-subnet
  natOutgoing: true
  nodeSelector: all()
```

#### Kubernetes deployment

When KataAgent is deployed on a Kubernetes cluster with Calico already installed, no additional CNI configuration is needed. The existing Calico installation handles:

- IP allocation via Calico IPAM
- Cross-node routing via BGP or VXLAN
- Network policy enforcement via Felix

`create_local_network()` is a no-op (same as KubernetesAgent) — Kubernetes Services and DNS handle inter-pod discovery.

### Network Policy for Session Isolation

Calico network policies prevent unauthorized traffic between sessions. The agent labels each Kata VM's network endpoint with session metadata, and a default-deny policy isolates sessions from each other:

```yaml
# Default deny: sessions cannot reach other sessions
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: default-deny-inter-session
spec:
  selector: has(ai.backend.session-id)
  types:
  - Ingress
  - Egress
  ingress:
  - action: Deny
    source:
      notSelector: ai.backend.session-id == "{{session_id}}"
  egress:
  - action: Allow   # Allow outbound (storage, internet)
```

```yaml
# Allow intra-cluster: containers in the same session can communicate
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: allow-intra-session
spec:
  selector: has(ai.backend.session-id)
  order: 100
  types:
  - Ingress
  ingress:
  - action: Allow
    source:
      selector: ai.backend.session-id == "{{session_id}}"
```

Note: The `{{session_id}}` placeholders above are **templates** — Calico does not support variable substitution in policy YAML. The agent generates per-session policies with actual session IDs substituted programmatically before applying via `calicoctl apply`.

KataAgent applies these labels when creating containers via containerd, and Calico's Felix agent enforces the rules in real-time on the host's iptables.

### Single-Container Sessions

For single-container sessions, Calico provides connectivity:

1. Containerd invokes the Calico CNI plugin when creating the container's network namespace
2. Calico assigns an IP from the configured IP pool and programs routes on the host
3. Kata's TC filter redirects traffic from the Calico-created veth to a tap device
4. The guest VM gets the Calico-assigned IP, reachable from other hosts via BGP/VXLAN
5. Service ports are exposed via the portmap CNI plugin

### Multi-Container Sessions (Clusters)

For multi-container sessions, all containers in the cluster receive IPs from the same Calico IP pool and are labeled with the same `session-id`. The network policy allows intra-session traffic while blocking inter-session traffic.

`create_local_network()` for Calico standalone mode ensures the session's network policy rules are applied:

```python
async def create_local_network(self, network_name: str) -> None:
    """Apply Calico network policy for inter-VM cluster communication."""
    session_id = network_name  # network_name is derived from session_id
    # Apply session-scoped network policy via calicoctl
    await self._apply_calico_policy(session_id)

async def destroy_local_network(self, network_name: str) -> None:
    """Remove session-scoped Calico network policy."""
    session_id = network_name
    await self._remove_calico_policy(session_id)
```

Containers within the same cluster can reach each other by IP. Hostname resolution is handled by `/etc/hosts` injection (see below).

### DNS / Hostname Resolution

Docker provides embedded DNS for container-to-container name resolution. Kata with standalone containerd does **not** have this. KataAgent must handle hostname resolution explicitly.

**Approach: `/etc/hosts` injection**

After all containers in a cluster are created and have IPs assigned, KataAgent writes `/etc/hosts` entries into each container's scratch directory (shared via virtio-fs):

```python
async def _inject_cluster_hosts(
    self,
    cluster_info: ClusterInfo,
    containers: dict[str, ContainerInfo],  # hostname → container info
) -> None:
    """Write /etc/hosts with cluster hostname mappings into each container."""
    hosts_entries = []
    for hostname, info in containers.items():
        hosts_entries.append(f"{info.ip_address}\t{hostname}")
    hosts_content = "\n".join([
        "127.0.0.1\tlocalhost",
        "::1\tlocalhost ip6-localhost ip6-loopback",
        *hosts_entries,
    ])
    for hostname, info in containers.items():
        hosts_path = info.scratch_dir / "config" / "hosts"
        hosts_path.write_text(hosts_content)
```

The `/home/config/hosts` file is bind-mounted (via virtio-fs) as `/etc/hosts` inside the guest. This provides immediate hostname resolution without requiring a DNS server.

**Alternative considered: CoreDNS sidecar** — too heavyweight for per-cluster DNS; `/etc/hosts` is simpler and sufficient for the small number of containers in a Backend.AI cluster (typically 2-8).

### Service Port Exposure

Service ports (SSH, ttyd, Jupyter, etc.) are mapped from container ports to host ports via the CNI portmap plugin (included in the Calico conflist above). The portmap plugin programs DNAT rules to forward host ports to the VM's Calico-assigned IP — the standard CNI approach, transparent to Kata's TC filter.

### Network Plugin Compatibility

| Plugin | Docker | Kata | Notes |
|--------|--------|------|-------|
| Default | Docker bridge API | Calico CNI | Multi-host routing + network policy |
| Overlay | Docker overlay driver | Calico VXLAN mode | Cross-subnet encapsulation |
| Host | `--net=host` | **Not supported** | VM isolation prevents this |
| RDMA | Device mount | SR-IOV VF passthrough (future) | Out of scope for Phase 1 |

## Interface / API

| Abstraction | Location | Change for Kata |
|-------------|----------|-----------------|
| `create_local_network()` | `AbstractAgent` method | Apply Calico session-scoped network policy |
| `destroy_local_network()` | `AbstractAgent` method | Remove Calico session-scoped network policy |
| `apply_network()` | `KernelCreationContext` method | Assign Calico endpoint labels, configure CNI network |
| `AbstractNetworkAgentPlugin` | `src/ai/backend/agent/plugin/network.py` | Kata-specific Calico plugin implementation |
| Service port mapping | Agent port pool | Use CNI portmap plugin |
| Calico endpoint labeling | New in KataAgent | Label VMs with session-id for policy matching |

## Implementation Notes

- **Calico deployment**: Standalone mode requires `calico-node` (Felix + BIRD) on each agent host and an etcd cluster. The etcd instance can be shared with Backend.AI's existing etcd if present, or deployed separately. For Kubernetes deployments, Calico is assumed to be pre-installed as the cluster CNI.
- **Calico CNI binaries**: `calico` and `calico-ipam` plugins must be installed in `/opt/cni/bin/`. The portmap plugin (from standard CNI plugins) is also required for service port exposure.
- **TC filter**: Kata's default networking mode since v1.6. No configuration needed — the Kata shim sets up TC rules automatically when it detects a veth interface in the container namespace. This is fully transparent to Calico.
- **IP pool sizing**: The default `10.244.0.0/16` pool provides ~65k IPs. For large deployments with many concurrent sessions, consider multiple IP pools or a larger CIDR.
- **Network policy lifecycle**: Session-scoped Calico network policies are created in `create_local_network()` and removed in `destroy_local_network()`. The agent interacts with the Calico datastore (etcd or Kubernetes API) via `calicoctl` or the Calico Python client library.
- **Endpoint labeling**: Each Kata VM's network endpoint must be labeled with `ai.backend.session-id`, `ai.backend.scaling-group`, and `ai.backend.cluster-role` for policy matching. Labels are applied via Calico's workload endpoint API.
- For Kubernetes deployments, `create_local_network()` is a no-op (same as KubernetesAgent) — the cluster CNI and Kubernetes NetworkPolicy handle pod networking.
- The `gwbridge_subnet` detection and `OMPI_MCA_btl_tcp_if_exclude` logic from DockerAgent should be adapted for Calico's host-local interface to support MPI workloads.
- VSOCK could theoretically be used for inter-VM communication (each VM has a unique CID), but this requires custom socket code in user workloads and is not practical for transparent hostname-based networking.

## Host Requirements (Calico)

In addition to the Kata host requirements in [configuration-deployment.md](configuration-deployment.md), Calico requires:

| Requirement | Details |
|-------------|---------|
| `calico-node` service | Felix (policy agent) + BIRD (BGP daemon), runs as systemd unit or container |
| CNI plugins | `/opt/cni/bin/calico`, `/opt/cni/bin/calico-ipam`, `/opt/cni/bin/portmap` |
| CNI config | `/etc/cni/net.d/10-calico.conflist` |
| etcd (standalone mode) | etcd v3 cluster accessible from all agent hosts |
| `calicoctl` | CLI for IP pool and network policy management |
| Network connectivity | BGP peering (port 179) or VXLAN (UDP 4789) between agent hosts |
| IP forwarding | `net.ipv4.ip_forward = 1` (usually already enabled for Kata) |
