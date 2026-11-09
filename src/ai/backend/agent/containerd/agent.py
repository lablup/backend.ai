from __future__ import annotations

import asyncio
import logging
import signal
import uuid
from collections.abc import Mapping, MutableMapping, Sequence
from decimal import Decimal
from ipaddress import IPv4Address, ip_address
from pathlib import Path
from typing import Any, Final, cast, override

from aiodocker.docker import Docker

from ai.backend.agent.agent import (
    ACTIVE_STATUS_SET,
    AbstractAgent,
    AbstractKernelCreationContext,
    ScanImagesResult,
)
from ai.backend.agent.config.unified import AgentUnifiedConfig, ContainerSandboxType
from ai.backend.agent.containerd.hostconfig import (
    HostConfigTranslation,
    apply_to_spec,
    merge_translations,
    translate_fragment,
)
from ai.backend.agent.containerd.image import resolve_image
from ai.backend.agent.containerd.intrinsic import CPUSET_LABEL, MEMORY_LABEL
from ai.backend.agent.containerd.kernel import ContainerdKernel
from ai.backend.agent.containerd.lifecycle import (
    clean_container,
    destroy_container,
    launch_container,
)
from ai.backend.agent.containerd.network import KernelNetwork, PortForward
from ai.backend.agent.containerd.profile.base import RuntimeProfile, describe_profile_failure
from ai.backend.agent.containerd.profile.loader import load_runtime_profile
from ai.backend.agent.containerd.rpc.client import ContainerdAPI, ContainerdClient
from ai.backend.agent.containerd.rpc.types import (
    ContainerdClientConfig,
    ContainerRecord,
    TaskState,
)
from ai.backend.agent.containerd.sealed import (
    remove_spec_dir,
    spec_jws_mount,
    spec_jws_path,
    spec_signature,
    write_spec_jws,
)
from ai.backend.agent.containerd.spec import (
    SpecInput,
    build_base_spec,
    build_launch_spec,
    merge_env,
)
from ai.backend.agent.errors import UnsupportedResource
from ai.backend.agent.errors.agent import (
    ContainerCreationFailedError,
    InvalidAgentConfigError,
    UnsupportedBaseDistroError,
)
from ai.backend.agent.errors.containerd import KernelNetworkSetupFailed, KernelVerbNotSupported
from ai.backend.agent.etcd import AgentEtcdClientView
from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.port_pool import PortPool
from ai.backend.agent.resources import (
    AbstractComputePlugin,
    ComputerContext,
    KernelResourceSpec,
    Mount,
    known_slot_types,
)
from ai.backend.agent.types import Container, KernelOwnershipData, MountInfo, Port
from ai.backend.agent.utils import get_arch_name
from ai.backend.common.cgroup import CgroupController
from ai.backend.common.docker import ImageRef, LabelName
from ai.backend.common.dto.agent.response import PurgeImagesResp
from ai.backend.common.dto.manager.rpc_request import PurgeImagesReq
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import (
    AutoPullBehavior,
    ClusterInfo,
    ClusterSSHPortMapping,
    ContainerId,
    ContainerStatus,
    DeviceId,
    DeviceName,
    ImageConfig,
    ImageRegistry,
    KernelCreationConfig,
    KernelId,
    MountPermission,
    MountTypes,
    ResourceSlot,
    Sentinel,
    ServicePort,
    SlotName,
    current_resource_slots,
)
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


_CONTAINER_STATUS: Final[Mapping[TaskState, ContainerStatus]] = {
    TaskState.CREATED: ContainerStatus.CREATED,
    TaskState.RUNNING: ContainerStatus.RUNNING,
    TaskState.PAUSED: ContainerStatus.PAUSED,
    TaskState.PAUSING: ContainerStatus.PAUSED,
    TaskState.STOPPED: ContainerStatus.EXITED,
}
HOST_PORTS_LABEL: Final = "ai.backend.containerd.host-ports"
KERNEL_IP_LABEL: Final = "ai.backend.containerd.kernel-ip"
_INTRINSIC_DEVICES: Final = frozenset({DeviceName("cpu"), DeviceName("mem")})
# A plugin's generate_docker_args must not use its docker argument; one that does
# fails with AttributeError.
_NO_DOCKER: Final = cast(Docker, None)


def _allocated(resource_spec: KernelResourceSpec) -> tuple[list[int], int]:
    """The kernel's cpuset cores and memory bytes."""
    cpus = resource_spec.allocations.get(DeviceName("cpu"), {}).get(SlotName("cpu"), {})
    mems = resource_spec.allocations.get(DeviceName("mem"), {}).get(SlotName("mem"), {})
    return sorted(int(core) for core in cpus), int(sum(mems.values()))


def _bind_mount(info: MountInfo) -> dict[str, Any]:
    if info.mode != MountTypes.BIND:
        raise KernelVerbNotSupported(f"accelerator mount type {info.mode} ({info.dst_path})")
    return {
        "destination": str(info.dst_path),
        "type": "bind",
        "source": str(info.src_path),
        "options": ["rbind", "ro", "rprivate"],
    }


def _kernel_id_of(record: ContainerRecord) -> KernelId | None:
    try:
        return KernelId(uuid.UUID(record.labels[LabelName.KERNEL_ID]))
    except (KeyError, ValueError):
        return None


def _check_bind_host(host: str) -> None:
    """The DNAT match needs an IPv4 literal; loopback is never DNATed."""
    if host in ("", "0.0.0.0"):
        return
    try:
        usable = not IPv4Address(host).is_loopback
    except ValueError:
        usable = False
    if not usable:
        raise InvalidAgentConfigError(
            "container.bind-host must be empty, 0.0.0.0 or a non-loopback IPv4 address: " + host
        )


def _check_advertised_host(host: str) -> None:
    try:
        loopback = ip_address(host).is_loopback
    except ValueError:
        loopback = host.lower() == "localhost"
    if loopback:
        raise InvalidAgentConfigError(
            f"container.advertised-host must not be a loopback address: {host}"
        )


def _to_container(record: ContainerRecord, status: ContainerStatus) -> Container:
    """Only host_port is meaningful: the base discards it from the pool on startup."""
    host_ports = [int(p) for p in record.labels.get(HOST_PORTS_LABEL, "").split(",") if p]
    return Container(
        id=ContainerId(record.id),
        status=status,
        image=record.image,
        labels=record.labels,
        ports=[Port("127.0.0.1", p, p) for p in host_ports],
        backend_obj=record,
    )


class ContainerdKernelCreationContext(AbstractKernelCreationContext[ContainerdKernel]):
    _profile: RuntimeProfile
    _client: ContainerdAPI
    _port_pool: PortPool
    _network: KernelNetwork
    _address: IPv4Address | None
    _resource_lock: asyncio.Lock
    _base_spec: dict[str, Any]
    _spec_signature: str | None
    _spec_mount: dict[str, Any] | None
    _host_configs: list[tuple[str, HostConfigTranslation]]
    _accelerator_allocs: list[
        tuple[AbstractComputePlugin, Mapping[SlotName, Mapping[DeviceId, Decimal]]]
    ]

    def __init__(
        self,
        ownership_data: KernelOwnershipData,
        event_producer: EventProducer,
        kernel_image: ImageRef,
        kernel_config: KernelCreationConfig,
        distro: str,
        local_config: AgentUnifiedConfig,
        computers: Mapping[DeviceName, ComputerContext],
        restarting: bool = False,
        *,
        profile: RuntimeProfile,
        client: ContainerdAPI,
        port_pool: PortPool,
        network: KernelNetwork,
        resource_lock: asyncio.Lock,
    ) -> None:
        super().__init__(
            ownership_data,
            event_producer,
            kernel_image,
            kernel_config,
            distro,
            local_config,
            computers,
            restarting=restarting,
        )
        self._profile = profile
        self._client = client
        self._port_pool = port_pool
        self._network = network
        self._address = None
        self._resource_lock = resource_lock
        self._base_spec = {}
        # Read first: a sealed kernel without a signature fails before anything is created.
        self._spec_signature = spec_signature(kernel_config)
        self._spec_mount = None
        self._host_configs = []
        self._accelerator_allocs = []

    @override
    async def get_extra_envs(self) -> Mapping[str, str]:
        return {}

    @override
    async def prepare_resource_spec(
        self,
    ) -> tuple[KernelResourceSpec, Mapping[str, Any] | None]:
        if self.restarting:
            raise KernelVerbNotSupported("restart_kernel")
        slots = ResourceSlot.from_json(self.kernel_config["resource_slots"])
        # Ensure that we have intrinsic slots.
        if SlotName("cpu") not in slots:
            raise UnsupportedResource("cpu slot is required")
        if SlotName("mem") not in slots:
            raise UnsupportedResource("mem slot is required")
        # accept unknown slot type with zero values
        # but reject if they have non-zero values.
        for st, sv in slots.items():
            if st not in known_slot_types and sv != Decimal(0):
                raise UnsupportedResource(st)
        # sanitize the slots
        current_resource_slots.set(known_slot_types)
        slots = slots.normalize_slots(ignore_unknown=True)
        resource_spec = KernelResourceSpec(
            allocations={},
            slots=slots.copy(),
            mounts=[],
            scratch_disk_size=0,  # TODO: implement (#70)
        )
        resource_opts = self.kernel_config.get("resource_opts", {})
        return resource_spec, resource_opts

    # No scratch directory: the kernel sees only its image rootfs.
    @override
    async def prepare_scratch(self) -> None:
        return None

    @override
    async def get_intrinsic_mounts(self) -> Sequence[Mount]:
        return []

    @property
    @override
    def repl_ports(self) -> Sequence[int]:
        raise KernelVerbNotSupported("repl_ports")

    @property
    @override
    def protected_services(self) -> Sequence[str]:
        raise KernelVerbNotSupported("protected_services")

    # FIXME(containerd-mvp): cluster networking; cluster sessions get no inter-kernel hostnames
    @override
    async def apply_network(self, cluster_info: ClusterInfo) -> None:
        return None

    # FIXME(containerd-mvp): cluster SSH keys are not installed
    @override
    async def prepare_ssh(self, cluster_info: ClusterInfo) -> None:
        return None

    # Nothing is mounted into the kernel; requested mounts (vfolders) are refused, not dropped.
    @override
    async def process_mounts(self, mounts: Sequence[Mount]) -> None:
        if mounts:
            raise KernelVerbNotSupported(f"mounts ({', '.join(str(m.target) for m in mounts)})")

    # cpu and mem are applied through the spec resources; another plugin's device nodes and
    # env are translated from its Docker container fragment.
    @override
    async def apply_accelerator_allocation(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> None:
        if computer.key in _INTRINSIC_DEVICES:
            return
        fragment = await computer.generate_docker_args(_NO_DOCKER, device_alloc)
        name = str(computer.key)
        translation = await asyncio.to_thread(translate_fragment, name, fragment)
        self._host_configs = [*self._host_configs, (name, translation)]
        merge_translations(self._host_configs)

    # No kernel runner: the image's own command runs, so no runner files are mounted. The
    # accelerators' allocations are still applied, and their env goes into the kernel environ.
    @override
    async def mount_krunner(
        self,
        resource_spec: KernelResourceSpec,
        environ: MutableMapping[str, str],
    ) -> None:
        # The plugin mounts are generated in prepare_container, where a failure removes the dir.
        for view in resource_spec.device_list:
            if view.device in _INTRINSIC_DEVICES:
                continue
            computer = self.computers[view.device].instance
            alloc = {view.slot: view.device_alloc}
            await self.apply_accelerator_allocation(computer, alloc)
            self._accelerator_allocs.append((computer, alloc))
        environ.update(merge_translations(self._host_configs).env)

    @override
    async def generate_accelerator_mounts(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> list[MountInfo]:
        if computer.key in _INTRINSIC_DEVICES:
            return []
        src_path = (
            self.local_config.container.scratch_root / str(self.kernel_id) / str(computer.key)
        )
        await asyncio.to_thread(src_path.mkdir, parents=True, exist_ok=True)
        return await computer.generate_mounts(src_path, device_alloc)

    @override
    def resolve_krunner_filepath(self, filename: str) -> Path:
        raise KernelVerbNotSupported("resolve_krunner_filepath")

    @override
    def get_runner_mount(
        self,
        type: MountTypes,
        src: str | Path,
        target: str | Path,
        perm: MountPermission = MountPermission.READ_ONLY,
        opts: Mapping[str, Any] | None = None,
    ) -> Mount:
        raise KernelVerbNotSupported("get_runner_mount")

    @override
    async def prepare_container(
        self,
        resource_spec: KernelResourceSpec,
        environ: Mapping[str, str],
        service_ports: list[ServicePort],
        cluster_info: ClusterInfo,
    ) -> ContainerdKernel:
        extra_caps = (
            ("CAP_SYS_PTRACE",)
            if self.local_config.container.sandbox_type == ContainerSandboxType.JAIL
            else ()
        )
        resource_opts = self.kernel_config.get("resource_opts") or {}
        cores, memory_bytes = _allocated(resource_spec)
        self._base_spec = build_base_spec(
            SpecInput(
                hostname=self.kernel_config["cluster_hostname"],
                cpu_cores=cores,
                memory_bytes=memory_bytes,
                shm_bytes=int(resource_opts.get("shmem") or 0),
                netns_path=self._network.netns_path(self.kernel_id),
                extra_caps=extra_caps,
            )
        )
        self._base_spec = apply_to_spec(self._base_spec, merge_translations(self._host_configs))
        # A failed setup tears down what it created, including the plugins' scratch dirs.
        try:
            for computer, alloc in self._accelerator_allocs:
                for info in await self.generate_accelerator_mounts(computer, alloc):
                    self._base_spec["mounts"].append(_bind_mount(info))
            if self._spec_signature is not None:
                await self._add_spec_jws(self._spec_signature)
            self._address = await self._network.setup(self.kernel_id)
        except BaseException:
            await self._teardown_network()
            await self._remove_spec_dir()
            raise
        return ContainerdKernel(
            self.ownership_data,
            self.kernel_config["network_id"],
            self.image_ref,
            self.kspec_version,
            agent_config=self.local_config.model_dump(by_alias=True),
            resource_spec=resource_spec,
            service_ports=service_ports,
            environ=environ,
            data={},
            client=self._client,
            profile=self._profile,
        )

    async def _add_spec_jws(self, signature: str) -> None:
        root = self.local_config.container.scratch_root
        path = spec_jws_path(root, str(self.kernel_id))
        await asyncio.to_thread(write_spec_jws, path, signature)
        self._spec_mount = spec_jws_mount(path)

    # Removes the kernel's whole scratch dir: the spec JWS and the plugins' mount dirs.
    async def _remove_spec_dir(self) -> None:
        root = self.local_config.container.scratch_root
        await asyncio.to_thread(remove_spec_dir, root, str(self.kernel_id))

    def _acquire_host_ports(self, count: int) -> list[int]:
        acquired: list[int] = []
        try:
            for _ in range(count):
                acquired.append(self._port_pool.acquire())
        except BackendAIError:
            self._port_pool.release_many(acquired)
            raise
        return acquired

    async def _teardown_network(self) -> None:
        try:
            await self._network.teardown(self.kernel_id)
        except BackendAIError:
            log.exception("kernel network teardown failed", kernel_id=self.kernel_id)

    async def _free_allocations(self, resource_spec: KernelResourceSpec) -> None:
        async with self._resource_lock:
            for dev_name, device_alloc in resource_spec.allocations.items():
                self.computers[dev_name].alloc_map.free(device_alloc)

    # Every container port of the service ports gets a pool host port and a DNAT rule; the REPL
    # ports are 0. No runner: the task runs the image's own command, so cmdargs are not used.
    @override
    async def start_container(
        self,
        kernel_obj: AbstractKernel,
        cmdargs: list[str],
        resource_opts: Mapping[str, Any] | None,
        preopen_ports: Sequence[int],
        cluster_info: ClusterInfo,
    ) -> Mapping[str, Any]:
        image_name = self.kernel_config["image"]["canonical"]
        container_id = f"{self.kernel_id}-{uuid.uuid4().hex[:8]}"
        service_ports = kernel_obj.service_ports
        host_ports: list[int] = []
        try:
            launch_plan = self._profile.plan(self.kernel_config)
            if isinstance(kernel_obj, ContainerdKernel):
                kernel_obj.launch_plan = launch_plan
            address = self._address
            if address is None:
                raise KernelNetworkSetupFailed("start_container ran before prepare_container")
            host_ports = self._acquire_host_ports(
                sum(len(sport["container_ports"]) for sport in service_ports)
            )
            image = await resolve_image(self._client, image_name, get_arch_name())
            pending = iter(host_ports)
            forwards = [
                PortForward(next(pending), cport)
                for sport in service_ports
                for cport in sport["container_ports"]
            ]
            await self._network.publish(self.kernel_id, forwards)
            pending = iter(host_ports)
            for sport in service_ports:
                sport["host_ports"] = tuple(next(pending) for _ in sport["container_ports"])
            spec = build_launch_spec(
                self._base_spec,
                args=[*image.entrypoint, *image.cmd],
                env=merge_env(image.env, kernel_obj.environ),
                cwd=image.working_dir or "/",
                # cgroupfs path form; a runtime profile must not enable systemd cgroups.
                cgroups_path=f"/{self._client.namespace}/{container_id}",
                spec_patch=launch_plan.spec_patch,
            )
            if self._spec_mount is not None:
                # After the patch: a profile's spec_patch["mounts"] replaces the base list.
                spec.setdefault("mounts", []).append(self._spec_mount)
            record = ContainerRecord(
                id=container_id,
                image=image_name,
                snapshotter=self._client.snapshotter,
                snapshot_key=container_id,
                labels=self._container_labels(kernel_obj.resource_spec, host_ports),
            )
            await launch_container(
                self._client,
                record,
                runtime=launch_plan.runtime_handler,
                chain_id=image.chain_id,
                spec=spec,
                runtime_options=launch_plan.runtime_options,
            )
        except BaseException as e:
            self._port_pool.release_many(host_ports)
            await self._teardown_network()
            await self._free_allocations(kernel_obj.resource_spec)
            await self._remove_spec_dir()
            if not isinstance(e, Exception):
                raise
            reason = describe_profile_failure(self._profile, None, str(e))
            if reason is None:
                raise
            raise ContainerCreationFailedError(
                f"Kernel failed to create container (k:{self.kernel_id!s}, detail: {e!s})",
                failure_reason=reason,
            ) from e
        container = self.local_config.container
        return {
            "container_id": container_id,
            "kernel_host": str(container.advertised_host or container.bind_host),
            "repl_in_port": 0,
            "repl_out_port": 0,
            "stdin_port": 0,
            "stdout_port": 0,
            "host_ports": host_ports,
            "kernel_ip": str(address),
            "published_host": self._network.published_host,
        }

    def _container_labels(
        self, resource_spec: KernelResourceSpec, host_ports: Sequence[int]
    ) -> dict[str, str]:
        cores, memory_bytes = _allocated(resource_spec)
        return {
            HOST_PORTS_LABEL: ",".join(map(str, host_ports)),
            KERNEL_IP_LABEL: str(self._address or ""),
            CPUSET_LABEL: ",".join(map(str, cores)),
            MEMORY_LABEL: str(memory_bytes),
            LabelName.AGENT_ID: str(self.agent_id),
            LabelName.KERNEL_ID: str(self.kernel_id),
            LabelName.SESSION_ID: str(self.session_id),
            LabelName.OWNER_USER: self.ownership_data.owner_user_id_to_str or "",
            LabelName.OWNER_PROJECT: self.ownership_data.owner_project_id_to_str or "",
            LabelName.OWNER_AGENT: str(self.agent_id),
            LabelName.BLOCK_SERVICE_PORTS: (
                "1" if self.internal_data.get("block_service_ports", False) else "0"
            ),
        }


class ContainerdAgent(
    AbstractAgent[ContainerdKernel, ContainerdKernelCreationContext],
):
    _profile: RuntimeProfile
    _client: ContainerdAPI
    _network: KernelNetwork

    def __init__(
        self,
        etcd: AgentEtcdClientView,
        local_config: AgentUnifiedConfig,
        **kwargs: Any,
    ) -> None:
        # Load first: a bad profile must stop the agent before any background task starts.
        containerd_config = local_config.containerd
        profile = load_runtime_profile(
            containerd_config.runtime_profile, containerd_config.profiles
        )
        _check_bind_host(local_config.container.bind_host)
        _check_advertised_host(local_config.container.advertised_host or "0.0.0.0")
        super().__init__(etcd, local_config, **kwargs)
        self._profile = profile
        self._network = KernelNetwork(
            containerd_config.bridge_name,
            containerd_config.bridge_subnet,
            local_config.container.bind_host,
            local_config.container.port_range,
        )
        # The base class starts a registry cleanup loop in its __init__, which needs the client.
        self._client = ContainerdClient(
            ContainerdClientConfig(
                address=containerd_config.address,
                namespace=containerd_config.namespace,
                snapshotter=containerd_config.snapshotter,
                create_task_timeout=containerd_config.create_task_timeout,
            )
        )

    @override
    async def __ainit__(self) -> None:
        # The base class scans the running kernels, so the client must be connected before it.
        config = self.local_config.containerd
        await self._client.connect()
        log.info("containerd connected", address=config.address, namespace=config.namespace)
        try:
            await self._network.init()
            await self._sweep_network()
            await super().__ainit__()
        except BaseException:
            await self._client.close()
            raise

    async def _sweep_network(self) -> None:
        """Keep the addresses of the containers found at startup and remove other netns."""
        found = await self.enumerate_containers(frozenset(ContainerStatus))
        for kernel_id, container in found:
            if address := container.labels.get(KERNEL_IP_LABEL):
                try:
                    self._network.restore(kernel_id, IPv4Address(address))
                except ValueError:
                    log.warning("kernel address label is malformed", kernel_id=kernel_id)
        await self._network.sweep([kernel_id for kernel_id, _ in found])

    @override
    async def shutdown(self, stop_signal: signal.Signals) -> None:
        try:
            await super().shutdown(stop_signal)
        finally:
            await self._client.close()

    # FIXME(containerd-mvp): kernel recovery is not supported; an agent restart destroys
    # running kernels
    @override
    async def _load_kernel_registry_from_recovery(self) -> dict[KernelId, AbstractKernel]:
        log.debug("kernel registry recovery skipped")
        return {}

    # FIXME(containerd-mvp): the kernel registry is not persisted
    @override
    async def _write_kernel_to_recovery(self, kernel: AbstractKernel) -> None:
        return None

    @override
    async def enumerate_containers(
        self,
        status_filter: frozenset[ContainerStatus] = ACTIVE_STATUS_SET,
    ) -> Sequence[tuple[KernelId, Container]]:
        if not self._client.connected:
            # The base cleanup loop may run before __ainit__ has connected the client.
            return []
        records = await self._client.list_containers({
            LabelName.OWNER_AGENT: str(self.id),
            LabelName.KERNEL_ID: "",
        })
        # A container whose task was deleted or never created counts as exited.
        tasks = await asyncio.gather(
            *(self._client.get_task(r.id) for r in records), return_exceptions=True
        )
        result: list[tuple[KernelId, Container]] = []
        for record, task in zip(records, tasks, strict=True):
            if isinstance(task, BaseException):
                if not isinstance(task, Exception):
                    raise task
                log.warning(
                    "failed to get the task of a container",
                    container_id=record.id,
                    error=repr(task),
                )
                continue
            if task is None:
                status = ContainerStatus.EXITED
            elif task.state in _CONTAINER_STATUS:
                status = _CONTAINER_STATUS[task.state]
            else:
                log.debug(
                    "container skipped for its unknown task state",
                    container_id=record.id,
                )
                continue
            kernel_id = _kernel_id_of(record)
            if kernel_id is None or status not in status_filter:
                continue
            if record.labels.get(LabelName.OWNER_AGENT) != str(self.id):
                continue  # the server-side filter is a pre-selection only
            result.append((kernel_id, _to_container(record, status)))
        return result

    @override
    async def resolve_image_distro(self, image: ImageConfig) -> str:
        distro = image["labels"].get(LabelName.BASE_DISTRO)
        if not distro:
            raise UnsupportedBaseDistroError(
                f"image {image['canonical']} has no {LabelName.BASE_DISTRO} label"
            )
        return distro

    @override
    async def get_cgroup_path(
        self, controller: CgroupController, container_id: ContainerId
    ) -> Path:
        raise KernelVerbNotSupported("get_cgroup_path")

    @override
    def get_cgroup_version(self) -> str:
        raise KernelVerbNotSupported("get_cgroup_version")

    @override
    async def extract_image_command(self, image: str) -> list[str] | None:
        raise KernelVerbNotSupported("extract_image_command")

    # FIXME(containerd-mvp): installed images are not reported to the manager
    @override
    async def scan_images(self) -> ScanImagesResult:
        return ScanImagesResult(scanned_images={}, removed_images={})

    @override
    async def pull_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout_seconds: float | None,
    ) -> None:
        raise KernelVerbNotSupported("pull_image")

    @override
    async def push_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout_seconds: float | None | Sentinel = Sentinel.TOKEN,
    ) -> None:
        raise KernelVerbNotSupported("push_image")

    @override
    async def purge_images(self, request: PurgeImagesReq) -> PurgeImagesResp:
        raise KernelVerbNotSupported("purge_images")

    # FIXME(containerd-mvp): the host never pulls; runc images must be imported beforehand
    @override
    async def check_image(
        self, image_ref: ImageRef, image_id: str, auto_pull: AutoPullBehavior
    ) -> bool:
        return False

    @override
    async def init_kernel_context(
        self,
        ownership_data: KernelOwnershipData,
        kernel_image: ImageRef,
        kernel_config: KernelCreationConfig,
        *,
        restarting: bool = False,
        cluster_ssh_port_mapping: ClusterSSHPortMapping | None = None,
    ) -> ContainerdKernelCreationContext:
        distro = await self.resolve_image_distro(kernel_config["image"])
        return ContainerdKernelCreationContext(
            ownership_data,
            self.event_producer,
            kernel_image,
            kernel_config,
            distro,
            self.local_config,
            self.computers,
            restarting=restarting,
            profile=self._profile,
            client=self._client,
            port_pool=self.port_pool,
            network=self._network,
            resource_lock=self.resource_lock,
        )

    @override
    async def destroy_kernel(
        self,
        kernel_id: KernelId,
        container_id: ContainerId | None,
    ) -> None:
        if container_id is None:
            return
        try:
            found = await destroy_container(self._client, str(container_id))
        except BackendAIError:
            log.exception("container stop failed", container_id=container_id)
            await self.error_monitor.capture_exception()
            return
        if not found:
            log.warning("container missing on destroy", container_id=container_id)
            await self.reconstruct_resource_usage()

    @override
    async def clean_kernel(
        self,
        kernel_id: KernelId,
        container_id: ContainerId | None,
        restarting: bool,
    ) -> None:
        if container_id is not None and not self.local_config.debug.skip_container_deletion:
            try:
                await clean_container(self._client, str(container_id))
            except BackendAIError:
                log.exception("container delete failed", container_id=container_id)
        try:
            await self._network.teardown(kernel_id)
        except BackendAIError:
            log.exception("kernel network teardown failed", kernel_id=kernel_id)
        await asyncio.to_thread(
            remove_spec_dir, self.local_config.container.scratch_root, str(kernel_id)
        )

    @override
    async def create_local_network(self, network_name: str) -> None:
        raise KernelVerbNotSupported("create_local_network")

    @override
    async def destroy_local_network(self, network_name: str) -> None:
        raise KernelVerbNotSupported("destroy_local_network")

    @override
    async def restart_kernel__load_config(
        self,
        kernel_id: KernelId,
        name: str,
    ) -> bytes:
        raise KernelVerbNotSupported("restart_kernel__load_config")

    # FIXME(containerd-mvp): restart configs are not stored
    @override
    async def restart_kernel__store_config(
        self,
        kernel_id: KernelId,
        name: str,
        data: bytes,
    ) -> None:
        return None
