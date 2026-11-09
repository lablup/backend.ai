import logging
from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from typing import Any, Final, override

from aiodocker.docker import Docker

from ai.backend.agent.alloc_map import AbstractAllocMap, DiscretePropertyAllocMap
from ai.backend.agent.docker import intrinsic as docker_intrinsic
from ai.backend.agent.errors import InvalidArgumentError
from ai.backend.agent.stats import (
    ContainerMeasurement,
    NodeMeasurement,
    ProcessMeasurement,
    StatContext,
)
from ai.backend.agent.types import Container
from ai.backend.common.types import DeviceId, SlotName
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

# Container labels recording the kernel's allocations, read back by restore_from_container.
CPUSET_LABEL: Final = "ai.backend.containerd.cpuset"
MEMORY_LABEL: Final = "ai.backend.containerd.memory-bytes"


def _discrete_map(alloc_map: AbstractAllocMap) -> DiscretePropertyAllocMap:
    if not isinstance(alloc_map, DiscretePropertyAllocMap):
        raise InvalidArgumentError(
            f"Expected DiscretePropertyAllocMap, got {type(alloc_map).__name__}"
        )
    return alloc_map


class CPUPlugin(docker_intrinsic.CPUPlugin):
    """
    Represents the CPU, reusing the Docker plugin's device discovery and alloc map
    without its Docker client, statistics and container limits.
    """

    @override
    async def init(self, context: Any | None = None) -> None:
        pass

    @override
    async def cleanup(self) -> None:
        pass

    # FIXME(containerd-mvp): no CPU statistics are collected for the node, containers or
    # processes
    @override
    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        return []

    @override
    async def gather_container_measures(
        self,
        ctx: StatContext,
        container_ids: Sequence[str],
    ) -> Sequence[ContainerMeasurement]:
        return []

    @override
    async def gather_process_measures(
        self, ctx: StatContext, pid_map: Mapping[int, str]
    ) -> Sequence[ProcessMeasurement]:
        return []

    @override
    async def generate_docker_args(
        self,
        docker: Docker,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Mapping[str, Any]:
        return {}

    @override
    async def restore_from_container(
        self,
        container: Container,
        alloc_map: AbstractAllocMap,
    ) -> None:
        discrete = _discrete_map(alloc_map)
        cpuset = container.labels.get(CPUSET_LABEL)
        if not cpuset:
            return
        try:
            cores = [str(int(core)) for core in cpuset.split(",")]
        except ValueError:
            log.warning("malformed cpuset label skipped", container_id=container.id, value=cpuset)
            return
        unknown = [core for core in cores if DeviceId(core) not in discrete.device_slots]
        if unknown:
            log.warning(
                "cpuset label has unknown cores",
                container_id=container.id,
                cores=",".join(unknown),
            )
            cores = [core for core in cores if core not in unknown]
        discrete.apply_allocation({
            SlotName("cpu"): {DeviceId(core): Decimal(1) for core in cores},
        })


class MemoryPlugin(docker_intrinsic.MemoryPlugin):
    """
    Represents the main memory, reusing the Docker plugin's device discovery and alloc map
    without its Docker client, statistics and container limits.
    """

    @override
    async def init(self, context: Any | None = None) -> None:
        pass

    @override
    async def cleanup(self) -> None:
        pass

    # FIXME(containerd-mvp): no memory statistics are collected for the node, containers or
    # processes
    @override
    async def gather_node_measures(self, ctx: StatContext) -> Sequence[NodeMeasurement]:
        return []

    @override
    async def gather_container_measures(
        self,
        ctx: StatContext,
        container_ids: Sequence[str],
    ) -> Sequence[ContainerMeasurement]:
        return []

    @override
    async def gather_process_measures(
        self, ctx: StatContext, pid_map: Mapping[int, str]
    ) -> Sequence[ProcessMeasurement]:
        return []

    @override
    async def generate_docker_args(
        self,
        docker: Docker,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> Mapping[str, Any]:
        return {}

    @override
    async def restore_from_container(
        self,
        container: Container,
        alloc_map: AbstractAllocMap,
    ) -> None:
        discrete = _discrete_map(alloc_map)
        memory = container.labels.get(MEMORY_LABEL)
        if not memory:
            return
        try:
            amount = Decimal(memory)
        except InvalidOperation:
            log.warning("malformed memory label skipped", container_id=container.id, value=memory)
            return
        if not amount.is_finite() or amount < 0:
            log.warning("malformed memory label skipped", container_id=container.id, value=memory)
            return
        discrete.apply_allocation({SlotName("mem"): {DeviceId("root"): amount}})
