# `docker/` — Service and infra images

The `backend.ai-*` dockerfiles in this directory are built and published to
Docker Hub for every release tag by `.github/workflows/docker-images.yml` in a
single `docker buildx bake` run (`docker-bake.hcl` at the repository root),
multi-arch (`linux/amd64` + `linux/arm64`).
`scripts/list-dockerfiles.sh` stays the publishing allowlist — the workflow
fails when it and the bake targets drift apart
(`scripts/check-bake-targets.sh`). The remaining dockerfiles are runtime
helper images and are not published.

## Published images

All published images are thin layers over a shared, **unpublished** base image
(`backend.ai-base.dockerfile`) that installs every backend.ai package once:

- Every image contains **all** backend.ai packages and the full `backend.ai`
  CLI; the images differ only in their default command, prepared directories,
  and service extras (e.g. the agent's Docker CLI and entrypoint).
- A host running several services downloads the shared base layers once; the
  per-service layers are a few KB.
- The same-version rule below is structural: one base build feeds all seven
  images of a release.

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
| `latest` | Applied to **any** final (non-prerelease) release — never moved by rc/alpha/beta releases. This includes hotfixes cut from older release branches, so `latest` can move *backwards*; pin explicit versions in production |

**Build contract.** The base image takes `PYTHON_VERSION` (from `pants.toml`)
and `PKGVER` (normalized `VERSION`) and installs the release wheels staged in
`dist/` (falling back to PyPI for a version already released there); the
service dockerfiles take only `PKGVER` and start
`FROM backend.ai-base:${PKGVER}`. Always build through bake — it builds the
base as an in-run dependency of the service targets (via a named build
context), so the base never needs to be pre-built or pushed anywhere:

```sh
PYTHON_VERSION=<ver from pants.toml> \
PKGVER=$(python3 scripts/normalize-version.py "$(cat VERSION)") \
  docker buildx bake backend_ai-manager --set '*.platform=linux/arm64' --load
```

(Bake target names replace the `.` of the image name with `_`; the build
context is the repository root.)

**Run every `lablup/backend.ai-*` image in one deployment at the SAME version.**
The components exchange serialized messages over the shared Redis/Valkey event
bus, and the message schema evolves between minor releases; a mixed-version
fleet fails at runtime with deserialization errors (e.g. a pre-26.8 subscriber
crashes on the `triggered_user` metadata field added in 26.8).

## Infra images (not published)

Runtime helper images loaded on demand by the agent from bundled archives —
not published to Docker Hub.

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
| manager | `/etc/backend.ai/manager.toml` | also mount `fixtures/` at `/app/fixtures` **read-write** — manager RPC keypair (auto-generated at first start) + DB fixtures |
| agent | `/etc/backend.ai/agent.toml` | see the privilege and path-parity sections below |
| webserver | `/etc/backend.ai/webserver.conf` | note the `.conf` target name, not `.toml` |
| storage-proxy | `/etc/backend.ai/storage-proxy.toml` | to run unprivileged with the chown watcher, set the `user`/`group` knobs in `storage-proxy.toml` (the daemon drops privileges itself after starting as root); when the watcher is not used, compose `user:` works too — the DOCKER install mode runs it as the installing user this way. If TLS is enabled, mount the cert material read-only at whatever path `ssl-cert`/`ssl-privkey` point to |
| appproxy-coordinator | `/etc/backend.ai/proxy-coordinator.toml` | |
| appproxy-worker | `/etc/backend.ai/proxy-worker.toml` | one container per worker: each needs its OWN toml with a unique `authority`, protocol (`http`/`tcp`), `api_bind_addr` port, and a non-overlapping `[proxy_worker.port_proxy] bind_port_range` (port-based frontends only) — and the compose port mappings must match |

The `/etc/backend.ai/*` targets are what the images' **default commands**
read; the DOCKER install mode (see the reference compose file below) follows
the same convention, mounting each generated config at its default-command
path read-only.

Shared prerequisites:

| Item | Used by | Why |
|---|---|---|
| halfstack services (PostgreSQL, Valkey/Redis, etcd) | all | the reference definitions live in `docker-compose.halfstack-main.yml` |
| `supergraph.graphql` + a GraphQL gateway (e.g. `ghcr.io/graphql-hive/gateway`) | GraphQL federation | the supergraph schema is generated per release (`scripts/generate-graphql-schema.sh`); the gateway composes manager subgraphs |
| RPC auth key distribution | manager, agent | the agent needs the manager's RPC **public** key to authenticate RPC calls — e.g. share the parity-mounted fixtures directory across nodes, or mount a common key directory at `/etc/backend.ai/keys:ro` |
| `wheelhouse/` mount at `/app/wheelhouse` | manager, agent | staging dir for extra plugin wheels (e.g. accelerator plugins) — the DOCKER install mode creates and mounts `<install-dir>/wheelhouse` read-only by default; nothing in the images consumes it automatically, so install with `docker exec <container> pip install /app/wheelhouse/*.whl` or build a derived image |

## Container privileges

Most services run fine with compose defaults (bridge network, config file
bind-mounted read-only). Only the **agent** needs real host privileges; the
manager needs at most the Docker socket. Grant each item consciously —
together they amount to root-equivalent control of the host.

| Requirement | manager | agent | Why |
|---|---|---|---|
| `network_mode: host` | optional | ✅ | Agent: kernel↔agent ZMQ/service ports and agent RPC are advertised on host addresses; kernels spawned on the host network must reach them. Manager: convenience only — the bridge alternative works via the `announce-addr` / `announce-internal-addr` knobs |
| `privileged: true` | default | ✅ | Agent: container/device management against the host daemon; sysfs reads for metrics. The manager does not strictly need it — the Docker socket alone suffices for its (conditional) Docker use — but the DOCKER install mode's generated compose grants it by default; remove the flag for a least-privilege deployment |
| `/var/run/docker.sock` bind mount | conditional | ✅ | DooD: containers are created by talking to the **host** Docker daemon. Manager: only when the `local` container registry is used |
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
reads hardcoded `/sys/fs/cgroup/...` paths; the metrics path separately
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

The values below are the defaults the DOCKER install mode writes — all under
fixed system paths, so the install directory itself is never mounted into a
running service; a hand-rolled deployment may choose any absolute paths as
long as the parity rule holds.

| Config knob (`agent.toml`) | DOCKER-mode default | Used for |
|---|---|---|
| `[container] scratch-root` | `/var/lib/backend.ai/scratches` | Scratch roots of kernel containers |
| `[agent] mount-path` | `/vfroot/local` | Vfolder tree whose subdirectories become kernel bind-mount sources |
| `[agent] ipc-base-path` | `/tmp/backend.ai/ipc/agent` | Agent↔kernel IPC sockets |
| `[agent] var-base-path` | `/var/lib/backend.ai` | Plugin state bind-mounted into kernels (e.g. accelerator hook caches); plugin dirs live as siblings of `scratches/`, `commit/`, and `krunner/` |
| `[agent] image-commit-path` | `/var/lib/backend.ai/commit` | Session image-commit tarballs written by the host daemon |
| env `BACKENDAI_KRUNNER_SHARED` | `/var/lib/backend.ai/krunner` | Kernel-runner files: the image entrypoint copies them here so the host daemon can mount them into kernels; the entrypoint **refuses to start** without the share being host-backed |

With these defaults, three parity mounts cover everything on the agent:
`/var/lib/backend.ai` (which also backs the krunner share), `/tmp/backend.ai`,
and `/vfroot/local`. The Docker daemon creates the missing host directories
on first start; they stay root-owned, which is fine — the agent runs as
root, and the storage-proxy's `/vfroot/local/volume1` is chowned to the
installing user by the installer.

Vfolder roots (e.g. `/vfroot/local/volume1`) follow the same rule on the
**storage-proxy**: mount each volume at the identical absolute path on host and
in the storage-proxy container, so the kernel bind-mount sources it reports
resolve on the host. The agent container itself does not need the vfroot mount
— unless the agent itself performs the volume mounting
(`cohabiting-storage-proxy = false`), in which case its `mount-path` must be a
**shared-propagation** bind mount (`bind-propagation: rshared`) so host-side
mounts become visible inside the container. Also, `scratch-type = "memory"` is
unsupported in the containerized agent — a tmpfs mounted inside the container's
namespace is invisible to the host daemon — use `hostdir`.

## Reference compose file

`docker-compose.monorepo.yml` at the repository root is a **partial, legacy
example** — it uses different image names, includes no agent or storage-proxy,
and runs on a bridge network. The authoritative reference is the compose file
the **DOCKER install mode** of `backend.ai-installer` generates at
`<install-dir>/docker-compose.yaml` (rendered from the
`src/ai/backend/install/configs/docker-compose.services.yml` template — the
standard output name means a bare `docker compose` in the install directory
addresses the deployment). Its contract:

- Every service reads its generated config from the image's default
  `/etc/backend.ai/*` path via a per-file read-only mount and runs the
  image's default command — the same convention as the deployment layout
  above.
- The installer merges the halfstack definition (PostgreSQL/Redis/etcd +
  optional observability) INTO the generated file, so the WHOLE deployment
  is ONE compose file and ONE compose project.
- Host networking is granted only to the manager and the agent (and the
  `manager-cli` one-off tool). The other services join the halfstack's
  `half` bridge network with published ports and `depends_on` health gating;
  their generated configs get DB/etcd addresses rewritten to compose
  service DNS names (container-side ports), redis addressed by the host
  public IP + published port everywhere (it is shared across both network
  profiles via the etcd `config/redis/addr`), the manager API rewritten to
  `host.docker.internal` (mapped via `extra_hosts: host-gateway` on the
  webserver), and bind addresses forced to `0.0.0.0` — while
  announce/advertised addresses are untouched.
- **No running service mounts the install directory.** The daemon-visible
  state lives under fixed system paths with host==container path parity:
  `/var/lib/backend.ai` + `/tmp/backend.ai` (agent) and `/vfroot/local`
  (agent + storage-proxy). Only `manager-cli`, the installer's one-off tool,
  mounts the install directory (for fixture files). The manager exchanges
  the RPC keypair through `<install-dir>/fixtures` mounted at
  `/app/fixtures`, and the storage-proxy reads its TLS material from a
  read-only mount of `<install-dir>/configs/storage-proxy`.
- The storage-proxy runs as the **installing user** (compose `user:`),
  matching PACKAGE-mode file ownership; the installer chowns
  `/vfroot/local/volume1` to that user via a root one-off container.
- `/etc/machine-id` is passed through read-only to the manager and agent so
  anything deriving a stable host identity sees the host's, not the
  container's.
- All images are pinned to the installer's own version (the event-bus
  version-skew rule above).
- The compose project name is fixed (`backendai-services`) so reruns and
  operator commands always address the same deployment regardless of the
  install directory's name.
- One-off management commands run via `docker compose run` on a dedicated
  non-privileged `manager-cli` twin of the manager (no Docker socket, no
  restart policy; its `cli` profile keeps `up -d` from starting it).
- No agent-watcher container ships in this mode, and the app-proxy data plane
  runs as an `appproxy-worker` / `appproxy-worker-tcp` pair.

The fragment below reproduces the two elevated services. Replace `<version>`
with a tag from the tagging scheme above and `<install-dir>` with the install
target directory. The `cgroup:` key requires Docker Compose v2.15+.

```yaml
name: backendai-services
services:
  manager:
    image: lablup/backend.ai-manager:<version>
    network_mode: host    # optional — bridge works via the announce-addr knobs
    privileged: true      # installer default; the socket alone suffices (see the matrix) — remove for least privilege
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock   # needed only when the `local` container registry is used
      - /etc/machine-id:/etc/machine-id:ro
      - <install-dir>/manager.toml:/etc/backend.ai/manager.toml:ro
      # the image entrypoint generates the RPC keypair here at first start
      - <install-dir>/fixtures:/app/fixtures
    restart: unless-stopped

  agent:
    image: lablup/backend.ai-agent:<version>
    network_mode: host
    privileged: true
    pid: host
    cgroup: host          # REQUIRED on cgroup v2 hosts; Docker defaults to private
    deploy:               # GPU nodes only (the installer currently rejects --accelerator
      resources:          # until the published images bundle the accelerator plugins)
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /etc/machine-id:/etc/machine-id:ro
      - <install-dir>/agent.toml:/etc/backend.ai/agent.toml:ro
      # path-parity mounts (host path == container path), created by the
      # Docker daemon on first start; /var/lib/backend.ai also backs the
      # krunner share the image entrypoint fills
      - /var/lib/backend.ai:/var/lib/backend.ai
      - /tmp/backend.ai:/tmp/backend.ai
      - /vfroot/local:/vfroot/local
    restart: unless-stopped
```

Bind mounts are fixed at container **creation**, so after adding or changing
the parity mounts, recreate the container
(`docker compose up -d --force-recreate agent`) — the entrypoint does re-run
on a plain restart, but the old container's mounts cannot change.
