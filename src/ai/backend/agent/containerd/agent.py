from __future__ import annotations

import asyncio
import logging
import signal
import uuid
from collections.abc import AsyncGenerator, Callable, Iterable, Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from functools import partial
from importlib.resources import files
from io import StringIO
from ipaddress import IPv4Address, ip_address
from pathlib import Path
from time import monotonic
from typing import Any, Final, cast, override

import aiofiles

from ai.backend.agent.agent import (
    ACTIVE_STATUS_SET,
    AbstractAgent,
    AbstractKernelCreationContext,
    ScanImagesResult,
)
from ai.backend.agent.config.unified import AgentUnifiedConfig, ContainerSandboxType
from ai.backend.agent.containerd.client import (
    ContainerdAPI,
    ContainerdClient,
    ContainerdClientConfig,
    ContainerRecord,
    TaskInfo,
    TaskState,
)
from ai.backend.agent.containerd.image import resolve_image
from ai.backend.agent.containerd.kernel import ContainerdKernel
from ai.backend.agent.containerd.lifecycle import (
    clean_container,
    destroy_container,
    is_gone,
    launch_container,
)
from ai.backend.agent.containerd.mounts import host_system_mounts, to_generated_mounts
from ai.backend.agent.containerd.network import KernelNetwork, PortForward
from ai.backend.agent.containerd.profile.base import (
    GeneratedMount,
    KernelLaunch,
    RuntimeProfile,
    StdioMode,
    prepare_kernel_config,
    profile_skips_host_krunner,
)
from ai.backend.agent.containerd.profile.loader import load_runtime_profiles, select_profile
from ai.backend.agent.containerd.profile.runc import RuncProfile
from ai.backend.agent.containerd.scratch import (
    CONFIG_DIR_LABEL,
    Owner,
    ScratchDirs,
    create_scratch,
    read_resource_spec,
    remove_scratch,
    write_config_files,
    write_dotfiles,
    write_hosts_file,
    write_resolv_conf,
)
from ai.backend.agent.containerd.sealed import spec_jws_mount, spec_signature, write_spec_jws
from ai.backend.agent.containerd.spec import (
    SpecInput,
    build_base_spec,
    build_launch_spec,
    merge_env,
)
from ai.backend.agent.errors import UnsupportedResource
from ai.backend.agent.errors.agent import InvalidAgentConfigError, UnsupportedBaseDistroError
from ai.backend.agent.errors.containerd import (
    ContainerTaskStuck,
    KernelNetworkSetupFailed,
    KernelVerbNotSupported,
)
from ai.backend.agent.etcd import AgentEtcdClientView
from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.kernel_registry.writer.types import KernelRegistrySaveMetadata
from ai.backend.agent.port_pool import PortPool
from ai.backend.agent.resources import (
    AbstractComputePlugin,
    ComputerContext,
    KernelResourceSpec,
    Mount,
    known_slot_types,
)
from ai.backend.agent.types import (
    Container,
    KernelOwnershipData,
    LifecycleEvent,
    MountInfo,
    Port,
)
from ai.backend.agent.utils import get_arch_name
from ai.backend.common.asyncio import run_in_executor_with_context
from ai.backend.common.cgroup import CgroupController
from ai.backend.common.docker import ImageRef, KernelFeatures, LabelName
from ai.backend.common.dto.agent.response import PurgeImagesResp
from ai.backend.common.dto.manager.rpc_request import PurgeImagesReq
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.kernel import KernelLifecycleEventReason
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


async def _run_scratch_work[**P, T](func: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    """Run blocking scratch work in the executor; a cancel waits until the thread has finished.

    Otherwise the thread could recreate the scratch dir after its removal.
    """
    work = asyncio.ensure_future(run_in_executor_with_context(None, partial(func, *args, **kwargs)))
    try:
        return await asyncio.shield(work)
    except asyncio.CancelledError:
        while not work.done():
            try:
                await asyncio.wait({work})
            except asyncio.CancelledError:
                pass
        raise


HOST_PORTS_LABEL: Final = "ai.backend.containerd.host-ports"
KERNEL_IP_LABEL: Final = "ai.backend.containerd.kernel-ip"
_INTRINSIC_SLOTS: Final = frozenset({SlotName("cpu"), SlotName("mem")})
_LOG_COLLECT_TIMEOUT_SEC: Final = 60.0
_LOG_CHUNK_BYTES: Final = 64 * 1024
_CONTAINER_STATUS: Final[Mapping[TaskState, ContainerStatus]] = {
    TaskState.CREATED: ContainerStatus.CREATED,
    TaskState.RUNNING: ContainerStatus.RUNNING,
    TaskState.PAUSED: ContainerStatus.PAUSED,
    TaskState.PAUSING: ContainerStatus.PAUSED,
    TaskState.STOPPED: ContainerStatus.EXITED,
    TaskState.UNKNOWN: ContainerStatus.DEAD,
}
_DEFAULT_SHM_BYTES: Final = 64 * 2**20
_STUCK_RETRY_MIN_SEC: Final = 5.0
_STUCK_RETRY_MAX_SEC: Final = 300.0
_STUCK_ESCALATE_SEC: Final = 30 * 60.0


@dataclass(slots=True)
class _StuckKernel:
    """A kernel whose container task is not confirmed gone; its allocations stay reserved."""

    kernel_id: KernelId
    container_id: str
    host_ports: list[int]
    first_failed_at: float
    next_retry_at: float
    attempts: int = 0
    escalated: bool = False


def _kernel_slots(kernel_config: KernelCreationConfig) -> Mapping[SlotName, Decimal]:
    return {
        SlotName(k): v for k, v in ResourceSlot.from_json(kernel_config["resource_slots"]).items()
    }


def _refuse_accelerators(device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]]) -> None:
    for slot, alloc in device_alloc.items():
        if slot not in _INTRINSIC_SLOTS and any(amount > 0 for amount in alloc.values()):
            raise KernelVerbNotSupported(f"accelerator allocation ({slot})")


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


def _host_ports_of(record: ContainerRecord) -> list[int]:
    return [int(p) for p in record.labels.get(HOST_PORTS_LABEL, "").split(",") if p]


def _to_container(record: ContainerRecord, status: ContainerStatus) -> Container:
    """Only host_port is meaningful: the base discards it from the pool on clean."""
    ports = [Port("127.0.0.1", p, p) for p in _host_ports_of(record)]
    return Container(
        id=ContainerId(record.id),
        status=status,
        image=record.image,
        labels=record.labels,
        ports=ports,
        backend_obj=record,
    )


class ContainerdKernelCreationContext(AbstractKernelCreationContext[ContainerdKernel]):
    _profile: RuntimeProfile
    _slots: Mapping[SlotName, Decimal]
    _client: ContainerdAPI
    _port_pool: PortPool
    _network: KernelNetwork
    _address: IPv4Address | None
    _resource_lock: asyncio.Lock
    _dirs: ScratchDirs
    _generated_mounts: list[GeneratedMount]
    _base_spec: dict[str, Any]
    _spec_signature: str | None

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
        slots: Mapping[SlotName, Decimal],
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
        self._slots = slots
        self._client = client
        self._port_pool = port_pool
        self._network = network
        self._address = None
        self._resource_lock = resource_lock
        self._dirs = ScratchDirs.for_kernel(
            local_config.container.scratch_root, str(ownership_data.kernel_id)
        )
        self._generated_mounts = []
        self._base_spec = {}
        # Before the scratch dir exists: a sealed kernel without a signature fails here.
        self._spec_signature = spec_signature(kernel_config)

    def _owner(self) -> Owner | None:
        """Who owns the files in the work dir, as the Docker agent decides it."""
        container = self.local_config.container
        uid_match = KernelFeatures.UID_MATCH in self.kernel_features
        ouid, ogid = self.get_overriding_uid(), self.get_overriding_gid()
        if ouid is None and ogid is None:
            return Owner(container.kernel_uid, container.kernel_gid) if uid_match else None
        return Owner(
            ouid if ouid is not None or not uid_match else container.kernel_uid,
            ogid if ogid is not None or not uid_match else container.kernel_gid,
        )

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

    # FIXME(containerd-mvp): scratch is always a host directory, whatever container.scratch-type
    # says (memory and hostfile are not implemented)
    @override
    async def prepare_scratch(self) -> None:
        await _run_scratch_work(
            create_scratch,
            self._dirs,
            self._owner(),
            clone_dotfiles=not self.restarting,
        )

    # Not mirrored from the Docker agent: the agent socket, domain-socket proxies, extra
    # Docker volumes and the memory-scratch /tmp.
    @override
    async def get_intrinsic_mounts(self) -> Sequence[Mount]:
        mounts = [
            Mount(
                MountTypes.BIND, self._dirs.config, Path("/home/config"), MountPermission.READ_ONLY
            ),
            Mount(MountTypes.BIND, self._dirs.work, Path("/home/work"), MountPermission.READ_WRITE),
            *host_system_mounts(self._dirs.hosts, self._dirs.resolv_conf),
        ]
        coredump = self.local_config.debug.coredump
        if coredump.enabled:
            mounts.append(
                Mount(
                    MountTypes.BIND, coredump.path, coredump.core_path, MountPermission.READ_WRITE
                )
            )
        return mounts

    @property
    @override
    def repl_ports(self) -> Sequence[int]:
        raise KernelVerbNotSupported("repl_ports")

    @property
    @override
    def protected_services(self) -> Sequence[str]:
        raise KernelVerbNotSupported("protected_services")

    # FIXME(containerd-mvp): cluster networking; each kernel has its own netns on the bridge, so
    # cluster sessions get no inter-kernel hostnames
    @override
    async def apply_network(self, cluster_info: ClusterInfo) -> None:
        return None

    # FIXME(containerd-mvp): cluster SSH keys are not installed
    @override
    async def prepare_ssh(self, cluster_info: ClusterInfo) -> None:
        return None

    @override
    async def process_mounts(self, mounts: Sequence[Mount]) -> None:
        self._generated_mounts = to_generated_mounts(mounts)

    # cpu and mem are applied through the spec resources; any other device is refused.
    @override
    async def apply_accelerator_allocation(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> None:
        _refuse_accelerators(device_alloc)

    @override
    async def generate_accelerator_mounts(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> list[MountInfo]:
        _refuse_accelerators(device_alloc)
        return []

    @override
    async def mount_krunner(
        self,
        resource_spec: KernelResourceSpec,
        environ: MutableMapping[str, str],
    ) -> None:
        if not profile_skips_host_krunner(self._profile):
            await super().mount_krunner(resource_spec, environ)
            return
        # The image carries its own krunner: skip the host runner and libbaihook resolution,
        # but keep the accelerator allocation and mounts that the base does in the same step.
        # Plugin hooks and LD_PRELOAD are skipped too: they chain onto the host libbaihook preload.
        for device_view in resource_spec.device_list:
            computer_ctx = self.computers[device_view.device]
            alloc = {device_view.slot: device_view.device_alloc}
            await self.apply_accelerator_allocation(computer_ctx.instance, alloc)
            for mount_info in await self.generate_accelerator_mounts(computer_ctx.instance, alloc):
                resource_spec.mounts.append(
                    self.get_runner_mount(
                        mount_info.mode,
                        mount_info.src_path,
                        mount_info.dst_path.as_posix(),
                        MountPermission.READ_ONLY,
                    )
                )

    @override
    def resolve_krunner_filepath(self, filename: str) -> Path:
        return Path(str(files("ai.backend.runner").joinpath("../" + filename))).resolve()

    @override
    def get_runner_mount(
        self,
        type: MountTypes,
        src: str | Path,
        target: str | Path,
        perm: MountPermission = MountPermission.READ_ONLY,
        opts: Mapping[str, Any] | None = None,
    ) -> Mount:
        return Mount(
            type,
            Path(src),
            Path(target),
            MountPermission(perm),
            opts=opts,
        )

    @override
    async def prepare_container(
        self,
        resource_spec: KernelResourceSpec,
        environ: Mapping[str, str],
        service_ports: list[ServicePort],
        cluster_info: ClusterInfo,
    ) -> ContainerdKernel:
        try:
            return await self._prepare_kernel(resource_spec, environ, service_ports)
        except BaseException:
            # The kernel is not registered yet, so no clean_kernel removes its scratch dir.
            await run_in_executor_with_context(
                None, remove_scratch, self.local_config.container.scratch_root, str(self.kernel_id)
            )
            raise

    async def _prepare_kernel(
        self,
        resource_spec: KernelResourceSpec,
        environ: Mapping[str, str],
        service_ports: list[ServicePort],
    ) -> ContainerdKernel:
        await self._write_config_files(resource_spec, environ)
        extra_caps = (
            ("CAP_SYS_PTRACE",)
            if self.local_config.container.sandbox_type == ContainerSandboxType.JAIL
            else ()
        )
        resource_opts = self.kernel_config.get("resource_opts") or {}
        cpus = resource_spec.allocations.get(DeviceName("cpu"), {}).get(SlotName("cpu"), {})
        mems = resource_spec.allocations.get(DeviceName("mem"), {}).get(SlotName("mem"), {})
        self._base_spec = build_base_spec(
            SpecInput(
                cwd="/home/work",
                hostname=self.kernel_config["cluster_hostname"],
                cpu_cores=sorted(int(core) for core in cpus),
                memory_bytes=int(sum(mems.values())),
                shm_bytes=int(resource_opts.get("shmem") or _DEFAULT_SHM_BYTES),
                netns_path=self._network.netns_path(self.kernel_id),
                extra_caps=extra_caps,
            )
        )
        if self._spec_signature is not None:
            await self._add_spec_jws(self._spec_signature)
        launch = KernelLaunch(
            kernel_id=self.kernel_id,
            session_id=self.session_id,
            config=self.kernel_config,
            slots=self._slots,
            devices=(),  # no accelerator is accepted
            mounts=tuple(self._generated_mounts),
            trusted_storage_path=None,
            base_spec=self._base_spec,
        )
        # The netns exists before plan(); a failure in setup or plan tears it down.
        try:
            self._address = await self._network.setup(self.kernel_id)
            launch_plan = self._profile.plan(launch)
        except BaseException:
            await self._teardown_network()
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
            launch_plan=launch_plan,
        )

    async def _add_spec_jws(self, signature: str) -> None:
        await _run_scratch_work(write_spec_jws, self._dirs.spec_jws, signature)
        # Appended to the base spec, not a GeneratedMount: a profile's spec_patch["mounts"] keeps
        # the base mounts (coco-tdx replaces the list with base mounts + resolver binds).
        self._base_spec["mounts"].append(spec_jws_mount(self._dirs.spec_jws))

    async def _write_config_files(
        self, resource_spec: KernelResourceSpec, environ: Mapping[str, str]
    ) -> None:
        resource_lines = StringIO()
        resource_spec.write_to_file(resource_lines)
        for dev_type, device_alloc in resource_spec.allocations.items():
            plugin = self.computers[dev_type].instance
            for k, v in (await plugin.generate_resource_data(device_alloc)).items():
                resource_lines.write(f"{k}={v}\n")
        owner = self._owner()

        def _write() -> None:
            write_config_files(
                self._dirs,
                environ="".join(f"{k}={v}\n" for k, v in environ.items()),
                resource=resource_lines.getvalue(),
                bootstrap_script=self.kernel_config.get("bootstrap_script"),
                owner=owner,
            )
            write_dotfiles(self._dirs, self.internal_data.get("dotfiles", []), owner)
            write_hosts_file(self._dirs, self.kernel_config["cluster_hostname"])
            write_resolv_conf(self._dirs)

        await _run_scratch_work(_write)

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

    # Every container port of the service ports gets a pool host port and a DNAT rule. The REPL
    # ports stay inside the kernel netns, so the four REPL entries are 0.
    @override
    async def start_container(
        self,
        kernel_obj: AbstractKernel,
        cmdargs: list[str],
        resource_opts: Mapping[str, Any] | None,
        preopen_ports: Sequence[int],
        cluster_info: ClusterInfo,
    ) -> Mapping[str, Any]:
        launch_plan = cast(ContainerdKernel, kernel_obj).launch_plan
        container_id = f"{self.kernel_id}-{uuid.uuid4().hex[:8]}"
        service_ports = kernel_obj.service_ports
        address = self._address
        if address is None:
            raise KernelNetworkSetupFailed("start_container ran before prepare_container")
        host_ports = self._acquire_host_ports(
            sum(len(sport["container_ports"]) for sport in service_ports)
        )
        try:
            image = await resolve_image(self._client, launch_plan.rootfs_image, get_arch_name())
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
                args=["/opt/kernel/entrypoint.sh", *cmdargs],
                env=merge_env(image.env, kernel_obj.environ),
                mounts=self._generated_mounts,
                allowed_mount_kinds=launch_plan.allowed_mount_kinds,
                spec_patch=launch_plan.spec_patch,
                # cgroupfs form: the native API passes no runc options, so runc uses cgroupfs.
                # A profile enabling SystemdCgroup overrides it with spec_patch.
                cgroups_path=f"/{self._client.namespace}/{container_id}",
            )
            stdio = (
                f"file://{self._dirs.task_log}" if launch_plan.stdio is StdioMode.LOG_FILE else ""
            )
            record = ContainerRecord(
                id=container_id,
                image=launch_plan.rootfs_image,
                snapshotter=self._client.snapshotter,
                snapshot_key=container_id,
                labels=self._container_labels(host_ports, address),
            )
            await launch_container(
                self._client,
                record,
                runtime=launch_plan.runtime_handler,
                chain_id=image.chain_id,
                spec=spec,
                stdio=stdio,
                runtime_options=launch_plan.runtime_options,
            )
        except BaseException:
            await self._teardown_network()
            self._port_pool.release_many(host_ports)
            await self._free_allocations(kernel_obj.resource_spec)
            raise
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

    def _container_labels(self, host_ports: Sequence[int], address: IPv4Address) -> dict[str, str]:
        return {
            LabelName.AGENT_ID: str(self.agent_id),
            LabelName.KERNEL_ID: str(self.kernel_id),
            LabelName.SESSION_ID: str(self.session_id),
            LabelName.OWNER_USER: self.ownership_data.owner_user_id_to_str or "",
            LabelName.OWNER_PROJECT: self.ownership_data.owner_project_id_to_str or "",
            LabelName.OWNER_AGENT: str(self.agent_id),
            LabelName.BLOCK_SERVICE_PORTS: (
                "1" if self.internal_data.get("block_service_ports", False) else "0"
            ),
            HOST_PORTS_LABEL: ",".join(map(str, host_ports)),
            KERNEL_IP_LABEL: str(address),
            CONFIG_DIR_LABEL: str(self._dirs.config),
        }


class ContainerdAgent(
    AbstractAgent[ContainerdKernel, ContainerdKernelCreationContext],
):
    _runtime_profiles: list[RuntimeProfile]
    _profile_required_slots: frozenset[SlotName]
    _runc_profile: RuncProfile
    _client: ContainerdAPI
    _network: KernelNetwork
    _orphan_ports: dict[KernelId, list[int]]
    _stuck_kernels: dict[str, _StuckKernel]  # keyed by container id
    _stuck_retry_task: asyncio.Task[None] | None
    _resources_stale: bool
    _tolerate_lookup_errors: bool
    _lookup_warned: set[str]

    def __init__(
        self,
        etcd: AgentEtcdClientView,
        local_config: AgentUnifiedConfig,
        **kwargs: Any,
    ) -> None:
        # Load first: a bad profile must stop the agent before any background task starts.
        containerd_config = local_config.containerd
        runtime_profiles = load_runtime_profiles(
            containerd_config.runtime_profiles, containerd_config.profiles
        )
        _check_bind_host(local_config.container.bind_host)
        _check_advertised_host(local_config.container.advertised_host or "0.0.0.0")
        super().__init__(etcd, local_config, **kwargs)
        self._runtime_profiles = runtime_profiles
        self._profile_required_slots = frozenset(
            SlotName(s) for s in containerd_config.profile_required_slots
        )
        self._runc_profile = RuncProfile(local_config.kernel_lifecycles.init_timeout_sec)
        self._orphan_ports = {}
        self._stuck_kernels = {}
        self._stuck_retry_task = None
        self._resources_stale = False
        self._tolerate_lookup_errors = False
        self._lookup_warned = set()
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
            )
        )

    @override
    async def _restore_container_resources(
        self,
        kernel_id: KernelId,
        container: Container,
        *,
        strict: bool = True,
    ) -> None:
        """Restore from resource.txt; accelerator plugins' restore expects a Docker container.

        The plugin hook is not called; a read failure always warns and continues."""
        try:
            spec = await read_resource_spec(container.labels)
        except Exception as e:
            log.warning(
                "kernel resource info read failed",
                kernel_id=kernel_id,
                session_id=container.labels.get(LabelName.SESSION_ID),
                container_id=container.id,
                error_repr=repr(e),
            )
            return
        if spec is None:
            return
        for device_name, allocation in spec.allocations.items():
            if (computer_ctx := self.computers.get(device_name)) is not None:
                computer_ctx.alloc_map.apply_allocation(allocation)

    @override
    async def __ainit__(self) -> None:
        # The base class scans the running kernels, so the client must be connected before it.
        config = self.local_config.containerd
        await self._client.connect()
        log.info("containerd connected", address=config.address, namespace=config.namespace)
        await self._network.init()
        await self._record_orphans()
        await self._seed_stuck_kernels()
        # A container whose task cannot be read is skipped, not reported dead, while starting.
        self._tolerate_lookup_errors = True
        try:
            await super().__ainit__()
        finally:
            self._tolerate_lookup_errors = False
        # The base scan restores active containers only; the stopped ones still hold devices.
        async with self.registry_lock:
            await self.reconstruct_resource_usage()
        self._stuck_retry_task = asyncio.create_task(self._stuck_retry_loop())

    async def _record_orphans(self) -> None:
        """Recovery is a stub, so each container found at startup has no kernel object.

        Its ports are returned once, by its clean; its address is kept until then, and the
        network of any kernel without a container is swept.
        """
        known: list[KernelId] = []
        for kernel_id, record, task in await self._scan_containers():
            known.append(kernel_id)
            if address := record.labels.get(KERNEL_IP_LABEL):
                self._network.restore(kernel_id, IPv4Address(address))
            if isinstance(task, BackendAIError):
                log.warning(
                    "container task lookup failed at startup",
                    kernel_id=kernel_id,
                    container_id=record.id,
                )
                continue
            if task is not None and _CONTAINER_STATUS[task.state] in ACTIVE_STATUS_SET:
                self._orphan_ports[kernel_id] = _host_ports_of(record)
        await self._network.sweep(known)

    async def _seed_stuck_kernels(self) -> None:
        """Resume the retry of containers whose task is stopped or unreadable but not removed.

        A task still running is destroyed by the lifecycle sync, which must be enabled.
        """
        now = monotonic()
        for kernel_id, record, task in await self._scan_containers():
            if task is None or (isinstance(task, TaskInfo) and not is_gone(task)):
                continue
            host_ports = _host_ports_of(record)
            for port in host_ports:
                self.port_pool.discard(port)
            self._stuck_kernels[record.id] = _StuckKernel(
                kernel_id=kernel_id,
                container_id=record.id,
                host_ports=host_ports,
                first_failed_at=now,
                next_retry_at=now + _STUCK_RETRY_MIN_SEC,
            )
            log.warning(
                "container task not confirmed gone at startup",
                kernel_id=kernel_id,
                container_id=record.id,
            )

    @override
    async def shutdown(self, stop_signal: signal.Signals) -> None:
        try:
            await super().shutdown(stop_signal)
        finally:
            if self._stuck_retry_task is not None:
                self._stuck_retry_task.cancel()
                await asyncio.wait({self._stuck_retry_task})
            await self._client.close()

    @override
    def _restore_ports(self, host_ports: Iterable[int]) -> None:
        held = {port for entry in self._stuck_kernels.values() for port in entry.host_ports}
        super()._restore_ports(port for port in host_ports if port not in held)

    # FIXME(containerd-mvp): kernel recovery is not supported; an agent restart destroys
    # running kernels
    @override
    async def _load_kernel_registry_from_recovery(self) -> dict[KernelId, AbstractKernel]:
        log.warning("kernel registry recovery skipped")
        return {}

    # FIXME(containerd-mvp): the kernel registry is not persisted
    @override
    async def _write_kernel_registry_to_recovery(
        self,
        kernel_registry: Mapping[KernelId, AbstractKernel],
        metadata: KernelRegistrySaveMetadata,
    ) -> None:
        return None

    async def _scan_containers(
        self,
    ) -> list[tuple[KernelId, ContainerRecord, TaskInfo | BackendAIError | None]]:
        """Own containers with their task; a failed task lookup is returned in its place."""
        if not self._client.connected:
            # The base cleanup loop may run before __ainit__ has connected the client.
            return []
        records = await self._client.list_containers({
            LabelName.OWNER_AGENT: str(self.id),
            LabelName.KERNEL_ID: "",
        })
        tasks = await asyncio.gather(
            *(self._client.get_task(r.id) for r in records), return_exceptions=True
        )
        result: list[tuple[KernelId, ContainerRecord, TaskInfo | BackendAIError | None]] = []
        for record, task in zip(records, tasks, strict=True):
            kernel_id = _kernel_id_of(record)
            if kernel_id is None:
                continue
            if record.labels.get(LabelName.OWNER_AGENT) != str(self.id):
                continue  # the server-side filter is a pre-selection only
            if isinstance(task, BaseException) and not isinstance(task, BackendAIError):
                raise task
            result.append((kernel_id, record, task))
        return result

    @override
    async def enumerate_containers(
        self,
        status_filter: frozenset[ContainerStatus] = ACTIVE_STATUS_SET,
    ) -> Sequence[tuple[KernelId, Container]]:
        result: list[tuple[KernelId, Container]] = []
        for kernel_id, record, task in await self._scan_containers():
            if record.id in self._stuck_kernels:
                continue  # the retry loop is the only cleaner of a stuck container
            if isinstance(task, BackendAIError):
                if not self._tolerate_lookup_errors:
                    raise task
                if record.id not in self._lookup_warned:
                    self._lookup_warned.add(record.id)
                    log.warning("container task lookup failed", container_id=record.id)
                continue
            self._lookup_warned.discard(record.id)
            if task is None:
                # A task is gone once it stops; a container without one counts as exited.
                status = ContainerStatus.EXITED
            else:
                status = _CONTAINER_STATUS[task.state]
            if status in status_filter:
                result.append((kernel_id, _to_container(record, status)))
        return result

    async def _held_containers(self) -> Sequence[tuple[KernelId, Container]]:
        """Every container with a task in any state, or whose task lookup fails."""
        result: list[tuple[KernelId, Container]] = []
        for kernel_id, record, task in await self._scan_containers():
            if task is None:
                continue
            status = (
                ContainerStatus.DEAD
                if isinstance(task, BackendAIError)
                else _CONTAINER_STATUS[task.state]
            )
            result.append((kernel_id, _to_container(record, status)))
        return result

    @override
    async def reconstruct_resource_usage(self) -> None:
        """Rebuild the alloc maps from the resource.txt of every held container.

        The base sees active containers only; a stopped or unreadable task still holds devices.
        """
        containers = await self._held_containers()
        async with self.resource_lock:
            for computer_ctx in self.computers.values():
                computer_ctx.alloc_map.clear()
            for kernel_id, container in containers:
                await self._restore_container_resources(kernel_id, container, strict=False)

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
        if restarting:
            self._refuse_while_stuck(ownership_data.kernel_id)
        slots = _kernel_slots(kernel_config)
        profile = select_profile(
            self._runtime_profiles,
            self._profile_required_slots,
            slots,
            builtin=self._runc_profile,
        )
        log.debug(
            "runtime profile selected",
            kernel_id=str(ownership_data.kernel_id),
            profile=profile.name,
        )
        kernel_config = await prepare_kernel_config(profile, kernel_config)
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
            profile=profile,
            slots=slots,
            client=self._client,
            port_pool=self.port_pool,
            network=self._network,
            resource_lock=self.resource_lock,
        )

    def _refuse_while_stuck(self, kernel_id: KernelId) -> None:
        for entry in self._stuck_kernels.values():
            if entry.kernel_id == kernel_id:
                raise ContainerTaskStuck(
                    f"the kernel cannot restart while its container {entry.container_id} "
                    "is not confirmed gone"
                )

    @override
    async def restart_kernel(
        self,
        ownership_data: KernelOwnershipData,
        kernel_image: ImageRef,
        updating_kernel_config: KernelCreationConfig,
    ) -> dict[str, Any]:
        kernel_id = ownership_data.kernel_id
        self._refuse_while_stuck(kernel_id)
        result = await super().restart_kernel(ownership_data, kernel_image, updating_kernel_config)
        if kernel_id in self.restarting_kernels:
            # The old container got stuck during this restart and the base swallowed the refusal.
            try:
                self._refuse_while_stuck(kernel_id)
            except ContainerTaskStuck:
                self.restarting_kernels.pop(kernel_id, None)
                if (kernel_obj := self.kernel_registry.get(kernel_id)) is not None:
                    kernel_obj.termination_reason = None  # RESTARTING would replace the reason
                await self.inject_container_lifecycle_event(
                    kernel_id,
                    ownership_data.session_id,
                    LifecycleEvent.CLEAN,
                    KernelLifecycleEventReason.FAILED_TO_START,
                )
                raise
        return result

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
        dirs = ScratchDirs.for_kernel(self.local_config.container.scratch_root, str(kernel_id))
        if container_id is not None:
            await self._collect_task_log(kernel_id, container_id, dirs)
            if not self.local_config.debug.skip_container_deletion:
                try:
                    await clean_container(self._client, str(container_id))
                except ContainerTaskStuck:
                    await self._hold_stuck(kernel_id, str(container_id))
                    return
                except BackendAIError:
                    log.exception("container delete failed", container_id=container_id)
            # Ports of kernels created by this process are released by the base.
            self.port_pool.release_many(self._orphan_ports.pop(kernel_id, []))
            if entry := self._stuck_kernels.pop(str(container_id), None):
                self.port_pool.release_many(entry.host_ports)
        await self._remove_kernel_leftovers(kernel_id, restarting)

    async def _remove_kernel_leftovers(self, kernel_id: KernelId, restarting: bool) -> None:
        try:
            await self._network.teardown(kernel_id)
        except BackendAIError:
            log.exception("kernel network teardown failed")
        if not restarting:
            await run_in_executor_with_context(
                None, remove_scratch, self.local_config.container.scratch_root, str(kernel_id)
            )

    async def _hold_stuck(self, kernel_id: KernelId, container_id: str) -> None:
        """Keep the allocations, ports, network and scratch of a kernel whose task survives."""
        entry = self._stuck_kernels.get(container_id)
        if entry is None:
            host_ports: set[int] = set(self._orphan_ports.pop(kernel_id, []))
            if (kernel_obj := self.kernel_registry.get(kernel_id)) is not None:
                host_ports.update(kernel_obj.get("host_ports") or [])
                kernel_obj["host_ports"] = []  # the base must not release them again
            try:
                record = await self._client.get_container(container_id)
            except BackendAIError:
                record = None
            if record is not None:
                host_ports.update(_host_ports_of(record))
            now = monotonic()
            self._stuck_kernels[container_id] = entry = _StuckKernel(
                kernel_id=kernel_id,
                container_id=container_id,
                host_ports=sorted(host_ports),
                first_failed_at=now,
                next_retry_at=now + _STUCK_RETRY_MIN_SEC,
            )
        log.warning(
            "container task not confirmed gone; allocations held",
            kernel_id=kernel_id,
            container_id=container_id,
            attempts=entry.attempts,
        )

    async def _stuck_retry_loop(self) -> None:
        while True:
            try:
                await self._retry_stuck_kernels()
            except Exception:
                log.exception("stuck container retry cycle failed")
            await asyncio.sleep(_STUCK_RETRY_MIN_SEC)

    async def _retry_stuck_kernels(self) -> None:
        if self._resources_stale:
            async with self.registry_lock:
                await self._rebuild_resources()
        for entry in list(self._stuck_kernels.values()):
            if monotonic() < entry.next_retry_at:
                continue
            try:
                await self._retry_stuck(entry)
            except Exception:
                log.exception("stuck container retry failed", container_id=entry.container_id)
                await self._back_off(entry)

    async def _back_off(self, entry: _StuckKernel) -> None:
        """Delay the next retry; the caller is in an except block, which the error event reports."""
        now = monotonic()
        stuck_sec = now - entry.first_failed_at
        entry.next_retry_at = now + min(
            _STUCK_RETRY_MIN_SEC * 2**entry.attempts, _STUCK_RETRY_MAX_SEC
        )
        log.warning(
            "container task still not confirmed gone",
            kernel_id=entry.kernel_id,
            container_id=entry.container_id,
            attempts=entry.attempts,
            stuck_sec=stuck_sec,
        )
        if stuck_sec >= _STUCK_ESCALATE_SEC and not entry.escalated:
            entry.escalated = True
            try:
                await self.produce_error_event()
            except Exception:
                log.exception("stuck container error event failed", container_id=entry.container_id)

    async def _rebuild_resources(self) -> None:
        """Rebuild the alloc maps; a failure is retried on the next cycle."""
        try:
            await self.reconstruct_resource_usage()
        except Exception:
            self._resources_stale = True
            log.exception("resource usage rebuild failed; retrying on the next cycle")
        else:
            self._resources_stale = False

    async def _retry_stuck(self, entry: _StuckKernel) -> None:
        if self._stuck_kernels.get(entry.container_id) is not entry:
            return
        entry.attempts += 1
        # The clean runs outside the registry lock: it can wait for the kill and the RPCs.
        try:
            await clean_container(self._client, entry.container_id)
        except ContainerTaskStuck:
            await self._back_off(entry)
            return
        except BackendAIError:
            # The task is gone, so the allocations are freed; clean_container logged it.
            log.warning("container record left behind", container_id=entry.container_id)
        async with self.registry_lock:
            if self._stuck_kernels.get(entry.container_id) is not entry:
                return  # a clean event of the same container finished it meanwhile
            del self._stuck_kernels[entry.container_id]
            try:
                self.port_pool.release_many(entry.host_ports)
                self._orphan_ports.pop(entry.kernel_id, None)
                await self._remove_kernel_leftovers(
                    entry.kernel_id, entry.kernel_id in self.restarting_kernels
                )
            except Exception:
                log.exception("stuck container leftovers cleanup failed", kernel_id=entry.kernel_id)
            await self._rebuild_resources()
        log.info(
            "stuck container cleaned",
            kernel_id=entry.kernel_id,
            container_id=entry.container_id,
            attempts=entry.attempts,
        )

    async def _collect_task_log(
        self, kernel_id: KernelId, container_id: ContainerId, dirs: ScratchDirs
    ) -> None:
        async def log_iter() -> AsyncGenerator[bytes]:
            try:
                async with aiofiles.open(dirs.task_log, "rb") as fp:
                    while chunk := await fp.read(_LOG_CHUNK_BYTES):
                        yield chunk
            except FileNotFoundError:
                return

        try:
            async with asyncio.timeout(_LOG_COLLECT_TIMEOUT_SEC):
                await self.collect_logs(kernel_id, str(container_id), log_iter())
        except TimeoutError:
            log.warning("container log collection timed out", container_id=container_id)
        except Exception as e:
            log.warning("container log collection failed", container_id=container_id, exc_info=e)

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
