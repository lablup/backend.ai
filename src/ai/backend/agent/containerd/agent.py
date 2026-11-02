from __future__ import annotations

import asyncio
import logging
import signal
import uuid
from collections.abc import AsyncGenerator, Callable, Mapping, Sequence
from decimal import Decimal
from functools import partial
from importlib.resources import files
from io import StringIO
from pathlib import Path
from typing import Any, Final, cast, override

import aiodocker
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
from ai.backend.agent.containerd.mounts import host_system_mounts, to_bind_mounts
from ai.backend.agent.containerd.network import KernelNetwork
from ai.backend.agent.containerd.scratch import (
    CONFIG_DIR_LABEL,
    Owner,
    ScratchDirs,
    create_scratch,
    remove_scratch,
    write_config_files,
    write_dotfiles,
    write_hosts_file,
)
from ai.backend.agent.containerd.spec import (
    BindMount,
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
from ai.backend.common.asyncio import run_in_executor_with_context
from ai.backend.common.cgroup import CgroupController
from ai.backend.common.docker import ImageRef, KernelFeatures, LabelName
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
_RUNC_RUNTIME: Final = "io.containerd.runc.v2"
# FIXME(containerd-mvp): no Docker client; in-tree plugins ignore the argument
_NO_DOCKER: Final = cast(aiodocker.Docker, None)


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
    _network: KernelNetwork
    _resource_lock: asyncio.Lock
    _dirs: ScratchDirs
    _bind_mounts: list[BindMount]
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
        self._client = client
        self._network = network
        self._resource_lock = resource_lock
        self._dirs = ScratchDirs.for_kernel(
            local_config.container.scratch_root, str(ownership_data.kernel_id)
        )
        self._bind_mounts = []
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

    # FIXME(containerd-mvp): cluster networking; each kernel has its own netns with loopback
    # only, so cluster sessions get no inter-kernel hostnames
    @override
    async def apply_network(self, cluster_info: ClusterInfo) -> None:
        return None

    # FIXME(containerd-mvp): cluster SSH keys are not installed
    @override
    async def prepare_ssh(self, cluster_info: ClusterInfo) -> None:
        return None

    @override
    async def process_mounts(self, mounts: Sequence[Mount]) -> None:
        self._bind_mounts = to_bind_mounts(mounts)

    # cpu and mem return no Docker container fragment and are applied through the spec
    # resources; a plugin that needs one (devices, env) is refused.
    @override
    async def apply_accelerator_allocation(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> None:
        try:
            if await computer.generate_docker_args(_NO_DOCKER, device_alloc):
                raise KernelVerbNotSupported(f"container arguments of {computer.key}")
        except BaseException:
            # The kernel is not registered yet, so no clean_kernel removes its scratch dir.
            await run_in_executor_with_context(
                None, remove_scratch, self.local_config.container.scratch_root, str(self.kernel_id)
            )
            raise

    @override
    async def generate_accelerator_mounts(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> list[MountInfo]:
        src_path = self._dirs.config / str(computer.key)
        await run_in_executor_with_context(
            None, partial(src_path.mkdir, parents=True, exist_ok=True)
        )
        return await computer.generate_mounts(src_path, device_alloc)

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
                netns_path=self._network.netns_path(self.kernel_id),
                extra_caps=extra_caps,
            )
        )
        # A failure in setup tears down what it created.
        try:
            await self._network.setup(self.kernel_id)
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

        await _run_scratch_work(_write)

    async def _teardown_network(self) -> None:
        try:
            await self._network.teardown(self.kernel_id)
        except BackendAIError:
            log.exception("kernel network teardown failed", kernel_id=self.kernel_id)

    async def _free_allocations(self, resource_spec: KernelResourceSpec) -> None:
        async with self._resource_lock:
            for dev_name, device_alloc in resource_spec.allocations.items():
                self.computers[dev_name].alloc_map.free(device_alloc)

    # No port is published: the REPL and service ports stay inside the kernel netns.
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
                args=["/opt/kernel/entrypoint.sh", *cmdargs],
                env=merge_env(image.env, kernel_obj.environ),
                mounts=self._bind_mounts,
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
                stdio=f"file://{self._dirs.task_log}",
            )
        except BaseException:
            await self._teardown_network()
            await self._free_allocations(kernel_obj.resource_spec)
            await run_in_executor_with_context(
                None, remove_scratch, self.local_config.container.scratch_root, str(self.kernel_id)
            )
            raise
        return {"container_id": container_id}

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
            CONFIG_DIR_LABEL: str(self._dirs.config),
        }


class ContainerdAgent(
    AbstractAgent[ContainerdKernel, ContainerdKernelCreationContext],
):
    _client: ContainerdAPI
    _network: KernelNetwork

    def __init__(
        self,
        etcd: AgentEtcdClientView,
        local_config: AgentUnifiedConfig,
        **kwargs: Any,
    ) -> None:
        super().__init__(etcd, local_config, **kwargs)
        containerd_config = local_config.containerd
        self._network = KernelNetwork()
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
        await super().__ainit__()

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
        dirs = ScratchDirs.for_kernel(self.local_config.container.scratch_root, str(kernel_id))
        if container_id is not None:
            await self._collect_task_log(kernel_id, container_id, dirs)
            if not self.local_config.debug.skip_container_deletion:
                try:
                    await clean_container(self._client, str(container_id))
                except BackendAIError:
                    log.exception("container delete failed", container_id=container_id)
        try:
            await self._network.teardown(kernel_id)
        except BackendAIError:
            log.exception("kernel network teardown failed")
        if not restarting:
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
