<!-- context-for-ai
type: detail-doc
parent: BEP-1049 (Kata Containers Agent Backend)
scope: Volume mount compatibility between host filesystem and Kata guest VM via virtio-fs; intrinsic mount evaluation
depends-on: [kata-agent-backend.md, configuration-deployment.md]
key-decisions:
  - No new storage interface needed; virtio-fs is the transparent compatibility layer
  - Existing Mount abstraction (BIND, source, target, permission) reused unchanged
  - Kata shim translates bind mounts to virtio-fs shares automatically
  - lxcfs mounts skipped (guest kernel provides accurate /proc and /sys natively)
  - libbaihook.so LD_PRELOAD skipped (guest kernel provides accurate sysconf natively)
  - jail ptrace sandbox skipped (VM boundary is stronger isolation)
  - Agent socket replaced with TCP (UDS cannot cross VM boundary)
  - Domain socket proxies deferred (UDS limitation; niche feature)
  - /tmp uses guest-side tmpfs (no need to cross VM boundary)
  - Core dump requires guest-side core_pattern configuration
  - Docker named volumes (krunner, deeplearning-samples) not available with containerd; use virtio-fs bind mount or guest rootfs
  - Accelerator plugin mounts differ entirely (VFIO PCI passthrough replaces Docker DeviceRequests)
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

| Category | Mount Point(s) | Source | Type | Perm |
|----------|---------------|--------|------|------|
| Scratch workspace | `/home/config` | `scratch_dir/config` | BIND | RO |
| | `/home/work` | `scratch_dir/work` | BIND | RW |
| | `/tmp` | `scratch_dir_tmp` (tmpfs) | BIND | RW |
| Timezone | `/etc/localtime`, `/etc/timezone` | Host files | BIND | RO |
| lxcfs | `/proc/{cpuinfo,meminfo,stat,...}` | `/var/lib/lxcfs/proc/*` | BIND | RW |
| | `/sys/devices/system/cpu{,/online}` | `/var/lib/lxcfs/sys/...` | BIND | RW |
| Agent IPC | `/opt/kernel/agent.sock` | Agent Unix socket | BIND | RW |
| Domain socket proxy | `{host_sock_path}` | `ipc_base_path/proxy/*.sock` | BIND | RW |
| Core dump | `debug.coredump.core_path` | `debug.coredump.path` | BIND | RW |
| Deep learning samples | `/home/work/samples` | Docker volume `deeplearning-samples` | VOLUME | RO |
| krunner volume | `/opt/backend.ai` | Docker volume per distro/arch | VOLUME | RO |
| krunner binaries | `/opt/kernel/{su-exec,entrypoint.sh,...}` | Agent package resources (15+ files) | BIND | RO |
| LD_PRELOAD hooks | `/opt/kernel/libbaihook.so` | Agent package resources | BIND | RO |
| Jail sandbox | `/opt/kernel/jail` | Agent package resources | BIND | RO |
| Python libraries | `/opt/backend.ai/.../ai/backend/{kernel,helpers}` | Agent package resources | BIND | RO |
| Accelerator hooks | `/opt/kernel/{hook}.so` | Compute plugin paths | BIND | RO |
| VFolders | `/home/work/{vfolder}` | NFS/CephFS/local path | BIND | RO/RW |

Total: **20-30+ mounts** per container (varies by accelerator and vfolder count).

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

### Intrinsic Mount Evaluation for Kata

Each mount is evaluated against the fundamental difference: Docker containers share the host kernel, while Kata VMs run a separate guest kernel inside KVM. This changes which host-side resources are visible, which kernel interfaces are shared, and which IPC mechanisms work across the boundary.

#### Mounts That Work Transparently (KEEP)

**Scratch directories** (`/home/config` RO, `/home/work` RW): The agent creates these on the host and the Kata shim shares them via virtio-fs. Files written by the agent (environ.txt, resource.txt, SSH keys) are immediately visible in the guest. Files written by the container are immediately visible on the host. Bidirectional sync is inherent to virtio-fs.

**Timezone files** (`/etc/localtime`, `/etc/timezone`): Docker containers need these because they share the host kernel but not its timezone configuration files. Kata VMs also need them — the guest rootfs ships with UTC as default, but the container should match the host's timezone. Sharing via virtio-fs overrides the guest default.

**VFolder mounts** (`/home/work/{vfolder}`): User storage mounts pass through virtio-fs transparently. Same `Mount(BIND, host_path, target, permission)` spec. See [Direct Storage Access](#direct-storage-access-from-guest-vms) for why virtio-fs is preferred over direct guest mount.

**krunner binaries** (`/opt/kernel/su-exec`, `entrypoint.sh`, `dropbearmulti`, `sftp-server`, `tmux`, `ttyd`, `yank.sh`, `all-smi`, `bssh`, `extract_dotfiles.py`, `fantompass.py`, `hash_phrase.py`, `words.json`, `DO_NOT_STORE_PERSISTENT_FILES_HERE.md`, `terminfo.*`): These 15+ individual file bind mounts are translated to virtio-fs shares. All are still functionally required inside the guest container — SSH access, terminal multiplexing, GPU monitoring, entrypoint bootstrapping, etc. For Phase 1, share via virtio-fs from the host. For production, consider consolidating into a single directory mount or baking into the guest rootfs to reduce the per-file virtio-fs share count.

**Python library mounts** (`ai.backend.kernel`, `ai.backend.helpers`): The kernel runner Python packages are injected into `/opt/backend.ai/lib/python{ver}/site-packages/`. Still required — the container inside the VM runs the same kernel runner process.

#### Mounts That Change Mechanism (CHANGE)

**`/tmp` tmpfs**: In Docker, `/tmp` is backed by a host-side tmpfs bind-mounted into the container. For Kata, sharing host tmpfs across the VM boundary via virtio-fs adds unnecessary overhead for ephemeral data. Use guest-side tmpfs instead: `Mount(TMPFS, None, "/tmp", RW)` — allocated inside guest RAM, never crosses the VM boundary.

**krunner volume** (`/opt/backend.ai`): This Docker named volume contains the pre-built Python runtime environment (distro-matched libc, interpreter, packages). Docker named volumes are not available with containerd. **Phase 1**: extract krunner to a host directory and share via virtio-fs bind mount (transparent translation). **Production**: bake into the guest rootfs image (faster startup, eliminates one virtio-fs share; requires rebuild on krunner update).

**Core dump mount**: In Docker, the host kernel's `/proc/sys/kernel/core_pattern` governs container processes because they share the host kernel. The agent bind-mounts the host's coredump directory so dumps land on the host filesystem. In Kata, the **guest kernel** has its own `core_pattern` — host-side configuration doesn't affect guest processes. To capture guest core dumps: configure the guest kernel's `core_pattern` to write to a virtio-fs-shared path (e.g., `/home/work/.coredumps`). Low priority for Phase 1.

**Agent socket** (`/opt/kernel/agent.sock`): Unix domain sockets are host-kernel objects that cannot traverse the KVM boundary. The socket relay sidecar (`backendai-socket-relay`) is Docker-specific. For Kata, the kernel runner connects to the agent via **TCP over virtio-net**. No socket mount; connection info passed via environment variables:

```python
# KataKernelCreationContext — no agent.sock mount
environ["BACKENDAI_AGENT_CONNECT"] = "tcp"
environ["BACKENDAI_AGENT_HOST"] = self._agent_rpc_host
environ["BACKENDAI_AGENT_PORT"] = str(self._agent_rpc_port)
```

VSOCK (`AF_VSOCK`) is a lower-latency alternative for future optimization — purpose-built for host-guest communication without network stack overhead, but requires socket API changes in both agent and kernel runner.

#### Mounts That Are Skipped (SKIP)

**lxcfs** (`/proc/cpuinfo`, `/proc/meminfo`, `/proc/stat`, `/sys/devices/system/cpu`, etc.): lxcfs exists because Docker containers share the host kernel — `cat /proc/meminfo` shows host RAM, `nproc` shows all host CPUs. lxcfs intercepts these reads via FUSE and returns cgroup-scoped values. In a Kata VM, the guest kernel's `/proc` and `/sys` **already reflect the VM's allocated resources** (vCPU count, memory limit). lxcfs is both unnecessary (native guest kernel does this) and non-functional (host-side FUSE filesystem callbacks cannot cross the VM boundary).

**`libbaihook.so`** (LD_PRELOAD): This shared library hooks `sysconf(_SC_NPROCESSORS_ONLN)` and related calls to return cgroup-scoped values instead of host-wide values. It solves the same problem as lxcfs but at the userspace level — making `os.cpu_count()` in Python and `nproc` in shell return the container's allocated CPU count. In a Kata VM, `sysconf(_SC_NPROCESSORS_ONLN)` **already returns the VM's vCPU count** because the guest kernel only sees allocated vCPUs. The hook is redundant. Skip the mount and do not set `LD_PRELOAD=/opt/kernel/libbaihook.so`.

**`jail` sandbox** (`/opt/kernel/jail`): The jail binary is a ptrace-based syscall tracer that filters dangerous syscalls inside Docker containers. It provides an additional security layer on top of namespaces/cgroups. In a Kata VM, the **VM boundary (KVM hypervisor)** is a fundamentally stronger isolation boundary than ptrace sandboxing — guest processes cannot escape the VM regardless of syscalls. The jail sandbox is redundant, adds latency (ptrace overhead), and ptrace inside a guest VM may have complications. Skip unconditionally for Kata.

**Domain socket proxies**: Used only for special service containers (e.g., image importer) that need host-side Unix socket access. Same UDS-cannot-cross-VM-boundary limitation as the agent socket. Niche feature — defer to a future phase. If needed, a TCP-based proxy through virtio-net can replace it.

**Deep learning samples volume** (`/home/work/samples`): Docker named volume `deeplearning-samples` mounted for TensorFlow/Caffe/Keras/Torch/MXNet/Theano images. Already deprecated in the new provisioner pipeline. Docker named volumes are not available with containerd. Skip.

#### Mounts That Differ Entirely (DIFFERENT)

**Accelerator plugin mounts**: For Docker, the `CUDAPlugin` injects hook `.so` files via bind mount (appended to `LD_PRELOAD`) and generates Docker `DeviceRequests` for the NVIDIA Container Toolkit. For Kata with VFIO passthrough, this is entirely replaced:
- No `LD_PRELOAD` GPU hooks — the GPU is natively visible inside the VM via VFIO PCI passthrough
- `CUDAVFIOPlugin` generates VFIO device configuration (PCI addresses, IOMMU groups) passed to the Kata shim, not Docker `DeviceRequests`
- `nvidia-smi` and CUDA work natively inside the guest with the passthrough GPU
- See [vfio-accelerator-plugin.md](vfio-accelerator-plugin.md) for details

### Mount Compatibility Matrix

| Mount | Docker | Kata | Verdict |
|-------|--------|------|---------|
| `/home/config` (scratch) | Bind mount | virtio-fs | **KEEP** — same spec |
| `/home/work` (scratch) | Bind mount | virtio-fs | **KEEP** — same spec |
| `/tmp` (tmpfs) | Host tmpfs bind | Guest-side tmpfs | **CHANGE** — `TMPFS` type |
| `/etc/localtime`, `/etc/timezone` | Bind mount | virtio-fs | **KEEP** — same spec |
| lxcfs `/proc/*`, `/sys/*` | Bind mount | N/A | **SKIP** — guest kernel provides |
| `libbaihook.so` + `LD_PRELOAD` | Bind mount | N/A | **SKIP** — guest kernel provides |
| `jail` sandbox | Bind mount | N/A | **SKIP** — VM is stronger isolation |
| `/opt/kernel/agent.sock` | Unix socket | TCP / VSOCK | **REPLACE** — env vars |
| Domain socket proxies | Unix socket | N/A | **SKIP** — defer to future phase |
| Core dump path | Host core_pattern | Guest core_pattern | **CHANGE** — guest-side config |
| krunner volume (`/opt/backend.ai`) | Docker volume | virtio-fs / rootfs | **CHANGE** — no Docker volumes |
| Deep learning samples | Docker volume | N/A | **SKIP** — legacy, deprecated |
| krunner binaries (15+ files) | Bind mount | virtio-fs | **KEEP** — same spec |
| Python libs (`kernel`, `helpers`) | Bind mount | virtio-fs | **KEEP** — same spec |
| Accelerator hooks | Plugin `.so` | VFIO PCI config | **DIFFERENT** — new plugin |
| VFolders | Bind mount | virtio-fs | **KEEP** — same spec |

### I/O Performance Characteristics

#### Throughput (vs Native)

Benchmark data from Red Hat virtio-fs mailing list, Kata Containers issues, and Proxmox community testing:

| Workload | virtio-fs (no DAX) | virtio-fs (DAX) | virtio-9p | Source |
|----------|-------------------|-----------------|-----------|--------|
| Sequential read (psync, 4K) | 98 MB/s | 660 MB/s | 99 MB/s | Red Hat ML |
| Sequential read (mmap, 4 threads) | ~219 MB/s | 2,849-3,107 MB/s | 140 MB/s | LWN RFC |
| Sequential write (psync) | ~98 MB/s | 487 MB/s | — | Red Hat ML |
| Random 4K read IOPS | 36.2k | 64.2k | — | Proxmox |
| Random 4K write IOPS | 15.5k | 21.4k | — | Proxmox |
| Large file random R/W (4 GB) | 211 / 70.6 MB/s | — | 43 / 14 MB/s | Kata #2815 |

**Relative to native host performance** (tuned, kernel 6.11+, `cache=never`, `direct-io=1`):

| Workload | % of Native | Notes |
|----------|-------------|-------|
| Sequential read | 85-95% (DAX) | DAX critical for large sequential reads |
| Sequential write | 75-85% (DAX) | `cache=none` outperforms `cache=always` for writes |
| Random 4K read | ~85% (tuned) | 25.4k vs 29.8k IOPS (Proxmox 6.11) |
| Random 4K write | ~85% (tuned) | 13.7k vs 16.1k IOPS |
| Metadata (file create) | ~50-70% (est.) | 3.7x faster than 9p (714 vs 194 files/sec) |
| Directory listing | ~60-80% (est.) | 6.7x faster than 9p with caching (13.5k vs 2k files/sec) |

#### DAX: Critical Caveats

DAX maps host page cache directly into guest memory, providing near-native read performance for sequential workloads. However:

1. **DAX thrashing**: When the working set exceeds the DAX window size, performance **degrades catastrophically** — Kata #2138 measured 3.6k IOPS with DAX enabled vs 252k IOPS with DAX disabled for random workloads. DAX mappings thrash as the VM continuously faults in and evicts pages.

2. **DAX window sizing**: Each 2 MB DAX chunk requires 32 KB of guest page descriptors. A 16 GB window costs ~256 MB in page descriptor overhead (device memory, not counted against VM RAM). Undersized windows trigger thrashing; oversized windows waste host memory reservation.

3. **Small file penalty**: Files under 32 KB should not use DAX — the 32 KB page descriptor overhead per 2 MB chunk exceeds the benefit. Linux 5.17+ supports per-file DAX (`dax=inode`) to selectively enable DAX only for large files.

**Recommendation**: **Disable DAX by default** (`virtio_fs_cache_size = 0` in `kata.toml`). AI/ML workloads alternate between large sequential reads (training data loading — DAX beneficial) and heavy random I/O (checkpointing, Python imports, pip installs — DAX harmful). The penalty from DAX thrashing on random I/O is far worse than the throughput loss from no-DAX on sequential reads. Enable DAX only for workloads with known large-sequential-read-dominant I/O patterns.

#### Host-Side Overhead

Each virtio-fs share runs a separate `virtiofsd` process on the host:

| Resource | Per virtiofsd Process | 20 Shares (1 VM) |
|----------|----------------------|-------------------|
| Memory (RSS) | ~15 MB idle | ~300 MB |
| Heap under load | 5-6 MB | ~100-120 MB |
| File descriptors | Up to 80k under heavy load | Cumulative FD pressure |
| Shared memory | VM RAM size (shared with QEMU, not double-counted) | Same (shared) |

The `virtiofsd` Rust implementation is recommended over the legacy C version for better CPU efficiency. Use `--thread-pool-size=1` for most workloads — the default 64 threads causes lock contention that reduces IOPS by ~27%.

**Mount count impact**: KataAgent should consolidate the 15+ individual krunner binary mounts into a single directory mount to reduce the virtiofsd process count per VM. Each eliminated share saves ~15 MB RSS and reduces host scheduling overhead.

#### AI/ML Workload Impact Assessment

| Phase | I/O Pattern | Dominant Factor | virtio-fs Impact |
|-------|-------------|-----------------|-----------------|
| Data loading | Large sequential read from vfolders | Throughput | 85-95% native (no DAX sufficient; NVMe/SSD saturates first) |
| Training | GPU compute, minimal I/O | GPU | Negligible — I/O is not on critical path |
| Checkpointing | Large sequential write | Throughput | 75-85% native |
| pip install / imports | Many small file metadata ops | Latency | 50-70% native (one-time cost at session start) |
| Jupyter notebook | Small random R/W | Latency | ~85% native (tuned) |

For typical AI/ML workloads, GPU compute dominates wall-clock time. The virtio-fs overhead is concentrated in data loading (first minutes of a training run) and session startup (pip install, Python imports). Once training begins, the GPU utilization rate determines throughput — not storage I/O.

## Interface / API

No new storage interfaces are introduced. The existing abstractions are reused:

| Abstraction | Location | Change for Kata |
|-------------|----------|-----------------|
| `VFolderMount` | `src/ai/backend/common/types.py:1299` | None |
| `Mount` / `MountTypes` | `src/ai/backend/common/types.py:612` | None |
| `MountPermission` | `src/ai/backend/common/types.py:603` | None |
| `mount_vfolders()` | Agent method | Reuse as-is |
| `get_intrinsic_mounts()` | Agent method | Override: skip lxcfs, domain socket proxies, deep learning samples; replace agent socket with TCP env vars; use guest-side tmpfs |
| `mount_krunner()` | Agent method | Override: skip libbaihook.so + LD_PRELOAD, skip jail; convert krunner Docker volume to bind mount; skip accelerator LD_PRELOAD hooks |
| `process_mounts()` | Agent method | Override to produce OCI mount format (vs Docker API format) |

## Implementation Notes

- The virtiofsd daemon is managed by the Kata shim, not by the Backend.AI agent. No virtiofsd lifecycle code is needed in KataAgent.
- virtio-fs shares are set up per-sandbox (per-VM). Multiple containers in the same Kata sandbox share the same virtio-fs instance. Since Backend.AI uses one container per session (one sandbox per container), this is a 1:1 mapping.
- File ownership (UID/GID) is preserved across the virtio-fs boundary. The `kernel_uid`/`kernel_gid` settings work as expected.
- Symbolic links within mounted directories work correctly with virtio-fs.
- File locking (flock, fcntl) works with virtio-fs but may have different semantics for distributed filesystems (CephFS, NFS) that are already mounted on the host.
- `KataKernelCreationContext.mount_krunner()` should consolidate the 15+ individual krunner binary mounts into a single directory mount (e.g., bind-mount the entire `runner/` directory to `/opt/kernel/`) to reduce the number of virtio-fs shares. Docker uses individual file mounts to overlay binaries into an existing container filesystem; Kata can use a directory mount since the guest rootfs is purpose-built.
- The `ContainerSandboxType` config option is irrelevant for Kata — always use `DOCKER` (no-op sandbox) or introduce a `VM` type. Never use `JAIL` with Kata.
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
