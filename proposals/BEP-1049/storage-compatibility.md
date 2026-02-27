<!-- context-for-ai
type: detail-doc
parent: BEP-1049 (Kata Containers Agent Backend)
scope: Volume mount compatibility between host filesystem and Kata guest VM via virtio-fs
depends-on: [kata-agent-backend.md, configuration-deployment.md]
key-decisions:
  - No new storage interface needed; virtio-fs is the transparent compatibility layer
  - Existing Mount abstraction (BIND, source, target, permission) reused unchanged
  - Kata shim translates bind mounts to virtio-fs shares automatically
  - Specific mounts require Kata-specific handling (lxcfs, agent socket, tmpfs scratch)
  - virtio-fs for all storage backends; direct guest mount not proposed (no vendor Kata integration, CephFS benchmarks favor virtio-fs)
-->

# BEP-1049: Storage and Volume Mount Compatibility

## Summary

Backend.AI's existing `Mount` abstraction (bind mount with source path, target path, and permission) works unchanged for KataAgent. The Kata runtime shim automatically translates host-side bind mounts into virtio-fs shares exposed to the guest VM — no new storage management interface is required. This document details the compatibility layer, identifies mounts that require Kata-specific handling, and analyzes the I/O performance implications.

## Current Design: Docker Bind Mount Path

When `DockerAgent` creates a container, all storage mounts follow a single path:

```
Host filesystem ──(Linux bind mount)──→ Container mount namespace
```

This is zero-overhead because Docker containers share the host kernel's VFS. The mount specification flows through:

1. Manager resolves `VFolderMount.host_path` via Storage Proxy (`get_mount_path()` RPC)
2. Agent constructs `Mount(MountTypes.BIND, host_path, kernel_path, permission)`
3. `process_mounts()` converts to Docker API format: `{"Type": "bind", "Source": "...", "Target": "..."}`
4. Docker creates the bind mount in the container's mount namespace

Key files:
- `VFolderMount` type: `src/ai/backend/common/types.py:1299`
- `mount_vfolders()`: `src/ai/backend/agent/docker/agent.py:557`
- `get_intrinsic_mounts()`: `src/ai/backend/agent/docker/agent.py:512`
- `process_mounts()`: `src/ai/backend/agent/docker/agent.py:764`

### Mount Inventory (DockerAgent)

| Mount Point | Source | Type | Permission | Count |
|-------------|--------|------|------------|-------|
| `/home/config` | `scratch_dir/config` | BIND | RO | 1 |
| `/home/work` | `scratch_dir/work` | BIND | RW | 1 |
| `/tmp` | `scratch_dir_tmp` (tmpfs) | BIND | RW | 1 |
| `/etc/localtime` | Host `/etc/localtime` | BIND | RO | 1 |
| `/etc/timezone` | Host `/etc/timezone` | BIND | RO | 1 |
| `/var/lib/lxcfs/proc/*` | Host lxcfs | BIND | RW | 4-6 |
| `/var/lib/lxcfs/sys/...` | Host lxcfs | BIND | RW | 1-2 |
| `/opt/kernel/agent.sock` | Agent Unix socket | BIND | RW | 1 |
| `/home/work/{vfolder}` | NFS/CephFS/local path | BIND | RO/RW | 0-N |
| Image-defined volumes | Docker named volumes | VOLUME | varies | 0-N |
| KRunner binaries | Host package path | BIND | RO | 1-3 |

Total: **12-20+ mounts** per container.

## Proposed Design: virtio-fs Compatibility Layer

### How Kata Handles Bind Mounts

When a container is created via containerd with the Kata runtime class, the Kata shim **automatically** translates bind mount specifications into virtio-fs shares:

```
                         HOST SIDE                           │  GUEST VM SIDE
                                                             │
Host filesystem path                                         │
  (/mnt/vfolders/project)                                    │
         │                                                   │
         ▼                                                   │
  ┌──────────────┐                                           │
  │  virtiofsd   │  (FUSE server, one per sandbox)           │
  │  daemon      │                                           │
  └──────┬───────┘                                           │
         │  virtio-fs device                                 │
─────────┼───────────────────────────────────────────────────┼──── VM boundary (KVM)
         │                                                   │
         ▼                                                   │
  ┌──────────────┐                                           │
  │  virtio-fs   │  (guest kernel FUSE client)               │
  │  mount       │                                           │
  └──────┬───────┘                                           │
         │                                                   │
         ▼                                                   │
  Container mount namespace                                  │
  (/home/work/project)                                       │
```

The Kata shim handles this translation internally:
1. Reads bind mount specs from the OCI runtime config
2. Configures virtiofsd to serve the host directories
3. Inside the guest, kata-agent mounts the virtio-fs share
4. kata-agent creates the container's mount namespace with the target paths

**No changes to the `Mount` abstraction are needed.** The `KataKernelCreationContext.process_mounts()` method passes the same `Mount(BIND, source, target, permission)` objects to containerd, and the Kata shim does the rest.

### KataAgent process_mounts() Implementation

```python
async def process_mounts(self, mounts: Sequence[Mount]) -> None:
    """Convert Backend.AI mounts to containerd mount specs.

    For Kata containers, bind mounts are automatically translated
    to virtio-fs shares by the Kata shim — we just pass them through
    as standard OCI bind mounts.
    """
    oci_mounts = []
    for mount in mounts:
        if mount.type == MountTypes.BIND:
            oci_mounts.append({
                "destination": str(mount.target),
                "source": str(mount.source),
                "type": "bind",
                "options": self._build_mount_options(mount),
            })
        elif mount.type == MountTypes.TMPFS:
            oci_mounts.append({
                "destination": str(mount.target),
                "type": "tmpfs",
                "options": ["nosuid", "nodev", "size=65536k"],
            })
    self._container_mounts.extend(oci_mounts)
```

### Mounts Requiring Kata-Specific Handling

While most mounts work transparently via virtio-fs, several require special treatment:

#### 1. lxcfs Mounts — SKIP

lxcfs provides container-aware `/proc` and `/sys` by intercepting reads at the host kernel level. Inside a Kata VM, the guest kernel already provides accurate `/proc` and `/sys` — lxcfs is unnecessary and the host-side lxcfs paths don't exist in the guest.

```python
async def get_intrinsic_mounts(self) -> Sequence[Mount]:
    mounts = []
    # ... scratch dirs, timezone, etc. ...

    # SKIP lxcfs mounts — guest kernel provides accurate proc/sys
    # (Docker mounts /var/lib/lxcfs/proc/cpuinfo, meminfo, etc.)
    # These are host-kernel features that don't apply inside a VM.

    return mounts
```

#### 2. Agent Socket — VSOCK or TCP Instead of Unix Socket

The kernel-to-agent IPC socket (`/opt/kernel/agent.sock`) is a Unix domain socket that the container process uses to communicate with the Backend.AI agent process on the host. Unix sockets cannot cross the VM boundary.

**Options:**

**Option A: TCP over virtio-net (simpler)**
- Agent listens on a TCP port reachable via the guest's virtual network
- Container connects to `$BACKENDAI_AGENT_HOST:$BACKENDAI_AGENT_PORT`
- Pros: works with existing code; just change the address
- Cons: slightly higher latency than Unix socket

**Option B: VSOCK (lower latency)**
- Agent listens on a VSOCK socket (`AF_VSOCK`, CID=host, port=N)
- Container connects to `VMADDR_CID_HOST:port`
- Pros: purpose-built for host-guest communication, no network stack overhead
- Cons: requires VSOCK-aware socket code in both agent and kernel runner

**Recommendation: Option A (TCP)** for Phase 1 — simpler, proven, sufficient performance. VSOCK optimization can be added later if latency matters.

```python
# In KataKernelCreationContext.prepare_scratch():
# Instead of mounting agent.sock, set environment variables for TCP connection
environ["BACKENDAI_AGENT_CONNECT"] = "tcp"
environ["BACKENDAI_AGENT_HOST"] = self._agent_rpc_host  # host IP reachable from guest
environ["BACKENDAI_AGENT_PORT"] = str(self._agent_rpc_port)
```

#### 3. Scratch Directories — virtio-fs with Shared Lifecycle

Scratch directories (`/home/config`, `/home/work`) are created on the host by the agent and shared into the guest via virtio-fs. This works transparently, but note:

- Files written by the agent (environ.txt, resource.txt, SSH keys) on the host side are immediately visible in the guest via virtio-fs
- Files written by the container in `/home/work` are immediately visible on the host
- This bidirectional sync is a property of virtio-fs — no additional mechanism needed

#### 4. tmpfs Scratch (`/tmp`) — Guest-Side tmpfs

For Docker, `/tmp` can be backed by a host-side tmpfs mount. For Kata, it's simpler to use a guest-side tmpfs:

```python
# Docker: Mount(BIND, host_tmpfs_path, "/tmp", RW)
# Kata:   Mount(TMPFS, None, "/tmp", RW)  — allocated inside guest RAM
```

This avoids sharing temporary files across the VM boundary unnecessarily.

#### 5. KRunner Binaries — Guest Rootfs or virtio-fs

KRunner binaries (`/opt/kernel/entrypoint.sh`, `/usr/local/bin/*`) are mounted from the agent's host-side package in Docker. For Kata, two approaches:

**Option A: Include in guest rootfs image** (recommended for production)
- Bake krunner binaries into the Kata guest rootfs at image build time
- Pros: no mount needed, faster startup
- Cons: guest rootfs must be rebuilt when krunner is updated

**Option B: Share via virtio-fs** (simpler for development)
- Mount krunner host directory into guest via virtio-fs (same as Docker bind mount)
- Pros: always up-to-date, no image rebuild
- Cons: adds another virtio-fs share

**Recommendation: Option B** for Phase 1 (development velocity), migrate to Option A for production.

### Mount Compatibility Matrix

| Mount | Docker | Kata | Handling |
|-------|--------|------|----------|
| `/home/config` (scratch) | Bind mount | virtio-fs (transparent) | Same `Mount` spec |
| `/home/work` (scratch) | Bind mount | virtio-fs (transparent) | Same `Mount` spec |
| `/tmp` (tmpfs) | Host tmpfs bind | Guest-side tmpfs | Change to `TMPFS` type |
| `/etc/localtime` | Bind mount | virtio-fs (transparent) | Same `Mount` spec |
| `/etc/timezone` | Bind mount | virtio-fs (transparent) | Same `Mount` spec |
| lxcfs `/proc/*`, `/sys/*` | Bind mount | **Skip** | Not applicable in VM |
| `/opt/kernel/agent.sock` | Bind mount (Unix socket) | **TCP or VSOCK** | Replace with env vars |
| VFolders (`/home/work/*`) | Bind mount | virtio-fs (transparent) | Same `Mount` spec |
| KRunner binaries | Bind mount | virtio-fs or guest rootfs | Phase-dependent |
| Docker named volumes | Docker volume | **Not applicable** | Skip or convert to bind |

### I/O Performance Characteristics

| Mechanism | Sequential Read | Random Write p99 | Use Case |
|-----------|----------------|-----------------|----------|
| Docker bind mount | 100% (native) | 100% (native) | Baseline |
| virtio-fs (no DAX) | 70-90% | 3-10x overhead | Default Kata |
| virtio-fs + DAX | 90-98% | 2-5x overhead | Recommended for I/O |
| virtio-9p (legacy) | ~15% | ~100x overhead | Not recommended |

For AI/ML workloads, the I/O profile matters most during data loading phases (reading training data from vfolders). GPU compute phases are unaffected by storage overhead. The virtio-fs + DAX configuration provides acceptable performance for most workloads.

**Recommendation**: Enable DAX by default in `KataConfig` (`virtio_fs_cache_size = 0` means auto-sized DAX window). This is configured in [configuration-deployment.md](configuration-deployment.md).

## Interface / API

No new storage interfaces are introduced. The existing abstractions are reused:

| Abstraction | Location | Change for Kata |
|-------------|----------|-----------------|
| `VFolderMount` | `src/ai/backend/common/types.py:1299` | None |
| `Mount` / `MountTypes` | `src/ai/backend/common/types.py:612` | None |
| `MountPermission` | `src/ai/backend/common/types.py:603` | None |
| `mount_vfolders()` | Agent method | Reuse as-is |
| `get_intrinsic_mounts()` | Agent method | Override to skip lxcfs, handle agent socket |
| `process_mounts()` | Agent method | Override to produce OCI mount format (vs Docker API format) |

## Implementation Notes

- The virtiofsd daemon is managed by the Kata shim, not by the Backend.AI agent. No virtiofsd lifecycle code is needed in KataAgent.
- virtio-fs shares are set up per-sandbox (per-VM). Multiple containers in the same Kata sandbox share the same virtio-fs instance. Since Backend.AI uses one container per session (one sandbox per container), this is a 1:1 mapping.
- File ownership (UID/GID) is preserved across the virtio-fs boundary. The `kernel_uid`/`kernel_gid` settings work as expected.
- Symbolic links within mounted directories work correctly with virtio-fs.
- File locking (flock, fcntl) works with virtio-fs but may have different semantics for distributed filesystems (CephFS, NFS) that are already mounted on the host.
- For confidential computing (Phase 4), bind mounts are **NOT sync'd back** — files are copied into the guest at mount time and changes are lost. This is a fundamental CoCo limitation documented in [TR-2026-001](../../docs/reports/kata-containers-feature-parity-analysis.md). Non-confidential Kata mode does not have this limitation.

## Direct Storage Access from Guest VMs

### Motivation

Backend.AI supports 12+ storage backends (`vfs`, `xfs`, `netapp`, `dellemc-onefs`, `weka`, `gpfs`, `cephfs`, `vast`, `exascaler`, `purestorage`, `hammerspace`, etc.), each exposing vfolders to agent hosts via different protocols. The default design passes all storage through virtio-fs — the host mounts the storage, and virtiofsd shares it into the guest. This section evaluates whether any storage providers could be mounted **directly inside the guest VM**, bypassing the virtio-fs layer.

### Storage Provider Protocol Survey

| Provider | Client Protocol | Native VM Client Feasible? | Notes |
|----------|----------------|---------------------------|-------|
| VAST | NFS v3/v4 | Yes (NFS client in guest) | Pure NFS appliance; no vendor-specific VM integration |
| NetApp ONTAP | NFS v3/v4/v4.1 | Yes (NFS client in guest) | Supports KVM environments via NFS; no Kata-specific support |
| Weka | NFS v3/v4.1 or WekaFS POSIX | NFS: Yes; WekaFS: No | WekaFS native client requires SR-IOV NIC passthrough in VMs — too complex |
| Pure Storage FlashBlade | NFS v3 | Yes (NFS client in guest) | Standard NFS appliance; no vendor-specific VM integration |
| Dell EMC PowerScale (OneFS) | NFS v3/v4/v4.2 | Yes (NFS client in guest) | Standard NFS; guest OS mount documented for VMware VMs |
| Hammerspace | NFS (pNFS/FlexFiles) | Yes (NFS client in guest) | Metadata orchestration layer; supports VM and container environments |
| CephFS | Kernel ceph client or NFS gateway | Yes (kernel ceph client in guest) | Native client in guest achieves ~46% of virtio-fs throughput (see benchmarks below) |
| Lustre (DDN EXAScaler) | Lustre kernel client | Possible but complex | Requires Lustre kernel modules in guest rootfs; no Kata integration exists |
| GPFS (IBM Storage Scale) | GPFS kernel client or NFS gateway | Possible but complex | CSI driver for K8s exists; native client requires cluster membership |
| XFS / VFS (local) | Local filesystem | No | Local storage is host-attached; direct guest access not applicable |

### Why virtio-fs Is the Right Default

The Kata project explicitly chose virtio-fs over network protocols for host-guest file sharing:

> "These techniques [shared memory, DAX mapping] are not applicable to network file systems since the communications channel is bypassed by taking advantage of shared memory on a local machine."

For **host-local storage** (XFS, local NVMe), virtio-fs is unambiguously faster — it uses shared memory between host and guest processes, avoiding any network stack overhead.

An early Kata RFC ([kata-containers/runtime#279](https://github.com/kata-containers/runtime/issues/279)) explored NFS-over-VSOCK as an alternative to 9p (the predecessor to virtio-fs). While optimized NFS achieved 17-35x raw R/W performance over 9p, virtio-fs with DAX superseded this approach, and the NFS-over-VSOCK kernel patches were never upstreamed.

### Double-Hop Analysis for Network Storage

For storage that is **already network-attached** (NFS, CephFS, etc.), the current design creates a double-hop:

```
Storage cluster ──(NFS/CephFS)──→ Host mount ──(virtio-fs)──→ Guest mount
```

A direct guest mount would eliminate one hop:

```
Storage cluster ──(NFS/CephFS)──→ Guest mount (directly)
```

However, benchmarks from CephFS testing on Proxmox suggest virtio-fs passthrough still outperforms direct guest mounts:

| Path | Write (MiB/s) | Read (MiB/s) |
|------|---------------|--------------|
| Host CephFS → virtio-fs → guest | 2145 | 3488 |
| Guest native ceph client → cluster | 984 | 1601 |

The virtio-fs path wins because the host-side ceph client benefits from the host page cache and DAX mapping shares this cache directly with the guest — avoiding the overhead of running a separate ceph client (with its own cache, network connections, and OSD interactions) inside the resource-constrained guest kernel.

For NFS-based providers, the comparison is less clear-cut since NFS clients are lighter weight than ceph clients, but the shared-memory advantage of virtio-fs likely still applies.

### Practical Barriers to Direct Guest Mount

Even where technically feasible, direct guest NFS mount has significant practical issues:

1. **Guest kernel configuration**: The default Kata guest kernel does not include NFS client modules. A custom kernel with `CONFIG_NFS_FS=y`, `CONFIG_NFS_V4=y` is required. Kata [issue #10509](https://github.com/kata-containers/kata-containers/issues/10509) documents that even after adding NFS support, automatic volume mounts fail silently — only manual mounts work.

2. **Network connectivity**: The guest must have network access to the storage cluster. In the virtio-fs model, only the host needs storage network access — the guest's network is limited to the container workload's needs.

3. **Credential management**: NFS exports, CephFS keyrings, Lustre/GPFS client configurations must be provisioned inside the guest. This conflicts with the security model — especially for confidential computing where minimizing guest configuration surface is important.

4. **Mount lifecycle**: Backend.AI's agent manages mount lifecycle (create scratch dirs, write config files, clean up). With virtio-fs, this host-side management works transparently. Direct guest mounts would require the agent to coordinate mount operations inside the guest via kata-agent or containerd exec.

5. **Storage proxy integration**: Backend.AI's Storage Proxy resolves `host_path` for vfolders. These paths are host-local. Direct guest mount would require the guest to resolve storage paths independently, bypassing the Storage Proxy entirely.

### Recommendation

**Use virtio-fs for all storage backends.** The double-hop overhead is acceptable because:

- virtio-fs + DAX provides 90-98% native read performance — the dominant I/O pattern for AI/ML workloads (reading training data)
- The host page cache is shared with the guest via DAX, effectively giving the guest "free" caching
- The architecture remains simple — one storage path for all backends, no guest-side storage configuration
- No vendor offers built-in Kata/Firecracker integration that would justify a separate code path

Direct guest mount (NFS or native client) could be revisited as a future optimization if specific workloads demonstrate that the virtio-fs write overhead (2-5x for random writes with DAX) is a bottleneck. This would require:
- Custom guest kernel with NFS/client modules
- A new mount type or annotation to signal "direct guest mount" for specific vfolders
- Guest-side mount credential provisioning via kata-agent

This is **not proposed for the initial implementation**.
