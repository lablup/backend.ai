import asyncio
import random
from decimal import Decimal
from pathlib import Path
from typing import Any, FrozenSet, Literal, Mapping, MutableMapping, Optional, Sequence, Tuple

from ai.backend.common.docker import ImageRef
from ai.backend.common.types import (
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
    SessionId,
    SlotName,
    current_resource_slots,
)

from ..agent import ACTIVE_STATUS_SET, AbstractAgent, AbstractKernelCreationContext
from ..exception import UnsupportedResource
from ..kernel import AbstractKernel
from ..resources import AbstractComputePlugin, KernelResourceSpec, Mount, known_slot_types
from ..types import Container, ContainerStatus, MountInfo
from .kernel import DummyKernel
from .resources import detect_resources


class DummyKernelCreationContext(AbstractKernelCreationContext[DummyKernel]):
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
        await asyncio.sleep(2)

    async def get_intrinsic_mounts(self) -> Sequence[Mount]:
        return []

    async def apply_network(self, cluster_info: ClusterInfo) -> None:
        return

    async def prepare_ssh(self, cluster_info: ClusterInfo) -> None:
        await asyncio.sleep(0.1)

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
        await asyncio.sleep(0.1)
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
        await asyncio.sleep(5)
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
        await asyncio.sleep(1)


class DummyAgent(
    AbstractAgent[DummyKernel, DummyKernelCreationContext],
):
    async def enumerate_containers(
        self,
        status_filter: FrozenSet[ContainerStatus] = ACTIVE_STATUS_SET,
    ) -> Sequence[Tuple[KernelId, Container]]:
        return []

    async def detect_resources(
        self,
    ) -> Tuple[Mapping[DeviceName, AbstractComputePlugin], Mapping[SlotName, Decimal]]:
        return await detect_resources(self.etcd, self.local_config)

    async def scan_images(self) -> Mapping[str, str]:
        await asyncio.sleep(0.1)
        return {}

    async def pull_image(self, image_ref: ImageRef, registry_conf: ImageRegistry) -> None:
        await asyncio.sleep(random.uniform(0.5, 10))

    async def check_image(
        self, image_ref: ImageRef, image_id: str, auto_pull: AutoPullBehavior
    ) -> bool:
        return True

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
            kernel_config,
            self.local_config,
            self.computers,
            restarting=restarting,
        )

    async def destroy_kernel(
        self,
        kernel_id: KernelId,
        container_id: Optional[ContainerId],
    ) -> None:
        await asyncio.sleep(random.uniform(0.2, 5))

    async def clean_kernel(
        self,
        kernel_id: KernelId,
        container_id: Optional[ContainerId],
        restarting: bool,
    ) -> None:
        await asyncio.sleep(random.uniform(0.5, 100))

    async def create_local_network(self, network_name: str) -> None:
        await asyncio.sleep(2)

    async def destroy_local_network(self, network_name: str) -> None:
        await asyncio.sleep(2)

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
