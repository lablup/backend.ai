from __future__ import annotations

import asyncio
import logging
import signal
import uuid
from collections.abc import AsyncGenerator, Mapping, Sequence
from decimal import Decimal
from functools import partial
from importlib.resources import files
from io import StringIO
from pathlib import Path
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
    TaskState,
)
from ai.backend.agent.containerd.image import resolve_image
from ai.backend.agent.containerd.kernel import ContainerdKernel
from ai.backend.agent.containerd.lifecycle import (
    clean_container,
    destroy_container,
    launch_container,
)
from ai.backend.agent.containerd.mounts import host_system_mounts, to_generated_mounts
from ai.backend.agent.containerd.profile.base import (
    GeneratedMount,
    KernelLaunch,
    RuntimeProfile,
    StdioMode,
)
from ai.backend.agent.containerd.profile.loader import load_runtime_profiles, select_profile
from ai.backend.agent.containerd.profile.runc import RuncProfile
from ai.backend.agent.containerd.scratch import (
    CONFIG_DIR_LABEL,
    Owner,
    ScratchDirs,
    create_scratch,
    remove_scratch,
    write_config_files,
    write_dotfiles,
    write_hosts_file,
    write_intrinsic_ports,
)
from ai.backend.agent.containerd.spec import (
    SpecInput,
    build_base_spec,
    build_launch_spec,
    merge_env,
)
from ai.backend.agent.containerd.trusted_storage import (
    attach_trusted_storage,
    detach_trusted_storage,
)
from ai.backend.agent.errors import UnsupportedResource
from ai.backend.agent.errors.agent import UnsupportedBaseDistroError
from ai.backend.agent.errors.containerd import KernelVerbNotSupported
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
from ai.backend.agent.types import Container, KernelOwnershipData, MountInfo, Port
from ai.backend.agent.utils import get_arch_name
from ai.backend.common.asyncio import run_in_executor_with_context
from ai.backend.common.cgroup import CgroupController
from ai.backend.common.docker import ImageRef, KernelFeatures, LabelName
from ai.backend.common.dto.agent.response import PurgeImagesResp
from ai.backend.common.dto.manager.rpc_request import PurgeImagesReq
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.exception import BackendAIError
from ai.backend.common.json import dump_json
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

HOST_PORTS_LABEL: Final = "ai.backend.containerd.host-ports"
_INTRINSIC_SLOTS: Final = frozenset({SlotName("cpu"), SlotName("mem")})
# The kernel runner reads these from intrinsic-ports.json; with the host network they are
# all host ports.
_INTRINSIC_PORT_NAMES: Final = ("replin", "replout", "sshd", "ttyd")
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


def _host_ports_of(record: ContainerRecord) -> list[int]:
    return [int(p) for p in record.labels.get(HOST_PORTS_LABEL, "").split(",") if p]


def _to_container(record: ContainerRecord, status: ContainerStatus) -> Container:
    """The kernel shares the host network, so its ports are host ports on 127.0.0.1."""
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
    _resource_lock: asyncio.Lock
    _dirs: ScratchDirs
    _trusted_storage: Path | None
    _generated_mounts: list[GeneratedMount]
    _base_spec: dict[str, Any]

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
        self._resource_lock = resource_lock
        self._dirs = ScratchDirs.for_kernel(
            local_config.container.scratch_root, str(ownership_data.kernel_id)
        )
        self._trusted_storage = None
        self._generated_mounts = []
        self._base_spec = {}

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
        await run_in_executor_with_context(
            None,
            partial(
                create_scratch,
                self._dirs,
                self._owner(),
                clone_dotfiles=not self.restarting,
            ),
        )
        config = self.local_config.containerd
        # PROVISIONAL(trusted-storage): enabled per profile name; the profile gets the loop device
        if self._profile.name in config.trusted_storage_profiles:
            self._trusted_storage = await attach_trusted_storage(
                self._dirs.trusted_store, int(config.trusted_storage_size)
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
            *host_system_mounts(self._dirs.hosts),
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

    # FIXME(containerd-mvp): cluster networking; the runc kernel shares the host network
    # namespace, so there is nothing to apply and cluster sessions get no inter-kernel hostnames
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
                extra_caps=extra_caps,
            )
        )
        launch = KernelLaunch(
            kernel_id=self.kernel_id,
            session_id=self.session_id,
            config=self.kernel_config,
            slots=self._slots,
            devices=(),  # no accelerator is accepted
            mounts=tuple(self._generated_mounts),
            trusted_storage_path=self._trusted_storage,
            base_spec=self._base_spec,
        )
        launch_plan = self._profile.plan(launch)
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

        await run_in_executor_with_context(None, _write)

    def _acquire_intrinsic_ports(self) -> dict[str, int]:
        acquired: dict[str, int] = {}
        try:
            for name in _INTRINSIC_PORT_NAMES:
                acquired[name] = self._port_pool.acquire()
        except BackendAIError:
            self._port_pool.release_many(acquired.values())
            raise
        return acquired

    async def _free_allocations(self, resource_spec: KernelResourceSpec) -> None:
        async with self._resource_lock:
            for dev_name, device_alloc in resource_spec.allocations.items():
                self.computers[dev_name].alloc_map.free(device_alloc)

    # The REPL, sshd and ttyd ports are host ports, as the kernel shares the host network.
    # start_container returns them in host_ports (released when the kernel is cleaned) and
    # intrinsic_ports; the four REPL entries stay 0.
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
        intrinsic_ports = self._acquire_intrinsic_ports()
        host_ports = list(intrinsic_ports.values())
        try:
            image = await resolve_image(self._client, launch_plan.rootfs_image, get_arch_name())
            await run_in_executor_with_context(
                None, write_intrinsic_ports, self._dirs, dump_json(intrinsic_ports)
            )
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
                labels=self._container_labels(host_ports),
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
            self._port_pool.release_many(host_ports)
            await self._free_allocations(kernel_obj.resource_spec)
            await detach_trusted_storage(self._dirs.trusted_store)
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
            "intrinsic_ports": intrinsic_ports,
        }

    def _container_labels(self, host_ports: Sequence[int]) -> dict[str, str]:
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
            CONFIG_DIR_LABEL: str(self._dirs.config),
        }


class ContainerdAgent(
    AbstractAgent[ContainerdKernel, ContainerdKernelCreationContext],
):
    _runtime_profiles: list[RuntimeProfile]
    _profile_required_slots: frozenset[SlotName]
    _runc_profile: RuncProfile
    _client: ContainerdAPI
    _orphan_ports: dict[KernelId, list[int]]

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
        super().__init__(etcd, local_config, **kwargs)
        self._runtime_profiles = runtime_profiles
        self._profile_required_slots = frozenset(
            SlotName(s) for s in containerd_config.profile_required_slots
        )
        self._runc_profile = RuncProfile(local_config.kernel_lifecycles.init_timeout_sec)
        self._orphan_ports = {}
        # The base class starts a registry cleanup loop in its __init__, which needs the client.
        self._client = ContainerdClient(
            ContainerdClientConfig(
                address=containerd_config.address,
                namespace=containerd_config.namespace,
                snapshotter=containerd_config.snapshotter,
            )
        )

    @override
    async def __ainit__(self) -> None:
        # The base class scans the running kernels, so the client must be connected before it.
        config = self.local_config.containerd
        await self._client.connect()
        log.info("containerd connected", address=config.address, namespace=config.namespace)
        await self._record_orphan_ports()
        await super().__ainit__()

    async def _record_orphan_ports(self) -> None:
        """Recovery is a stub, so each container found at startup has no kernel object.

        Its ports are returned once, by its clean.
        """
        for kernel_id, container in await self.enumerate_containers():
            self._orphan_ports[kernel_id] = [
                p.host_port for p in container.ports if p.host_port is not None
            ]

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
        # A task is gone once it stops; a container without one counts as exited.
        tasks = await asyncio.gather(*(self._client.get_task(r.id) for r in records))
        result: list[tuple[KernelId, Container]] = []
        for record, task in zip(records, tasks, strict=True):
            status = _CONTAINER_STATUS[task.state] if task is not None else ContainerStatus.EXITED
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
        dirs = ScratchDirs.for_kernel(self.local_config.container.scratch_root, str(kernel_id))
        if container_id is not None:
            # Ports of kernels created by this process are released by the base.
            self.port_pool.release_many(self._orphan_ports.pop(kernel_id, []))
            await self._collect_task_log(kernel_id, container_id, dirs)
            if not self.local_config.debug.skip_container_deletion:
                try:
                    await clean_container(self._client, str(container_id))
                except BackendAIError:
                    log.exception("container delete failed", container_id=container_id)
        if not restarting:
            await detach_trusted_storage(dirs.trusted_store)
            await run_in_executor_with_context(
                None, remove_scratch, self.local_config.container.scratch_root, str(kernel_id)
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
