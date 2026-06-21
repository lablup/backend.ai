# KataAgent (MVP) — running Backend.AI kernels in Kata Containers microVMs

> **Status: hacky MVP.** This backend proves that a Backend.AI compute session
> can run inside a Kata Containers lightweight VM with almost no new code, by
> reusing the entire Docker kernel-creation pipeline and swapping only the final
> "create + start container" step for a `nerdctl run --runtime
> io.containerd.kata.v2` invocation. It is **not** production-ready and does
> **not** implement Confidential Computing (TDX/CoCo). See
> `proposals/BEP-1051-kata-containers-agent.md` for the full intended design and
> `~/Downloads/backend-ai-cc-investigation/mvp-findings-kataagent.md` for the
> findings report.

## What it is

`KataAgent` subclasses `DockerAgent`. The whole `create_kernel` orchestration
(scratch/config generation, krunner injection, vfolder mounts, resource specs,
image scan/pull) is inherited unchanged. The only behavioral delta:

| Concern | DockerAgent | KataAgent |
|---|---|---|
| create + start container | `aiodocker` `containers.create()` + `container.start()` | translate `container_config` → `nerdctl run -d --runtime io.containerd.kata.v2` |
| destroy / clean | `aiodocker` stop/delete | `nerdctl stop` / `nerdctl rm -f -v` |
| logs / list / download | `aiodocker` / `docker exec` | `nerdctl logs` / `nerdctl exec` |
| named krunner volume | Docker named volume | resolved to its host path and **bind-mounted** (Kata can't share a Docker named volume into the guest) |
| death detection | dockerd event stream | lightweight `nerdctl ps` poller (dockerd events don't see containerd's namespace) |

The repl ports (container 2000/2001) are still published to host `127.0.0.1`
via `-p 127.0.0.1:HPORT:CPORT`; nerdctl's bridge+portmap CNI installs the
host→guest DNAT so the agent's hardcoded `tcp://127.0.0.1:{port}` connection
(`docker/kernel.py:98`) keeps working across the VM boundary.

## Host prerequisites

A working Kata host (see Handover A / report §6c). In short:

- nested KVM available (`egrep -c '(vmx|svm)' /proc/cpuinfo` > 0), `/dev/kvm`,
  `vhost_vsock`.
- Kata Containers installed and registered as a containerd runtime handler
  `io.containerd.kata.v2` (kata-deploy / kata-manager).
- `nerdctl` + CNI plugins (`bridge`, `portmap`, `host-local`, `loopback`,
  `firewall`) in `/opt/cni/bin`.
- dockerd still present (Backend.AI halfstack + krunner volume preparation use
  it). KataAgent and DockerAgent coexist: nerdctl uses containerd namespace
  `default`, dockerd uses `moby`.

Smoke-test the host first:

```bash
nerdctl run --runtime io.containerd.kata.v2 -p 127.0.0.1:8080:80 nginx
curl 127.0.0.1:8080   # proves portmap into the VM
```

### Host gotcha: Docker 29 + Kata ≤3.31 — `Invalid namespace type`

Empirically observed (BA-6541, Kata 3.31.0 / Docker 29.6.0): Docker 29 applies a
**time namespace** to containers by default, but the Kata agent (≤3.31) only
recognizes `{user,ipc,pid,net,mnt,uts,cgroup}` and rejects the unknown
`time` namespace → the container/VM fails to start. Disable it in
`/etc/docker/daemon.json`:

```json
{
  "runtimes": {
    "kata": { "runtimeType": "/opt/kata/bin/containerd-shim-kata-v2" }
  },
  "features": { "time-namespaces": false }
}
```

This affects the Docker-runtime path below. The nerdctl/containerd path may hit
the same class of issue depending on the containerd version's default OCI spec —
if `nerdctl run --runtime io.containerd.kata.v2` fails with `invalid namespace
type`, the runtime spec is injecting a namespace the kata-agent doesn't know;
upgrade kata-agent or strip the offending namespace.

## Enabling it

In the agent config (`agent.toml` / `agent.conf`):

```toml
[agent]
backend = "kata"
```

Optional environment overrides (read by `kata/nerdctl.py`):

| Env var | Default | Meaning |
|---|---|---|
| `BACKENDAI_KATA_RUNTIME` | `io.containerd.kata.v2` | containerd runtime handler |
| `BACKENDAI_NERDCTL_BIN` | `nerdctl` | container engine CLI |
| `BACKENDAI_NERDCTL_NAMESPACE` | `default` | containerd namespace |

Restart the agent and create a session as usual:

```bash
./backend.ai session create -t kata-demo cr.backend.ai/stable/python:3.11-ubuntu24.04
./backend.ai run --rm cr.backend.ai/stable/python:3.11-ubuntu24.04 -c 'import platform; print(platform.uname().release)'
```

Proof it ran in a VM: the kernel release string inside the session differs from
the host's `uname -r` (the Kata guest runs its own kernel).

## Even cheaper alternative (zero code — proven working)

You do **not** need `backend = "kata"` at all if the host's dockerd is configured
with a Kata runtime handler. Keep `backend = "docker"` and drop an override file
so only kernels use the Kata runtime (other host containers are unaffected):

```jsonc
// /etc/backend.ai/agent-docker-container-opts.json
// (also loaded from ~/.config/backend.ai/ or CWD)
{ "HostConfig": { "Runtime": "kata" } }
```

This is loaded and merged in `docker/agent.py` (the `agent-docker-container-opts.json`
lookup) so the existing Docker create/start, PortBindings, event stream, and
cleanup path all run **verbatim**. This path was validated end-to-end in BA-6541
(Kata 3.31 / Docker 29): container create, scratch bind mount (read/write),
intrinsic socket, code execution, Jupyter-in-browser, and clean VM/virtiofsd/shim
teardown on session terminate all worked. The one gap: **file upload/download
failed** on this path (see degradations).

This `kata/` backend uses the **nerdctl/containerd** path instead because (a) it
is what Handover A's host proves (`nerdctl --runtime io.containerd.kata.v2`), (b)
it keeps Kata kernels in a separate containerd namespace from Docker, and (c) it
is the cleaner stepping stone toward the production containerd-gRPC backend
(BEP-1051 / report §6d.3). It also routes file upload/download through the kernel
**exec channel** (tar over `nerdctl exec`), which should fix the upload/download
gap seen on the Docker-runtime path.

## Known MVP degradations

- **stats** are not collected (lxcfs proc/sys mounts are meaningless inside a
  real VM; guest cgroup stats need a different path) — stubbed via inheritance.
- **container log streaming** is one-shot (`nerdctl logs`), not a live follow.
- **file upload/download**: routed through the kernel exec channel (tar over
  `nerdctl exec`) rather than host-side scratch writes / `docker get_archive`,
  to address the upload/download failure observed on the Docker-runtime path
  (BA-6541). Uploaded files land owned by the exec user (root) — ownership is
  not matched to the kernel user yet.
- **commit / image-from-container** raises `NotImplementedError`.
- **death detection** is a 5s poller, not an event stream.
- **GPU / accelerators** are out of scope (Docker `DeviceRequests` are not
  translated).
- The **agent socket relay** (unix socket bind-mounted into the kernel) may not
  function across the virtio-fs/VM boundary; socket-dependent features degrade.
  Basic repl/code-execution does not depend on it (it uses TCP/ZMQ).
