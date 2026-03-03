<!-- context-for-ai
type: detail-doc
parent: BEP-1049 (Kata Containers Agent Backend)
scope: KataAgent, KataKernel, KataKernelCreationContext implementation
depends-on: [configuration-deployment.md]
key-decisions:
  - Full AbstractAgent implementation with Kata-specific lifecycle
  - Container management via containerd gRPC with Kata shim
  - VSOCK for host-guest communication
  - virtio-fs for storage sharing
-->

# BEP-1049: KataAgent Backend

## Summary

KataAgent is the third `AbstractAgent` implementation that manages containers inside lightweight VMs via Kata Containers 3.x. It communicates with containerd's gRPC API to create containers using the Kata runtime shim, replacing Docker API calls with containerd CRI operations.

## Current Design

The existing backend abstraction (`src/ai/backend/agent/types.py`):

```python
class AgentBackend(enum.StrEnum):
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    DUMMY = "dummy"

def get_agent_discovery(backend: AgentBackend) -> AbstractAgentDiscovery:
    agent_mod = importlib.import_module(f"ai.backend.agent.{backend.value}")
    return cast(AbstractAgentDiscovery, agent_mod.get_agent_discovery())
```

`DockerAgent` (`src/ai/backend/agent/docker/agent.py`) manages containers via `aiodocker`:
- Creates containers with `docker.containers.create(container_config)`
- Merges accelerator plugin args via `update_nested_dict(container_config, plugin_args)`
- Monitors events via `docker.events.subscribe()`
- Shares storage via Docker bind mounts (zero overhead, direct kernel VFS)

## Proposed Design

### Package Structure

```
src/ai/backend/agent/kata/
├── __init__.py              # KataAgentDiscovery + get_agent_discovery()
├── agent.py                 # KataAgent + KataKernelCreationContext
├── kernel.py                # KataKernel
├── resources.py             # load_resources(), scan_available_resources()
├── intrinsic.py             # CPU/Memory compute plugins for Kata
└── containerd_client.py     # Async containerd gRPC client wrapper
```

### AgentBackend Enum Extension

```python
# src/ai/backend/agent/types.py
class AgentBackend(enum.StrEnum):
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    KATA = "kata"           # NEW
    DUMMY = "dummy"
```

### KataAgentDiscovery

```python
# src/ai/backend/agent/kata/__init__.py
class KataAgentDiscovery(AbstractAgentDiscovery):
    def get_agent_cls(self) -> type[AbstractAgent[Any, Any]]:
        return KataAgent

    async def load_resources(self, etcd, local_config):
        return await load_resources(etcd, local_config)

    async def scan_available_resources(self, compute_device_types):
        return await scan_available_resources(compute_device_types)

    async def prepare_krunner_env(self, local_config):
        # Kata approach: krunner binaries must be baked into the guest rootfs
        # image, not mounted as Docker volumes. Return paths to verify.
        return await prepare_krunner_env_kata(local_config)

def get_agent_discovery() -> AbstractAgentDiscovery:
    return KataAgentDiscovery()
```

### KataAgent

```python
class KataAgent(AbstractAgent[KataKernel, KataKernelCreationContext]):
```

Key method overrides:

**`__ainit__()`** — Initialize containerd client, validate Kata runtime availability:

```python
async def __ainit__(self):
    await super().__ainit__()
    kata_config = self.local_config.kata
    self._containerd = ContainerdClient(kata_config.containerd_socket)
    await self._containerd.connect()

    # Validate Kata runtime is registered
    runtime_info = await self._containerd.get_runtime_info(
        kata_config.kata_runtime_class
    )
    if not runtime_info:
        raise AgentError("Kata runtime not found in containerd")

    # Detect hypervisor
    self._hypervisor = kata_config.hypervisor
    log.info("KataAgent initialized with hypervisor: {}", self._hypervisor)
```

**`scan_images()`** — Scan container images via containerd (not Docker):

```python
async def scan_images(self):
    images = await self._containerd.list_images()
    # Convert to Backend.AI image format
    # containerd stores images with full references (registry/repo:tag)
```

**`pull_image()`** — Pull via containerd:

```python
async def pull_image(self, image_ref, registry_conf):
    await self._containerd.pull_image(image_ref, auth=registry_conf)
```

**Container lifecycle** — The core difference from DockerAgent:

```
DockerAgent:  docker.containers.create() → docker.containers.start()
KataAgent:    containerd.create_container() → containerd.create_task() → task.start()
              ↓ (internally)
              Kata shim boots VM → virtio-fs setup → VSOCK → kata-agent → container
```

**`destroy_kernel()`** — Stop and remove via containerd:

```python
async def destroy_kernel(self, kernel_id, container_id):
    await self._containerd.stop_task(container_id)
    await self._containerd.delete_task(container_id)
    await self._containerd.delete_container(container_id)
    # Kata shim automatically tears down VM when last container is removed
```

**Event monitoring** — Subscribe to containerd events instead of Docker:

```python
async def _handle_container_events(self):
    async for event in self._containerd.subscribe_events():
        if event.topic == "/tasks/exit":
            kernel_id = self._extract_kernel_id(event)
            await self._handle_kernel_exit(kernel_id, event.exit_status)
```

### KataKernelCreationContext

Key overrides that differ from `DockerKernelCreationContext`:

**`prepare_scratch()`** — Create directories that will be shared via virtio-fs:

Scratch directories are still required for Kata despite the VM having its own boot disk. The VM boot disk (`kata-containers.img`) is a **read-only, shared mini-OS** that only contains the kata-agent — it is not per-session storage. Scratch directories serve a different purpose:

- `/home/config` (RO): Agent-written config files (`environ.txt`, `resource.txt`, SSH keys, accelerator configs) consumed by the kernel runner at startup
- `/home/work` (RW): User's persistent workspace directory and vfolder mount point

The `resource.txt` and `environ.txt` files remain necessary even with VM-level resource isolation. The hypervisor enforces resource **limits** (vCPU, memory), but these files communicate resource **metadata** to the kernel runner — what was allocated, environment variables for the session, accelerator device mappings, etc. The kernel runner reads them to configure the user's environment, not to enforce limits.

```python
async def prepare_scratch(self):
    # Same directory structure as Docker — these are shared into the
    # guest VM via virtio-fs (not the VM boot disk, which is read-only)
    scratch_dir = self.scratch_root / str(self.kernel_id)
    scratch_dir.mkdir(parents=True, exist_ok=True)
    # Write environ.txt, resource.txt, etc. into scratch_dir
    # These become visible inside the guest at /home/config via virtio-fs
```

**`apply_accelerator_allocation()`** — Collect VFIO device info from plugins:

```python
async def apply_accelerator_allocation(self):
    vfio_devices = []
    for dev_type, device_alloc in self.resource_spec.allocations.items():
        computer = self.computers[dev_type].instance
        plugin_args = await computer.generate_docker_args(None, device_alloc)
        # CUDAVFIOPlugin returns {"_kata_vfio_devices": [...]}
        if "_kata_vfio_devices" in plugin_args:
            vfio_devices.extend(plugin_args["_kata_vfio_devices"])
    self._vfio_devices = vfio_devices
```

**`spawn()`** — Create container via containerd with Kata runtime:

```python
async def spawn(self):
    container_config = {
        "image": self.image_ref,
        "runtime": {"name": "io.containerd.kata.v2"},
        "env": self.environ,
        "mounts": self._build_virtio_fs_mounts(),
        "labels": self._build_labels(),
        "annotations": {
            # VFIO devices passed via annotations for Kata shim
            "io.katacontainers.config.hypervisor.hotplug_vfio_on_root_bus": "true",
            **self._build_vfio_annotations(),
        },
    }
    container = await self._containerd.create_container(
        container_id=str(self.kernel_id),
        config=container_config,
    )
    task = await self._containerd.create_task(container.id)
    await task.start()
    return container.id
```

### KataKernel

```python
class KataKernel(AbstractKernel):
    container_id: ContainerId
    sandbox_id: str          # Kata sandbox (VM) identifier

    async def create_code_runner(self):
        # Code runner connects to the kernel process inside the guest VM.
        # The connection path differs from Docker:
        #   Docker: TCP localhost:<mapped_port>
        #   Kata:   TCP <guest_ip>:<service_port> (routed via virtio-net)
        # The guest IP is assigned by the CNI plugin and is reachable
        # from the host via the TC-filter bridge.
        return await create_code_runner(
            kernel_id=self.kernel_id,
            host=self._guest_ip,
            port=self._service_port,
        )

    async def check_status(self):
        status = await self._containerd.get_task_status(self.container_id)
        return status == "running"
```

### ContainerdClient

Async wrapper around containerd's gRPC API:

```python
class ContainerdClient:
    def __init__(self, socket_path: Path):
        self._socket = socket_path

    async def connect(self): ...
    async def close(self): ...

    # Image operations
    async def list_images(self) -> list[ImageInfo]: ...
    async def pull_image(self, ref: str, auth: dict | None = None): ...

    # Container operations
    async def create_container(self, container_id: str, config: dict) -> ContainerInfo: ...
    async def delete_container(self, container_id: str): ...

    # Task operations (a "task" is a running process in containerd)
    async def create_task(self, container_id: str) -> TaskInfo: ...
    async def start_task(self, container_id: str): ...
    async def stop_task(self, container_id: str, timeout: int = 10): ...
    async def delete_task(self, container_id: str): ...
    async def get_task_status(self, container_id: str) -> str: ...

    # Events
    async def subscribe_events(self) -> AsyncIterator[Event]: ...

    # Runtime info
    async def get_runtime_info(self, runtime_class: str) -> dict | None: ...
```

This client uses `grpcio` (or `grpclib` for async) to communicate with containerd's Unix socket. The proto definitions come from the containerd API (`containerd.services.containers.v1`, `containerd.services.tasks.v1`).

## Interface / API

| Class | Extends | Key Responsibility |
|-------|---------|-------------------|
| `KataAgent` | `AbstractAgent[KataKernel, KataKernelCreationContext]` | Container lifecycle via containerd + Kata shim |
| `KataKernel` | `AbstractKernel` | Guest VM container state, code runner connection |
| `KataKernelCreationContext` | `AbstractKernelCreationContext` | VFIO device collection, virtio-fs mounts, containerd spawn |
| `KataAgentDiscovery` | `AbstractAgentDiscovery` | Plugin loading, resource scanning, krunner env |
| `ContainerdClient` | (standalone) | Async containerd gRPC wrapper |

## Implementation Notes

- Kata runtime must be installed on the host; the agent does not install it
- The krunner environment (entrypoint scripts, hook libraries) must be included in the guest rootfs image, unlike Docker where they are mounted from a host volume
- Image format: standard OCI images work unchanged; containerd handles the pull and unpack
- The `[container]` section settings (`scratch-root`, `port-range`) are shared between Docker and Kata backends
- Intrinsic CPU/Memory plugins (`intrinsic.py`) can largely reuse the Docker versions; the main difference is that resource limits apply to the VM (host cgroup) rather than directly to the container process
- Log collection: containerd tasks expose stdout/stderr via FIFO pipes, similar to Docker's log stream
