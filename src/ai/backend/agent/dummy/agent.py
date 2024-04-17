from __future__ import annotations

import asyncio
from decimal import Decimal
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    FrozenSet,
    Literal,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
    cast,
)

from ai.backend.common.docker import ImageRef
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events import EventProducer
from ai.backend.common.types import (
    AgentId,
    AutoPullBehavior,
    ClusterInfo,
    ClusterSSHPortMapping,
    ContainerId,
    DeviceId,
    DeviceName,
    ImageRegistry,
    KernelCreationConfig,
    KernelId,
    MountTypes,
    ResourceSlot,
    ServicePort,
    SessionId,
    SlotName,
    current_resource_slots,
)

from ..agent import ACTIVE_STATUS_SET, AbstractAgent, AbstractKernelCreationContext, ComputerContext
from ..exception import UnsupportedResource
from ..kernel import AbstractKernel
from ..resources import AbstractComputePlugin, KernelResourceSpec, Mount, known_slot_types
from ..types import Container, ContainerStatus, MountInfo
from .config import Agent as DummyAgentLocalConfig
from .config import KernelCreationCtxDelay as KernCreationCtxDelay
from .config import LocalConfig as DummyLocalConfig
from .kernel import DummyKernel
from .resources import load_resources, scan_available_resources

if TYPE_CHECKING:
    from ai.backend.common.auth import PublicKey
    from ai.backend.common.plugin.monitor import ErrorPluginContext, StatsPluginContext


class DummyKernelCreationContext(AbstractKernelCreationContext[DummyKernel]):
    dummy_config: DummyLocalConfig

    def __init__(
        self,
        kernel_id: KernelId,
        session_id: SessionId,
        agent_id: AgentId,
        event_producer: EventProducer,
        kernel_config: KernelCreationConfig,
        local_config: Mapping[str, Any],
        computers: MutableMapping[DeviceName, ComputerContext],
        restarting: bool = False,
        *,
        dummy_config: DummyLocalConfig,
    ) -> None:
        super().__init__(
            kernel_id,
            session_id,
            agent_id,
            event_producer,
            kernel_config,
            local_config,
            computers,
            restarting=restarting,
        )
        self.dummy_config = dummy_config
        self.creation_ctx_delay = cast(KernCreationCtxDelay, self.dummy_config.kernel_creation_ctx)

    async def get_extra_envs(self) -> Mapping[str, str]:
        return {}

    async def prepare_resource_spec(
        self,
    ) -> Tuple[KernelResourceSpec, Optional[Mapping[str, Any]]]:
        slots = ResourceSlot.from_json(self.kernel_config["resource_slots"])
        # Ensure that we have intrinsic slots.
        assert SlotName("cpu") in slots
        assert SlotName("mem") in slots
        # accept unknown slot type with zero values
        # but reject if they have non-zero values.
        for st, sv in slots.items():
            if st not in known_slot_types and sv != Decimal(0):
                raise UnsupportedResource(st)
        # sanitize the slots
        current_resource_slots.set(known_slot_types)
        slots = slots.normalize_slots(ignore_unknown=True)
        resource_spec = KernelResourceSpec(
            container_id="",
            allocations={},
            slots={**slots},  # copy
            mounts=[],
            scratch_disk_size=0,  # TODO: implement (#70)
        )
        resource_opts = self.kernel_config.get("resource_opts", {})
        return resource_spec, resource_opts

    async def prepare_scratch(self) -> None:
        delay = self.creation_ctx_delay.prepare_scratch
        await asyncio.sleep(delay)

    async def get_intrinsic_mounts(self) -> Sequence[Mount]:
        return []

    async def apply_network(self, cluster_info: ClusterInfo) -> None:
        return

    async def prepare_ssh(self, cluster_info: ClusterInfo) -> None:
        delay = self.creation_ctx_delay.prepare_ssh
        await asyncio.sleep(delay)

    async def process_mounts(self, mounts: Sequence[Mount]):
        return

    async def apply_accelerator_allocation(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> None:
        return

    async def generate_accelerator_mounts(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> list[MountInfo]:
        return []

    def resolve_krunner_filepath(self, filename) -> Path:
        return Path()

    def get_runner_mount(
        self,
        type: MountTypes,
        src: str | Path,
        target: str | Path,
        perm: Literal["ro", "rw"] = "ro",
        opts: Mapping[str, Any] = None,
    ):
        return Mount(MountTypes.BIND, Path(), Path())

    async def spawn(
        self,
        resource_spec: KernelResourceSpec,
        environ: Mapping[str, str],
        service_ports,
    ) -> DummyKernel:
        delay = self.creation_ctx_delay.spawn
        await asyncio.sleep(delay)
        return DummyKernel(
            self.kernel_id,
            self.session_id,
            self.agent_id,
            self.image_ref,
            self.kspec_version,
            agent_config=self.local_config,
            service_ports=service_ports,
            resource_spec=resource_spec,
            environ=environ,
            data={},
            dummy_config=self.dummy_config,
        )

    async def start_container(
        self,
        kernel_obj: AbstractKernel,
        cmdargs: list[str],
        resource_opts,
        preopen_ports,
    ) -> Mapping[str, Any]:
        container_bind_host = self.local_config["container"]["bind-host"]
        advertised_kernel_host = self.local_config["container"].get("advertised-host")
        delay = self.creation_ctx_delay.start_container
        await asyncio.sleep(delay)
        return {
            "container_id": "",
            "kernel_host": advertised_kernel_host or container_bind_host,
            "repl_in_port": 2000,
            "repl_out_port": 2001,
            "stdin_port": 2002,  # legacy
            "stdout_port": 2003,  # legacy
            "host_ports": [2000, 2001, 2002, 2003],
            "domain_socket_proxies": [],
            "block_service_ports": self.internal_data.get("block_service_ports", False),
        }

    async def mount_krunner(
        self,
        resource_spec: KernelResourceSpec,
        environ: MutableMapping[str, str],
    ) -> None:
        delay = self.creation_ctx_delay.mount_krunner
        await asyncio.sleep(delay)


class DummyAgent(
    AbstractAgent[DummyKernel, DummyKernelCreationContext],
):
    dummy_config: DummyLocalConfig
    dummy_agent_cfg: DummyAgentLocalConfig

    def __init__(
        self,
        etcd: AsyncEtcd,
        local_config: Mapping[str, Any],
        *,
        stats_monitor: StatsPluginContext,
        error_monitor: ErrorPluginContext,
        skip_initial_scan: bool = False,
        agent_public_key: Optional[PublicKey],
    ) -> None:
        super().__init__(
            etcd,
            local_config,
            stats_monitor=stats_monitor,
            error_monitor=error_monitor,
            skip_initial_scan=skip_initial_scan,
            agent_public_key=agent_public_key,
        )
        self.dummy_config = cast(DummyLocalConfig, local_config["dummy"])
        self.dummy_agent_cfg = cast(DummyAgentLocalConfig, self.dummy_config.agent)

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
    ):
        return {"status": "not-implemented"}

    def get_public_service_ports(self, service_ports: list[ServicePort]) -> list[ServicePort]:
        return []

    async def sync_container_lifecycles(self, interval: float) -> None:
        return

    async def enumerate_containers(
        self,
        status_filter: FrozenSet[ContainerStatus] = ACTIVE_STATUS_SET,
    ) -> Sequence[Tuple[KernelId, Container]]:
        return []

    async def load_resources(self) -> Mapping[DeviceName, AbstractComputePlugin]:
        return await load_resources(self.etcd, self.local_config)

    async def scan_available_resources(self) -> Mapping[SlotName, Decimal]:
        return await scan_available_resources(
            self.local_config, {name: cctx.instance for name, cctx in self.computers.items()}
        )

    async def scan_images(self) -> Mapping[str, str]:
        existing_imgs: dict[str, str] = self.dummy_agent_cfg.image.already_have
        delay = self.dummy_agent_cfg.delay.scan_image
        await asyncio.sleep(delay)
        return existing_imgs

    async def push_image(self, image_ref: ImageRef, registry_conf: ImageRegistry) -> None:
        delay = self.dummy_agent_cfg.delay.push_image
        await asyncio.sleep(delay)

    async def pull_image(self, image_ref: ImageRef, registry_conf: ImageRegistry) -> None:
        delay = self.dummy_agent_cfg.delay.pull_image
        await asyncio.sleep(delay)

    async def check_image(
        self, image_ref: ImageRef, image_id: str, auto_pull: AutoPullBehavior
    ) -> bool:
        if (
            existing_imgs := self.dummy_agent_cfg.image.already_have
        ) is not None and image_ref.canonical in existing_imgs:
            return True
        return False

    async def init_kernel_context(
        self,
        kernel_id: KernelId,
        session_id: SessionId,
        kernel_config: KernelCreationConfig,
        *,
        restarting: bool = False,
        cluster_ssh_port_mapping: Optional[ClusterSSHPortMapping] = None,
    ) -> DummyKernelCreationContext:
        return DummyKernelCreationContext(
            kernel_id,
            session_id,
            self.id,
            self.event_producer,
            kernel_config,
            self.local_config,
            self.computers,
            restarting=restarting,
            dummy_config=self.dummy_config,
        )

    async def destroy_kernel(
        self,
        kernel_id: KernelId,
        container_id: Optional[ContainerId],
    ) -> None:
        delay = self.dummy_agent_cfg.delay.destroy_kernel
        await asyncio.sleep(delay)

    async def clean_kernel(
        self,
        kernel_id: KernelId,
        container_id: Optional[ContainerId],
        restarting: bool,
    ) -> None:
        delay = self.dummy_agent_cfg.delay.clean_kernel
        await asyncio.sleep(delay)

    async def create_local_network(self, network_name: str) -> None:
        delay = self.dummy_agent_cfg.delay.create_network
        await asyncio.sleep(delay)

    async def destroy_local_network(self, network_name: str) -> None:
        delay = self.dummy_agent_cfg.delay.destroy_network
        await asyncio.sleep(delay)

    async def restart_kernel__load_config(
        self,
        kernel_id: KernelId,
        name: str,
    ) -> bytes:
        await asyncio.sleep(0.1)
        return b""

    async def restart_kernel__store_config(
        self,
        kernel_id: KernelId,
        name: str,
        data: bytes,
    ) -> None:
        await asyncio.sleep(0.1)
