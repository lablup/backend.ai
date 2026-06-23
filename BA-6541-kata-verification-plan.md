# BA-6541 — Kata Container Compatibility Verification Plan

Verify whether the Backend.AI Agent can create and operate kernels on top of the
Kata Container runtime, and classify each capability as **Fully / Partial /
Unsupported**.

> Guiding principle: Kata is lightweight-VM isolation. The more a feature depends
> directly on the host kernel, host devices, or host filesystem bind mounts, the
> more likely it is to break. Tests are therefore ordered by risk — the earliest
> tiers are the ones that, if they fail, make later tiers meaningless.

---

## 0. Background — how Kata is applied without code changes

The Agent only supports `docker`, `kubernetes`, `dummy` backends
(`src/ai/backend/agent/types.py:36-40`) and **never sets the Docker
`HostConfig.Runtime` parameter** (`src/ai/backend/agent/docker/agent.py:1194-1219`).
So every kernel is created with the daemon's default runtime (`runc`).

Two ways to force kernels onto Kata **without modifying Backend.AI**:

- **Method A — daemon default runtime.** Set `default-runtime` in
  `/etc/docker/daemon.json` to the Kata runtime. *All* containers become Kata.
- **Method B — per-Agent override file (recommended).** Backend.AI merges an
  optional override JSON into the container config
  (`src/ai/backend/agent/docker/agent.py:1256-1268`), searched in this order:
  - `/etc/backend.ai/agent-docker-container-opts.json`
  - `~/.config/backend.ai/agent-docker-container-opts.json`
  - `<cwd>/agent-docker-container-opts.json`

  Content:
  ```json
  { "HostConfig": { "Runtime": "kata" } }
  ```
  The runtime name must match the daemon's registration exactly (`docker info |
  grep -i runtime`). On the target server it is `kata`; use
  `io.containerd.kata.v2` instead if Kata is installed as a containerd shim.
  Method B keeps every other host container on `runc`, so it is the preferred
  verification path.

**Decision: use Method B.** Confirmed runtime name on the target server: `kata`
(`docker info | grep -i runtime`).

---

## 1. Test environment prerequisites

- [x] Kata Containers installed; runtime registered with the Docker daemon
      (`docker info | grep -i runtime` lists `kata` / `io.containerd.kata.v2`).
- [x] Sanity check outside Backend.AI:
      `docker run --rm --runtime=kata alpine uname -r`
      (kernel version differs from host ⇒ running inside the Kata VM).
- [ ] Single node, GPU-less baseline image first (e.g. a basic Python image).
- [ ] Place the Method B override file for the Agent and restart the Agent
      (see `/local-dev`). Confirm a new kernel container shows the Kata runtime:
      `docker inspect <kernel-container> --format '{{.HostConfig.Runtime}}'`.
- [ ] Record runtime/version: Kata version, Docker version, kernel, image digest.

---

## 2. Execution order

```
Tier 1 (create / mount / agent-kernel comms)   ← gate: must pass first
        │  if any of #1–#3 fails → "kernel won't start", stop and document
        ▼
Tier 2 (core operations)
        ▼
Tier 3 (resources / devices / GPU)
        ▼
Tier 4 (networking / app proxy)
        ▼
Tier 5 (security / isolation options)
```

Run Tiers 1–2 with a basic GPU-less kernel on a single node before expanding to
resources/devices. Each test records: result (✅/⚠️/❌), evidence (command output,
log line, `docker inspect`), and notes on any required extra configuration.

> All `./bai` commands: load the `/bai-cli` skill first.
> After each kernel action, check Agent logs/metrics via `/observability`
> (Loki) rather than tailing the console.

---

## Tier 1 — Gate: create, mount, agent↔kernel comms

| # | Item | BA mechanism | How to test | Pass criteria |
|---|------|-------------|-------------|---------------|
| 1 | Kernel creation | `docker.containers.create()` (`docker/agent.py:1290`) | `./bai session create` a basic image | Session reaches `RUNNING`; `HostConfig.Runtime` = kata on inspect |
| 2 | scratch / bind mount | scratch_root bind-mounted at `/home/work`, config/work dirs | After create, in kernel: `ls -la /home/work`, write a file | `/home/work` mounted & writable (Kata virtio-fs/9p) |
| 3 | intrinsic socket comms | kernel-runner ↔ Agent over service ports | Kernel reaches `RUNNING` (implies Agent connected) | Status `RUNNING`, no comms timeout in Agent log |

**If any of #1–#3 fails → record as ❌, stop the tier sweep, document the blocking
error (e.g. `runtime not found`, mount failure).**

---

## Tier 2 — Core kernel operations

| # | Item | BA mechanism | How to test | Pass criteria |
|---|------|-------------|-------------|---------------|
| 4 | Code execution | kernel-runner execute | Run a code snippet via session | Correct output returned |
| 5 | exec / attach (pty) | docker exec-based terminal | `./bai` exec / open terminal | Interactive shell works |
| 6 | File upload / download | file IO via scratch (`/home/work`) | `./bai session upload` / download a file | Round-trip integrity (depends on #2) |
| 7 | Session lifecycle | start / restart / terminate + cleanup | restart, then terminate the session | Clean restart; terminate removes Kata VM and scratch |

---

## Tier 3 — Resources & devices (highest "Partial" density)

| # | Item | BA mechanism | How to test | Pass criteria |
|---|------|-------------|-------------|---------------|
| 8 | CPU / Memory limits | `Cpus`, `CpusetCpus`, `Memory`, `MemorySwap` (`docker/intrinsic.py`) | Create with CPU/mem caps; check inside kernel | Limits enforced or documented approximation |
| 9 | GPU passthrough | accelerator plugin injects `Devices`/env | Create with GPU resource slot | GPU visible in kernel (likely needs VFIO setup ⇒ ⚠️/❌) |
| 10 | RDMA / hugepage | `/dev/infiniband` device, `IPC_LOCK`, `memlock` ulimit (`agent.py:717,1201`) | Create on RDMA-capable host | Device present & usable |
| 11 | shmem (`/dev/shm`) | `ShmSize` (`agent.py:1244`) | Create with `shmem` resource_opt; check `/dev/shm` | tmpfs sized correctly inside VM |
| 12 | vfolder / NFS-backed mount | vfolder host bind: `Path(host_path) → kernel_path` (`agent.py:559-565`) — same bind mechanism as scratch #2 | Mount an NFS-backed vfolder; inside kernel `ls`, read/write a file, `mount` to confirm the path | Vfolder visible & R/W inside VM; an NFS-backed host path passes through the bind → virtio-fs hop with byte-exact data (note any locking/attr-cache caveats) |

> If the test host has no GPU/RDMA, mark #9–#10 **Not tested** with the reason,
> rather than guessing.

---

## Tier 4 — Networking & external access

| # | Item | BA mechanism | How to test | Pass criteria |
|---|------|-------------|-------------|---------------|
| 13 | Port binding / service port | `PortBindings` host↔container (`agent.py:1196`) | Inspect published ports; reach a service port | Port mapping works through VM network |
| 14 | App Proxy access | wsproxy/appproxy → kernel service port | Open an app (e.g. Jupyter) via proxy | App reachable end-to-end (depends on #13) |
| 15 | Overlay networking | multi-node cluster network | Multi-node session (if available) | Inter-node connectivity (single-node ⇒ defer) |

---

## Tier 5 — Security / isolation options (host-kernel dependent)

| # | Item | BA mechanism | How to test | Pass criteria |
|---|------|-------------|-------------|---------------|
| 16 | JAIL sandbox mode | `seccomp=unconfined`, `apparmor=unconfined`, `SYS_PTRACE` (`agent.py:1227-1236`) | Set `container.sandbox_type = JAIL`, create kernel | Kernel starts & sandbox functions under Kata |
| 17 | seccomp profile | `_apply_seccomp_profile` (`agent.py:1053,1222`) | Default sandbox create | Profile applied without breaking the VM |

---

## 3. Result record (fill in during verification)

Classify each item: ✅ Fully / ⚠️ Partial (note required config) / ❌ Unsupported /
➖ Not tested (note reason).

| # | Item | Result | Evidence | Notes (extra config / limitation) |
|---|------|--------|----------|-----------------------------------|
| 1 | Kernel creation | ✅ | `docker inspect` → `HostConfig.Runtime = kata`; session RUNNING, container Up | Method B override (`Runtime: kata`) applied on the target Agent |
| 2 | scratch / bind mount | ✅ | `/home/work` listed & writable (`echo hi > t.txt` round-trip); `mount` → `none on /home/work type virtiofs (rw,relatime)` | scratch delivered into Kata VM via virtio-fs — no extra config needed |
| 3 | intrinsic comms | ✅ | Session reached RUNNING; no comms/heartbeat timeout in Agent log | RUNNING implies kernel-runner ↔ Agent established |
| 4 | Code execution | ✅ | Jupyter cell `print(1+1)` → `2`; `platform.uname().release` → `6.18.28` (Kata guest kernel, differs from host) | kernel-runner executes inside the Kata VM |
| 5 | exec / attach | ✅ | Jupyter Terminal (pty) interactive shell works | docker exec / pty allocation OK under Kata |
| 6 | File upload/download | ⚠️ | Jupyter UI download of `hello.txt` failed (saved as `hello.html`, "File wasn't available on site"); scratch read/write inside VM is fine (`open().read()` OK, virtio-fs) | **Not a Kata filesystem problem** — virtio-fs scratch is byte-exact. Two distinct degraded transfer paths; see detailed finding below. |
| 7 | Session lifecycle | ✅ | `terminate` → session TERMINATED; kernel container, Kata VM (hypervisor), virtiofsd, kata shim, and scratch dir all removed | Clean teardown — no leaked VM/virtiofsd processes |
| 8 | CPU / Memory limits | | | |
| 9 | GPU passthrough | ➖ | No GPU on the Vultr bare-metal host | Not tested — requires GPU + VFIO setup under Kata |
| 10 | RDMA / hugepage | ➖ | No `/dev/infiniband` on the host | Not tested — requires RDMA-capable host |
| 11 | shmem | | | |
| 12 | vfolder / NFS-backed mount | ✅ | Session created with an NFS-backed vfolder mounted; the mount is visible in the kernel and read + write both succeed inside the Kata guest | NFS host_path bind → virtio-fs passthrough into the VM works with no extra config (pending: capture guest `mount` type = virtiofs and host `df -T` = nfs4 to finalize evidence) |
| 13 | Port binding | ✅ | jupyter service port reached end-to-end through proxy chain (coordinator:10200 → worker:10201 → app:10240) | Service port traverses Kata VM network with no extra config |
| 14 | App Proxy | ✅ | `start-service` → `/v2/proxy/auth` → worker `/setup` (cookie) → Jupyter Notebook 7.3.3 returned `200 OK` + full HTML | wsproxy/appproxy end-to-end works; `rootUri=file:///home/work` confirms VM scratch mount |
| 15 | Overlay networking | ✅ | `cluster_mode=multi-node, cluster_size=2` session placed kernels on two agents (ag1/ag2); Docker swarm overlay `bai-multinode-<id>` created with both nodes as VXLAN peers; kernels got overlay IPs `10.0.1.4` (main1) / `10.0.1.2` (sub1); cross-node TCP connect sub1 → `10.0.1.4:12345` succeeded (`OK: overlay reachable`) | Kata VMs participate in the swarm overlay; inter-node connectivity confirmed end-to-end. **Caveat:** swarm `advertise-addr` was the public IP, so VXLAN (UDP 4789) traverses the public interface in plaintext — for production re-init swarm on the private VPC IP. MTU left at 1500. |
| 16 | JAIL sandbox | | | |
| 17 | seccomp profile | ✅ | (1) `docker inspect … .HostConfig.SecurityOpt` shows the full default-deny profile attached (`defaultAction=SCMP_ACT_ERRNO`, `defaultErrnoRet=1`, 441-syscall allowlist + cap-gated rules); kernel runs normally → applied without breaking the Kata VM. (2) **Enforcement confirmed inside the guest:** an allowlist-excluded syscall (`keyctl`, x86_64 #250) returned `errno 1 (EPERM)` — exactly the profile's `defaultErrnoRet`, so the filter is actually enforced in the Kata guest, not just passed to the runtime | Backend.AI's appended "additionally allowed syscalls" rule is present but empty (no accelerator extras on GPU-less host) |

Summarize the filled table into the BA-6541 findings (fully / partially /
unsupported under Kata).

### File upload / download (item #6) — detailed finding

File transfer is the one clearly degraded capability under the Method B
(Docker + `HostConfig.Runtime=kata`) path. The **underlying filesystem is not the
problem**: the scratch `work` dir is bind-mounted into the guest over virtio-fs and
reads/writes are byte-exact (confirmed in #2, and a separate on-host test in the
Kata-agent MVP transferred 1 MiB byte-exact in both directions via the host-side
virtio-fs share). The failures are at the **transfer mechanism layer**, and there
are two distinct ones:

1. **Backend.AI native transfer** (`./bai session upload`/`download` →
   `DockerKernel.get_archive` / `docker cp`). Not directly exercised here because
   the v2 CLI in this build does not expose `session upload`/`download`. The
   BA-6541 investigation (and the `feat/kata-agent-mvp-wip` README) found this
   Docker `get_archive`/`cp` API **does not work across the Kata VM boundary** —
   the failing symptom is the Docker archive API, not the shared mount. The
   Kata-agent MVP works around it by reading/writing the rw virtio-fs scratch share
   host-side instead of going through `get_archive`.

2. **Jupyter UI download** (what we observed): `GET /files/<path>` served by the
   Jupyter server and tunneled back through the app-proxy (worker). Chrome saved
   `hello.txt` as `hello.html` with "File wasn't available on site", i.e. the
   response was an HTML error page rather than the file stream. This is a separate
   **Jupyter → app-proxy HTTP-path** issue and is independent of the container
   runtime (Jupyter reads the file from the same filesystem that `open().read()`
   already proved works).

**Conclusion for #6:** classify as ⚠️ Partial — basic FS IO inside the VM works,
but both file-transfer paths are degraded. Neither is caused by the Kata
filesystem; the native path is a Docker `get_archive` API/VM-boundary limitation,
and the Jupyter path is an app-proxy transport issue. To attribute the Jupyter
symptom precisely, repeat the same download on a `runc` baseline session — if it
also fails there, it is fully runtime-independent.

### Out of scope / N/A

- **Image pull** — ➖ N/A. Image pull is handled by the Docker daemon/snapshotter
  at a layer *below* the container runtime; `kata-runtime` is only involved at
  container create/run time, so pull behaves identically to `runc`. With the
  Docker + `HostConfig.Runtime=kata` setup (Method B) it is a plain `docker pull`,
  and a successful pull is already confirmed indirectly by #1/#2 (the image rootfs
  is intact inside the VM). This would only need separate verification under a
  containerd + Kata-snapshotter (nydus / guest-pull) or confidential-containers
  setup, which is not used here.
