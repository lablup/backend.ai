from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any, override

from aiodocker.docker import Docker

from ai.backend.agent.docker import intrinsic as docker_intrinsic
from ai.backend.agent.resources import AbstractAllocMap
from ai.backend.agent.stats import (
    ContainerMeasurement,
    NodeMeasurement,
    ProcessMeasurement,
    StatContext,
)
from ai.backend.agent.types import Container
from ai.backend.common.types import DeviceId, SlotName


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

    # FIXME(containerd-mvp): CPU limits are not applied to containerd kernels
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
        return None


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

    # FIXME(containerd-mvp): memory limits are not applied to containerd kernels
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
        return None
