from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from ai.backend.agent.alloc_map import DeviceSlotInfo, DiscretePropertyAllocMap
from ai.backend.agent.containerd.intrinsic import (
    CPUSET_LABEL,
    MEMORY_LABEL,
    CPUPlugin,
    MemoryPlugin,
)
from ai.backend.agent.errors import InvalidArgumentError
from ai.backend.agent.types import Container
from ai.backend.common.types import (
    ContainerId,
    ContainerStatus,
    DeviceId,
    SlotName,
    SlotTypes,
)


class TestDockerArgs:
    @pytest.mark.parametrize("plugin_cls", [CPUPlugin, MemoryPlugin])
    async def test_intrinsic_plugins_emit_no_docker_args(
        self, plugin_cls: type[CPUPlugin | MemoryPlugin]
    ) -> None:
        plugin = plugin_cls({}, {})

        assert await plugin.generate_docker_args(MagicMock(), {}) == {}


def _container(labels: dict[str, str]) -> Container:
    return Container(
        id=ContainerId("c1"),
        status=ContainerStatus.RUNNING,
        image="img:1",
        labels=labels,
        ports=[],
        backend_obj=None,
    )


def _map(slot: str, devices: dict[str, str]) -> DiscretePropertyAllocMap:
    return DiscretePropertyAllocMap(
        device_slots={
            DeviceId(d): DeviceSlotInfo(SlotTypes.COUNT, SlotName(slot), Decimal(cap))
            for d, cap in devices.items()
        }
    )


class TestRestoreFromContainer:
    async def test_cpu_cores_are_taken_from_the_label(self) -> None:
        alloc_map = _map("cpu", {"0": "1", "1": "1", "2": "1"})

        await CPUPlugin({}, {}).restore_from_container(_container({CPUSET_LABEL: "0,2"}), alloc_map)

        used = alloc_map.allocations[SlotName("cpu")]
        assert used[DeviceId("0")] == 1
        assert used[DeviceId("1")] == 0
        assert used[DeviceId("2")] == 1

    async def test_memory_is_taken_from_the_label(self) -> None:
        alloc_map = _map("mem", {"root": "4096"})

        await MemoryPlugin({}, {}).restore_from_container(
            _container({MEMORY_LABEL: "1024"}), alloc_map
        )

        assert alloc_map.allocations[SlotName("mem")][DeviceId("root")] == 1024

    @pytest.mark.parametrize("plugin_cls", [CPUPlugin, MemoryPlugin])
    async def test_container_without_labels_restores_nothing(
        self, plugin_cls: type[CPUPlugin | MemoryPlugin]
    ) -> None:
        alloc_map = _map("cpu" if plugin_cls is CPUPlugin else "mem", {"0": "1"})

        await plugin_cls({}, {}).restore_from_container(_container({}), alloc_map)

        assert all(
            amount == 0
            for per_device in alloc_map.allocations.values()
            for amount in per_device.values()
        )

    @pytest.mark.parametrize(
        ("plugin_cls", "labels"),
        [
            (CPUPlugin, {CPUSET_LABEL: "0,x"}),
            (MemoryPlugin, {MEMORY_LABEL: "lots"}),
            (MemoryPlugin, {MEMORY_LABEL: "-1"}),
            (MemoryPlugin, {MEMORY_LABEL: "NaN"}),
        ],
    )
    async def test_malformed_label_restores_nothing(
        self, plugin_cls: type[CPUPlugin | MemoryPlugin], labels: dict[str, str]
    ) -> None:
        alloc_map = _map("cpu" if plugin_cls is CPUPlugin else "mem", {"0": "1"})

        await plugin_cls({}, {}).restore_from_container(_container(labels), alloc_map)

        assert all(
            amount == 0
            for per_device in alloc_map.allocations.values()
            for amount in per_device.values()
        )

    async def test_cores_outside_the_device_map_are_skipped(self) -> None:
        alloc_map = _map("cpu", {"0": "1", "2": "1"})

        await CPUPlugin({}, {}).restore_from_container(
            _container({CPUSET_LABEL: "0,99,-1"}), alloc_map
        )

        assert alloc_map.allocations[SlotName("cpu")] == {
            DeviceId("0"): Decimal(1),
            DeviceId("2"): Decimal(0),
        }

    @pytest.mark.parametrize("plugin_cls", [CPUPlugin, MemoryPlugin])
    async def test_other_alloc_map_is_rejected(
        self, plugin_cls: type[CPUPlugin | MemoryPlugin]
    ) -> None:
        with pytest.raises(InvalidArgumentError):
            await plugin_cls({}, {}).restore_from_container(_container({}), MagicMock())
