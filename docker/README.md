# `docker/` — Service and infra images

The `backend.ai-*` dockerfiles in this directory are built and published to
Docker Hub for every release tag by `.github/workflows/docker-images.yml`
(matrix from `scripts/list-dockerfiles.sh --service`), multi-arch
(`linux/amd64` + `linux/arm64`). The remaining dockerfiles are internal build
tooling and are not published.

## Published images

| Dockerfile | Docker Hub | Role |
|---|---|---|
| `backend.ai-manager.Dockerfile` | [lablup/backend.ai-manager](https://hub.docker.com/r/lablup/backend.ai-manager) | Cluster control plane: API, scheduling, DB access |
| `backend.ai-agent.dockerfile` | [lablup/backend.ai-agent](https://hub.docker.com/r/lablup/backend.ai-agent) | Compute node daemon: spawns kernel containers via the host Docker daemon (DooD) |
| `backend.ai-storage-proxy.dockerfile` | [lablup/backend.ai-storage-proxy](https://hub.docker.com/r/lablup/backend.ai-storage-proxy) | Storage volume management and data transfer |
| `backend.ai-webserver.dockerfile` | [lablup/backend.ai-webserver](https://hub.docker.com/r/lablup/backend.ai-webserver) | Web UI host and HTTP session gateway |
| `backend.ai-appproxy-coordinator.dockerfile` | [lablup/backend.ai-appproxy-coordinator](https://hub.docker.com/r/lablup/backend.ai-appproxy-coordinator) | App proxy control plane |
| `backend.ai-appproxy-worker.dockerfile` | [lablup/backend.ai-appproxy-worker](https://hub.docker.com/r/lablup/backend.ai-appproxy-worker) | App proxy data plane (in-session app traffic) |
| `backend.ai-client.dockerfile` | [lablup/backend.ai-client](https://hub.docker.com/r/lablup/backend.ai-client) | CLI / SDK client environment |

**Tagging scheme**

| Tag | Meaning |
|---|---|
| `<version>` (e.g. `26.9.0`, `26.9.0rc1`) | The normalized package version of the release tag that built the image |
| `latest` | The most recent **final** release only — never moved by rc/alpha/beta releases |

All images take the same build-arg contract: `PYTHON_VERSION` (from
`pants.toml`) and `PKGVER` (normalized `VERSION`), and install the release
wheels staged in `dist/` with the build context at the repository root.

## Infra images (not published)

| Dockerfile | Role |
|---|---|
| `krunner-extractor.dockerfile` | Extracts kernel-runner archives during agent operation |
| `linuxkit-nsenter.dockerfile` | Namespace helper for LinuxKit-based Docker Desktop hosts |
| `socket-relay.dockerfile` | Relays the Docker socket for restricted mount scenarios |

## Container privileges

Most services run fine with compose defaults (bridge network, config file
bind-mounted read-only). The manager and the agent need more; grant each item
consciously — together they amount to root-equivalent control of the host.

| Requirement | manager | agent | Why |
|---|---|---|---|
| `network_mode: host` | ✅ | ✅ | Kernel↔agent ZMQ/service ports and agent RPC are advertised on host addresses; kernels spawned on the host network must reach them |
| `privileged: true` | ✅ | ✅ | Container/device management against the host daemon; sysfs reads for metrics |
| `/var/run/docker.sock` bind mount | ✅ | ✅ | DooD: containers are created by talking to the **host** Docker daemon |
| `pid: host` | — | ✅ | Host PID namespace visibility: the agent inspects and signals kernel processes by host PID |
| `cgroup: host` (host cgroup namespace) | — | ✅ | **Required, not optional** — see below |
| Host `/sys` visibility | — | ✅ | Container resource metrics are read from the host cgroupfs/sysfs (follows automatically from the host cgroup namespace) |
| Path parity mounts | — | ✅ | See below |

### The agent cgroup-namespace trap

The agent's host-PID→container-PID translation
(`host_pid_to_container_pid` in `src/ai/backend/agent/utils.py`, via
`src/ai/backend/common/cgroup.py`) parses `/proc/<pid>/cgroup` expecting
**host-rooted** paths (`docker/<id>` or `system.slice/docker-<id>.scope`) and
resolves the cgroupfs mount point from `/proc/mounts`. In a private cgroup
namespace, sibling-container paths are not host-rooted and the mounted cgroupfs
is namespaced — PID translation and sysfs metrics both break.

**On cgroup v2 hosts Docker defaults to a private cgroup namespace even for
`--privileged` containers**, so `cgroup: host` (CLI: `--cgroupns=host`) must be
set explicitly.

### Agent path parity

Docker resolves kernel bind-mount *sources* in the **host** filesystem, so any
path the containerized agent hands to the host daemon must exist at the same
absolute path on both sides. Bind-mount each of these host paths to the
identical path inside the agent container:

| Path (host = container) | Used for |
|---|---|
| `/var/lib/backend.ai` | Scratch roots of kernel containers |
| `/tmp/backend.ai/ipc` | Agent↔kernel IPC sockets |
| `/tmp/backend-ai-krunner` | Kernel-runner files: the image entrypoint copies them here so the host daemon can mount them into kernels |
| vfolder mount roots (deployment-specific) | Data folder bind-mount sources |

## Reference compose file

`docker-compose.monorepo.yml` at the repository root composes the manager,
webserver, and app proxy images and is the maintained example; it assumes the
halfstack dependencies (PostgreSQL, Valkey, etcd) from
`docker-compose.halfstack-main.yml` are running. The fragment below shows the
full privilege set for the two elevated services:

```yaml
services:
  manager:
    image: lablup/backend.ai-manager:26.9.0
    network_mode: host
    privileged: true
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./manager.toml:/etc/backend.ai/manager.toml:ro
      - /tmp/backend.ai/ipc:/tmp/backend.ai/ipc
    restart: unless-stopped

  agent:
    image: lablup/backend.ai-agent:26.9.0
    network_mode: host
    privileged: true
    pid: host
    cgroup: host          # REQUIRED on cgroup v2 hosts; Docker defaults to private
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./agent.toml:/etc/backend.ai/agent.toml:ro
      # path-parity mounts: host path == container path
      - /var/lib/backend.ai:/var/lib/backend.ai
      - /tmp/backend.ai/ipc:/tmp/backend.ai/ipc
      - /tmp/backend-ai-krunner:/tmp/backend-ai-krunner
    restart: unless-stopped
```
