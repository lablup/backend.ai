from __future__ import annotations

import asyncio
import logging
import signal
import uuid
from collections.abc import Mapping, MutableMapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any, Final, override

from ai.backend.agent.agent import (
    ACTIVE_STATUS_SET,
    AbstractAgent,
    AbstractKernelCreationContext,
    ScanImagesResult,
)
from ai.backend.agent.config.unified import AgentUnifiedConfig, ContainerSandboxType
from ai.backend.agent.containerd.image import resolve_image
from ai.backend.agent.containerd.kernel import ContainerdKernel
from ai.backend.agent.containerd.lifecycle import (
    clean_container,
    destroy_container,
    launch_container,
)
from ai.backend.agent.containerd.rpc.client import ContainerdAPI, ContainerdClient
from ai.backend.agent.containerd.rpc.types import (
    ContainerdClientConfig,
    ContainerRecord,
    TaskState,
)
from ai.backend.agent.containerd.spec import (
    SpecInput,
    build_base_spec,
    build_launch_spec,
    merge_env,
)
from ai.backend.agent.errors import UnsupportedResource
from ai.backend.agent.errors.agent import UnsupportedBaseDistroError
from ai.backend.agent.errors.containerd import KernelVerbNotSupported
from ai.backend.agent.etcd import AgentEtcdClientView
from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.resources import (
    AbstractComputePlugin,
    ComputerContext,
    KernelResourceSpec,
    Mount,
    known_slot_types,
)
from ai.backend.agent.types import Container, KernelOwnershipData, MountInfo
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
_RUNC_RUNTIME: Final = "io.containerd.runc.v2"
_INTRINSIC_DEVICES: Final = frozenset({DeviceName("cpu"), DeviceName("mem")})


def _allocated(resource_spec: KernelResourceSpec) -> tuple[list[int], int]:
    """The kernel's cpuset cores and memory bytes."""
    cpus = resource_spec.allocations.get(DeviceName("cpu"), {}).get(SlotName("cpu"), {})
    mems = resource_spec.allocations.get(DeviceName("mem"), {}).get(SlotName("mem"), {})
    return sorted(int(core) for core in cpus), int(sum(mems.values()))


def _kernel_id_of(record: ContainerRecord) -> KernelId | None:
    try:
        return KernelId(uuid.UUID(record.labels[LabelName.KERNEL_ID]))
    except (KeyError, ValueError):
        return None


def _to_container(record: ContainerRecord, status: ContainerStatus) -> Container:
    """The kernel publishes no port."""
    return Container(
        id=ContainerId(record.id),
        status=status,
        image=record.image,
        labels=record.labels,
        ports=[],
        backend_obj=record,
    )


class ContainerdKernelCreationContext(AbstractKernelCreationContext[ContainerdKernel]):
    _client: ContainerdAPI
    _resource_lock: asyncio.Lock
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
        client: ContainerdAPI,
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
        self._client = client
        self._resource_lock = resource_lock
        self._base_spec = {}

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

    # cpu and mem are applied through the spec resources; any other plugin is refused.
    @override
    async def apply_accelerator_allocation(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> None:
        if computer.key not in _INTRINSIC_DEVICES:
            raise KernelVerbNotSupported(f"accelerator {computer.key}")

    # No kernel runner: the image's own command runs, so no runner or plugin files are mounted.
    @override
    async def mount_krunner(
        self,
        resource_spec: KernelResourceSpec,
        environ: MutableMapping[str, str],
    ) -> None:
        return None

    @override
    async def generate_accelerator_mounts(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> list[MountInfo]:
        raise KernelVerbNotSupported("generate_accelerator_mounts")

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
                extra_caps=extra_caps,
            )
        )
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
        )

    async def _free_allocations(self, resource_spec: KernelResourceSpec) -> None:
        async with self._resource_lock:
            for dev_name, device_alloc in resource_spec.allocations.items():
                self.computers[dev_name].alloc_map.free(device_alloc)

    # No port is published. No runner either: the task runs the image's own command, so
    # cmdargs (the runner's arguments) are not used.
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
        try:
            image = await resolve_image(self._client, image_name, get_arch_name())
            spec = build_launch_spec(
                self._base_spec,
                args=[*image.entrypoint, *image.cmd],
                env=merge_env(image.env, kernel_obj.environ),
                cwd=image.working_dir or "/",
                # cgroupfs form: the native API passes no runc options, so runc uses cgroupfs.
                cgroups_path=f"/{self._client.namespace}/{container_id}",
            )
            record = ContainerRecord(
                id=container_id,
                image=image_name,
                snapshotter=self._client.snapshotter,
                snapshot_key=container_id,
                labels=self._container_labels(),
            )
            await launch_container(
                self._client,
                record,
                runtime=_RUNC_RUNTIME,
                chain_id=image.chain_id,
                spec=spec,
            )
        except BaseException:
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
        }

    def _container_labels(self) -> dict[str, str]:
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
        }


class ContainerdAgent(
    AbstractAgent[ContainerdKernel, ContainerdKernelCreationContext],
):
    _client: ContainerdAPI

    def __init__(
        self,
        etcd: AgentEtcdClientView,
        local_config: AgentUnifiedConfig,
        **kwargs: Any,
    ) -> None:
        super().__init__(etcd, local_config, **kwargs)
        containerd_config = local_config.containerd
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
            await super().__ainit__()
        except BaseException:
            await self._client.close()
            raise

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
            client=self._client,
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
