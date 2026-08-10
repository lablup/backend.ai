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

**Run every `lablup/backend.ai-*` image in one deployment at the SAME version.**
The components exchange serialized messages over the shared Redis/Valkey event
bus, and the message schema evolves between minor releases; a mixed-version
fleet fails at runtime with deserialization errors (e.g. a pre-26.8 subscriber
crashes on the `triggered_user` metadata field added in 26.8).

## Infra images (not published)

| Dockerfile | Role |
|---|---|
| `krunner-extractor.dockerfile` | Extracts kernel-runner archives during agent operation |
| `linuxkit-nsenter.dockerfile` | Namespace helper for LinuxKit-based Docker Desktop hosts |
| `socket-relay.dockerfile` | Relays the Docker socket for restricted mount scenarios |

## Deployment layout

A compose deployment needs, per service, a config file bind-mounted at the
path the image's default command reads:

| Service | Config mount target | Notes |
|---|---|---|
| manager | `/etc/backend.ai/manager.toml` | also mount `fixtures/` at `/app/fixtures:ro` (initial DB fixtures) |
| agent | `/etc/backend.ai/agent.toml` | see the privilege and path-parity sections below |
| webserver | `/etc/backend.ai/webserver.conf` | note the `.conf` target name, not `.toml` |
| storage-proxy | `/etc/backend.ai/storage-proxy.toml` | runs unprivileged — set `user:` to the vfroot owner UID:GID; mount TLS material at `/app/ssl:ro` if enabled |
| appproxy-coordinator | `/etc/backend.ai/proxy-coordinator.toml` | |
| appproxy-worker | `/etc/backend.ai/proxy-worker.toml` | one container per worker: each needs its OWN toml with a unique `authority`, protocol (`http`/`tcp`), `api_bind_addr` port, and non-overlapping `bind_port_range` — and the compose port mappings must match |

Shared prerequisites:

| Item | Used by | Why |
|---|---|---|
| halfstack services (PostgreSQL, Valkey/Redis, etcd) | all | the reference definitions live in `docker-compose.halfstack-main.yml` |
| `supergraph.graphql` + a GraphQL gateway (e.g. `ghcr.io/graphql-hive/gateway`) | GraphQL federation | the supergraph schema is generated per release (`scripts/generate-graphql-schema.sh`); the gateway composes manager subgraphs |
| `/etc/machine-id` bind mount | manager, agent | stable node identity |
| `wheelhouse/` mount at `/app/wheelhouse` (optional) | manager, agent | staging directory for extra plugin wheels (e.g. accelerator plugins) installed into the container on top of the base image |

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
| GPU device reservation | — | ✅ (GPU nodes) | compose-native form: `deploy.resources.reservations.devices` with `driver: nvidia, count: all, capabilities: [gpu]` (requires the NVIDIA container toolkit on the host) |
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

Docker resolves bind-mount *sources* in the **host** filesystem, so any
absolute path the containerized agent hands to the host daemon must exist at
the same absolute path on both sides. The paths are set by `agent.toml` —
**every one of them must be an absolute path**, bind-mounted host↔container at
the identical location:

| Config knob (`agent.toml`) | Reference value | Used for |
|---|---|---|
| `[container] scratch-root` | `/var/lib/backend.ai/scratches` | Scratch roots of kernel containers |
| `[agent] ipc-base-path` | `/tmp/backend.ai/ipc` | Agent↔kernel IPC sockets |
| `[agent] var-base-path` | `/var/lib/backend.ai` | Plugin state bind-mounted into kernels (e.g. accelerator hook caches) |
| — (fixed path) | `/tmp/backend-ai-krunner` | Kernel-runner files: the image entrypoint copies them here so the host daemon can mount them into kernels; **without this mount kernel creation fails** with `bind source path does not exist` (the entrypoint logs a warning at startup) |

With the reference values, three parity mounts cover everything:
`/var/lib/backend.ai`, `/tmp/backend.ai`, and `/tmp/backend-ai-krunner`.

Vfolder roots (e.g. `/vfroot/local/volume1`) follow the same rule on the
**storage-proxy**: mount each volume at the identical absolute path on host and
in the storage-proxy container, so the kernel bind-mount sources it reports
resolve on the host. The agent container itself does not need the vfroot mount.

## Reference compose file

`docker-compose.monorepo.yml` at the repository root composes the service
images and assumes the halfstack dependencies from
`docker-compose.halfstack-main.yml`. The fragment below shows the full working
shape of the two elevated services, verified against a live deployment:

```yaml
services:
  manager:
    image: lablup/backend.ai-manager:26.4.4
    network_mode: host
    privileged: true
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /etc/machine-id:/etc/machine-id
      - ./manager.toml:/etc/backend.ai/manager.toml:ro
      - ./fixtures:/app/fixtures:ro
    restart: unless-stopped

  agent:
    image: lablup/backend.ai-agent:26.4.4
    network_mode: host
    privileged: true
    pid: host
    cgroup: host          # REQUIRED on cgroup v2 hosts; Docker defaults to private
    deploy:               # GPU nodes only
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /etc/machine-id:/etc/machine-id
      - ./agent.toml:/etc/backend.ai/agent.toml:ro
      # path-parity mounts: host path == container path
      - /var/lib/backend.ai:/var/lib/backend.ai
      - /tmp/backend.ai:/tmp/backend.ai
      - /tmp/backend-ai-krunner:/tmp/backend-ai-krunner
    restart: unless-stopped
```

The agent entrypoint builds its krunner symlink farm **at container start**, so
after adding or changing the parity mounts, recreate the container
(`docker compose up -d --force-recreate agent`) — a restart of the old
container is not enough.
