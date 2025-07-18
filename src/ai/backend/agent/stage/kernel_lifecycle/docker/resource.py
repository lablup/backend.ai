import asyncio
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, override

from aiodocker.docker import Docker

from ai.backend.agent.affinity_map import AffinityMap, AffinityPolicy
from ai.backend.agent.exception import UnsupportedResource
from ai.backend.agent.resources import (
    ComputerContext,
    KernelResourceSpec,
    Mount,
    allocate,
    known_slot_types,
)
from ai.backend.agent.types import MountInfo
from ai.backend.agent.utils import update_nested_dict
from ai.backend.common.asyncio import closing_async
from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)
from ai.backend.common.types import (
    DeviceName,
    MountPermission,
    ResourceSlot,
    current_resource_slots,
)


@dataclass
class ResourceSpec:
    """
    Specification for resource allocation stage.

    This includes the requested resource slots and all necessary context
    for allocating compute resources including accelerators.
    """

    resource_slots: ResourceSlot
    resource_opts: Mapping[str, Any]

    computers: Mapping[DeviceName, ComputerContext]
    allocation_order: list[DeviceName]
    affinity_map: AffinityMap
    affinity_policy: AffinityPolicy
    allow_fractional_resource_fragmentation: bool

    config_dir: Path


class ResourceSpecGenerator(ArgsSpecGenerator[ResourceSpec]):
    pass


@dataclass
class ResourceResult:
    resource_spec: KernelResourceSpec
    resource_opts: Mapping[str, Any]
    accelerator_mounts: list[Mount]
    container_arg: dict[str, Any]


class ResourceProvisioner(Provisioner[ResourceSpec, ResourceResult]):
    """
    Provisioner for the kernel creation setup stage.
    This provisioner handles resource allocation including accelerators (GPU, TPU, etc.).
    """

    def __init__(
        self,
        resource_lock: asyncio.Lock,
    ) -> None:
        self._lock = resource_lock

    @property
    @override
    def name(self) -> str:
        return "docker-resource"

    @override
    async def setup(self, spec: ResourceSpec) -> ResourceResult:
        resource_spec, resource_opts = self._prepare_resource_spec(spec)
        await self._allocate(spec, resource_spec)

        # Generate accelerator mounts for all allocated devices
        accelerator_mounts = await self._prepare_accelerator_mounts(spec, resource_spec)

        # Apply accelerator-specific configurations and collect environment variables
        container_arg = await self._prepare_accelerator_configs(spec, resource_spec)

        return ResourceResult(
            resource_spec=resource_spec,
            resource_opts=resource_opts,
            accelerator_mounts=accelerator_mounts,
            container_arg=container_arg,
        )

    def _prepare_resource_spec(
        self, spec: ResourceSpec
    ) -> tuple[KernelResourceSpec, Mapping[str, Any]]:
        slots = spec.resource_slots
        # Ensure that we have intrinsic slots.
        # But why do we need assertions here?
        # assert SlotName("cpu") in slots
        # assert SlotName("mem") in slots

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
            slots={**slots},  # copy
            mounts=[],
            scratch_disk_size=0,  # TODO: implement (#70)
        )
        resource_opts = spec.resource_opts
        return resource_spec, resource_opts

    async def _allocate(self, spec: ResourceSpec, kernel_resource_spec: KernelResourceSpec) -> None:
        async with self._lock:
            allocate(
                spec.computers,
                kernel_resource_spec,
                spec.allocation_order,
                spec.affinity_map,
                spec.affinity_policy,
                allow_fractional_resource_fragmentation=spec.allow_fractional_resource_fragmentation,
            )

    async def _prepare_accelerator_mounts(
        self, spec: ResourceSpec, resource_spec: KernelResourceSpec
    ) -> list[Mount]:
        mounts: list[MountInfo] = []

        for dev_type, device_alloc in resource_spec.allocations.items():
            if dev_type not in spec.computers:
                continue

            computer_ctx = spec.computers[dev_type]
            computer = computer_ctx.instance

            # Create directory for accelerator-specific files
            src_path = spec.config_dir / str(computer.key)
            src_path.mkdir(exist_ok=True)

            # Generate mounts for this accelerator type
            accelerator_mounts = await computer.generate_mounts(src_path, device_alloc)
            mounts.extend(accelerator_mounts)

        return [
            Mount(
                m.mode,
                m.src_path,
                Path(m.dst_path.as_posix()),
                MountPermission.READ_WRITE,  # Accelerators typically need read-write access
            )
            for m in mounts
        ]

    async def _prepare_accelerator_configs(
        self, spec: ResourceSpec, resource_spec: KernelResourceSpec
    ) -> dict[str, Any]:
        container_arg: dict[str, Any] = {}

        async with closing_async(Docker()) as docker:
            for dev_type, device_alloc in resource_spec.allocations.items():
                computer_ctx = spec.computers[dev_type]
                computer = computer_ctx.instance

                update_nested_dict(
                    container_arg,
                    await computer.generate_docker_args(docker, device_alloc),
                )

        return container_arg

    @override
    async def teardown(self, resource: ResourceResult) -> None:
        """
        Release allocated resources.
        """
        # TODO: Implement proper resource deallocation
        # This should deallocate resources from the computers' allocation maps
        pass


class ResourceStage(ProvisionStage[ResourceSpec, ResourceResult]):
    """
    Stage for resource allocation in the kernel lifecycle.

    This stage handles:
    1. Allocation of compute resources (CPU, memory, etc.)
    2. Allocation of accelerator resources (GPU, TPU, etc.)
    3. Generation of accelerator-specific mounts
    4. Application of accelerator-specific configurations

    The accelerator_mounts generated by this stage should be used by
    KernelRunnerMountStage to properly mount accelerator files/directories.

    Example usage:
        # In the kernel creation pipeline
        resource_provisioner = ResourceProvisioner(resource_lock, computers, agent)
        resource_stage = ResourceStage(resource_provisioner)

        # After stage execution
        result = await resource_stage.wait_for_resource()
        # result.accelerator_mounts contains all accelerator-specific mounts
    """

    pass
