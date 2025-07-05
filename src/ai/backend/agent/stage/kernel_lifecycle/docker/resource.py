import asyncio
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, override

from ai.backend.agent.affinity_map import AffinityMap, AffinityPolicy
from ai.backend.agent.exception import UnsupportedResource
from ai.backend.agent.resources import (
    ComputerContext,
    KernelResourceSpec,
    allocate,
    known_slot_types,
)
from ai.backend.common.stage.types import Provisioner, ProvisionStage, SpecGenerator
from ai.backend.common.types import (
    DeviceName,
    ResourceSlot,
    current_resource_slots,
)


@dataclass
class ResourceSpec:
    resource_slots: ResourceSlot
    resource_opts: Mapping[str, Any]

    computers: Mapping[DeviceName, ComputerContext]
    allocation_order: list[DeviceName]
    affinity_map: AffinityMap
    affinity_policy: AffinityPolicy
    allow_fractional_resource_fragmentation: bool


class ResourceSpecGenerator(SpecGenerator[ResourceSpec]):
    def __init__(
        self,
        resource_slots: Mapping[str, str],
        resource_opts: Mapping[str, Any],
        computers: Mapping[DeviceName, ComputerContext],
        allocation_order: list[DeviceName],
        affinity_map: AffinityMap,
        affinity_policy: AffinityPolicy,
        allow_fractional_resource_fragmentation: bool,
    ) -> None:
        """
        Initializes the resource spec generator with the kernel configuration.
        :param kernel_config: The configuration for the kernel.
        """
        self._resource_slots = resource_slots
        self._resource_opts = resource_opts
        self._computers = computers
        self._allocation_order = allocation_order
        self._affinity_map = affinity_map
        self._affinity_policy = affinity_policy
        self._allow_fractional_resource_fragmentation = allow_fractional_resource_fragmentation

    @override
    async def wait_for_spec(self) -> ResourceSpec:
        """
        Waits for the spec to be ready.
        """
        return ResourceSpec(
            resource_slots=ResourceSlot.from_json(self._resource_slots),
            resource_opts=self._resource_opts,
            computers=self._computers,
            allocation_order=self._allocation_order,
            affinity_map=self._affinity_map,
            affinity_policy=self._affinity_policy,
            allow_fractional_resource_fragmentation=self._allow_fractional_resource_fragmentation,
        )


@dataclass
class ResourceResult:
    resource_spec: KernelResourceSpec
    resource_opts: Mapping[str, Any]


class ResourceProvisioner(Provisioner[ResourceSpec, ResourceResult]):
    """
    Provisioner for the kernel creation setup stage.
    This is a no-op provisioner as it does not create any resources.
    """

    def __init__(self, resource_lock: asyncio.Lock):
        self._lock = resource_lock

    @property
    @override
    def name(self) -> str:
        return "docker-resource"

    @override
    async def setup(self, spec: ResourceSpec) -> ResourceResult:
        resource_spec, resource_opts = self._prepare_resource_spec(spec)
        await self._allocate(spec, resource_spec)
        return ResourceResult(
            resource_spec=resource_spec,
            resource_opts=resource_opts,
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

    @override
    async def teardown(self, resource: ResourceResult) -> None:
        # TODO: Implement resource release logic
        pass


class ResourceStage(ProvisionStage[ResourceSpec, ResourceResult]):
    pass
