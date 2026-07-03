"""Containerd agent backend (BEP-1055).

An independent agent backend parallel to DockerAgent, targeting containerd's native
gRPC/task model instead of the Docker daemon. This is a structural scaffold: the
container-facing operations (image scan/pull, task create/start, destroy) raise
``NotImplementedError`` pending the containerd gRPC client; the runtime-agnostic parts
(resource spec, registration, kernel context wiring) are real.

Cluster networking is provided by the BEP-1055 runtime-neutral stack
(``agent.network``): the SessionNetworkCoordinator handles per-session setup and the
ContainerNetworkProvisioner attaches each container's task PID via CNI.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal, override

from ai.backend.agent.agent import (
    AbstractAgent,
    AbstractKernelCreationContext,
    ScanImagesResult,
)
from ai.backend.agent.errors import UnsupportedResource
from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.kernel_registry.writer.types import KernelRegistrySaveMetadata
from ai.backend.agent.resources import (
    AbstractComputePlugin,
    ComputerContext,
    KernelResourceSpec,
    Mount,
    known_slot_types,
)
from ai.backend.agent.types import Container, KernelOwnershipData, MountInfo
from ai.backend.common.docker import ImageRef
from ai.backend.common.dto.agent.response import PurgeImagesResp
from ai.backend.common.dto.manager.rpc_request import PurgeImagesReq
from ai.backend.common.events.dispatcher import EventProducer
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
    SessionId,
    SlotName,
    current_resource_slots,
)

from .kernel import ContainerdKernel
from .session_network import (
    ContainerdSessionNetwork,
    build_containerd_session_network,
)

_TODO = "containerd backend: not yet implemented (requires containerd gRPC client)"


class ContainerdKernelCreationContext(AbstractKernelCreationContext[ContainerdKernel]):
    def __init__(
        self,
        ownership_data: KernelOwnershipData,
        event_producer: EventProducer,
        kernel_image: ImageRef,
        kernel_config: KernelCreationConfig,
        distro: str,
        local_config: Any,
        computers: Mapping[DeviceName, ComputerContext],
        restarting: bool = False,
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

    @override
    async def get_extra_envs(self) -> Mapping[str, str]:
        return {}

    @override
    async def prepare_resource_spec(
        self,
    ) -> tuple[KernelResourceSpec, Mapping[str, Any] | None]:
        slots = ResourceSlot.from_json(self.kernel_config["resource_slots"])
        if SlotName("cpu") not in slots:
            raise UnsupportedResource("cpu slot is required")
        if SlotName("mem") not in slots:
            raise UnsupportedResource("mem slot is required")
        for st, sv in slots.items():
            if st not in known_slot_types and sv != Decimal(0):
                raise UnsupportedResource(st)
        current_resource_slots.set(known_slot_types)
        slots = slots.normalize_slots(ignore_unknown=True)
        resource_spec = KernelResourceSpec(
            allocations={},
            slots=slots.copy(),
            mounts=[],
            scratch_disk_size=0,
        )
        resource_opts = self.kernel_config.get("resource_opts", {})
        return resource_spec, resource_opts

    @override
    async def prepare_scratch(self) -> None:
        raise NotImplementedError(_TODO)

    @override
    async def get_intrinsic_mounts(self) -> Sequence[Mount]:
        return []

    @property
    @override
    def repl_ports(self) -> Sequence[int]:
        return (2000, 2001)

    @property
    @override
    def protected_services(self) -> Sequence[str]:
        return ()

    @override
    async def apply_network(self, cluster_info: ClusterInfo) -> None:
        # BEP-1055: per-session network setup is driven by SessionNetworkCoordinator
        # and per-container attach by ContainerNetworkProvisioner (against the task PID),
        # not here. Left as a no-op for single-node sessions.
        return

    @override
    async def prepare_ssh(self, cluster_info: ClusterInfo) -> None:
        raise NotImplementedError(_TODO)

    @override
    async def process_mounts(self, mounts: Sequence[Mount]) -> None:
        raise NotImplementedError(_TODO)

    @override
    async def apply_accelerator_allocation(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> None:
        raise NotImplementedError(_TODO)

    @override
    async def generate_accelerator_mounts(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> list[MountInfo]:
        return []

    @override
    def resolve_krunner_filepath(self, filename: str) -> Path:
        raise NotImplementedError(_TODO)

    @override
    def get_runner_mount(
        self,
        type: MountTypes,
        src: str | Path,
        target: str | Path,
        perm: MountPermission = MountPermission.READ_ONLY,
        opts: Mapping[str, Any] | None = None,
    ) -> Mount:
        raise NotImplementedError(_TODO)

    @override
    async def prepare_container(
        self,
        resource_spec: KernelResourceSpec,
        environ: Mapping[str, str],
        service_ports: list[ServicePort],
        cluster_info: ClusterInfo,
    ) -> ContainerdKernel:
        raise NotImplementedError(_TODO)

    @override
    async def start_container(
        self,
        kernel_obj: AbstractKernel,
        cmdargs: list[str],
        resource_opts: Mapping[str, Any] | None,
        preopen_ports: Sequence[int],
        cluster_info: ClusterInfo,
    ) -> Mapping[str, Any]:
        raise NotImplementedError(_TODO)

    @override
    async def mount_krunner(
        self,
        resource_spec: KernelResourceSpec,
        environ: Any,
    ) -> None:
        raise NotImplementedError(_TODO)


class ContainerdAgent(
    AbstractAgent[ContainerdKernel, ContainerdKernelCreationContext],
):
    _session_network: ContainerdSessionNetwork

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Cluster networking is delegated to the BEP-1055 agent.network stack via a
        # (verified) facade; the kernel-creation lifecycle will drive it. The uplink /
        # cni_path defaults should later be sourced from a containerd network config.
        container_cfg = self.local_config.container
        host_ip = str(container_cfg.advertised_host or container_cfg.bind_host)
        self._session_network = build_containerd_session_network(
            self.etcd,
            agent_id=str(self.id),
            host_ip=host_ip,
        )

    @override
    async def execute(
        self,
        session_id: SessionId,
        kernel_id: KernelId,
        run_id: str | None,
        mode: Literal["query", "batch", "input", "continue"],
        text: str,
        *,
        opts: Mapping[str, Any],
        api_version: int,
        flush_timeout: float,
    ) -> dict[str, Any]:
        raise NotImplementedError(_TODO)

    @override
    async def _load_kernel_registry_from_recovery(self) -> dict[KernelId, AbstractKernel]:
        return {}

    @override
    async def _write_kernel_registry_to_recovery(
        self,
        kernel_registry: Mapping[KernelId, AbstractKernel],
        metadata: KernelRegistrySaveMetadata,
    ) -> None:
        pass

    @override
    def get_public_service_ports(self, service_ports: list[ServicePort]) -> list[ServicePort]:
        return []

    @override
    async def sync_container_lifecycles(self) -> None:
        return

    @override
    async def enumerate_containers(
        self,
        status_filter: frozenset[ContainerStatus] = frozenset(),
    ) -> Sequence[tuple[KernelId, Container]]:
        raise NotImplementedError(_TODO)

    @override
    async def resolve_image_distro(self, image: ImageConfig) -> str:
        raise NotImplementedError(_TODO)

    @override
    def get_cgroup_path(self, controller: str, container_id: str) -> Path:
        # containerd uses the systemd/cgroupfs hierarchy; TODO: resolve the task's slice.
        raise NotImplementedError(_TODO)

    @override
    def get_cgroup_version(self) -> str:
        return "2"

    @override
    async def extract_image_command(self, image: str) -> list[str] | None:
        raise NotImplementedError(_TODO)

    @override
    async def scan_images(self) -> ScanImagesResult:
        raise NotImplementedError(_TODO)

    @override
    async def pull_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout_seconds: float | None,
    ) -> None:
        raise NotImplementedError(_TODO)

    @override
    async def push_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout_seconds: float | None | Sentinel = Sentinel.TOKEN,
    ) -> None:
        raise NotImplementedError(_TODO)

    @override
    async def purge_images(self, request: PurgeImagesReq) -> PurgeImagesResp:
        raise NotImplementedError(_TODO)

    @override
    async def check_image(
        self, image_ref: ImageRef, image_id: str, auto_pull: AutoPullBehavior
    ) -> bool:
        raise NotImplementedError(_TODO)

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
        )

    @override
    async def destroy_kernel(
        self,
        kernel_id: KernelId,
        container_id: ContainerId | None,
    ) -> None:
        raise NotImplementedError(_TODO)

    @override
    async def clean_kernel(
        self,
        kernel_id: KernelId,
        container_id: ContainerId | None,
        restarting: bool,
    ) -> None:
        raise NotImplementedError(_TODO)

    @override
    async def create_local_network(self, network_name: str) -> None:
        raise NotImplementedError(_TODO)

    @override
    async def destroy_local_network(self, network_name: str) -> None:
        raise NotImplementedError(_TODO)

    @override
    async def restart_kernel__load_config(
        self,
        kernel_id: KernelId,
        name: str,
    ) -> bytes:
        raise NotImplementedError(_TODO)

    @override
    async def restart_kernel__store_config(
        self,
        kernel_id: KernelId,
        name: str,
        data: bytes,
    ) -> None:
        raise NotImplementedError(_TODO)
