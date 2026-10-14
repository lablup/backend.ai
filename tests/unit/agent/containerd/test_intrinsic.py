from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ai.backend.agent.alloc_map import DiscretePropertyAllocMap
from ai.backend.agent.containerd.client import ContainerRecord
from ai.backend.agent.containerd.intrinsic import CPUPlugin, MemoryPlugin
from ai.backend.agent.containerd.scratch import CONFIG_DIR_LABEL
from ai.backend.agent.resources import DeviceSlotInfo, KernelResourceSpec
from ai.backend.agent.types import Container
from ai.backend.common.types import (
    ContainerId,
    ContainerStatus,
    DeviceId,
    DeviceName,
    ResourceSlot,
    SlotName,
    SlotTypes,
)

CPU = SlotName("cpu")
MEM = SlotName("mem")
GIB = 1 << 30


def _alloc_map() -> DiscretePropertyAllocMap:
    return DiscretePropertyAllocMap(
        device_slots={
            **{
                DeviceId(str(i)): DeviceSlotInfo(SlotTypes.COUNT, CPU, Decimal(1)) for i in range(4)
            },
            DeviceId("root"): DeviceSlotInfo(SlotTypes.BYTES, MEM, Decimal(8 * GIB)),
        },
    )


def _kernel(tmp_path: Path, name: str, cores: list[str], mem_bytes: int) -> Container:
    """A running container whose config dir holds the resource.txt the agent wrote."""
    config = tmp_path / name / "config"
    config.mkdir(parents=True)
    spec = KernelResourceSpec(
        allocations={
            DeviceName("cpu"): {CPU: {DeviceId(c): Decimal(1) for c in cores}},
            DeviceName("mem"): {MEM: {DeviceId("root"): Decimal(mem_bytes)}},
        },
        slots=ResourceSlot({CPU: Decimal(len(cores)), MEM: Decimal(mem_bytes)}),
        mounts=[],
        scratch_disk_size=0,
    )
    (config / "resource.txt").write_text(spec.write_to_string())
    record = ContainerRecord(
        id=name,
        image="img:1",
        snapshotter="overlayfs",
        snapshot_key=name,
        labels={CONFIG_DIR_LABEL: str(config)},
    )
    return Container(
        id=ContainerId(name),
        status=ContainerStatus.RUNNING,
        image="img:1",
        labels=record.labels,
        ports=[],
        backend_obj=record,
    )


class TestDockerArgs:
    @pytest.mark.parametrize("plugin_cls", [CPUPlugin, MemoryPlugin])
    async def test_intrinsic_plugins_emit_no_docker_args(
        self, plugin_cls: type[CPUPlugin | MemoryPlugin]
    ) -> None:
        plugin = plugin_cls({}, {})

        assert await plugin.generate_docker_args(MagicMock(), {}) == {}


class TestRestoreFromContainer:
    async def test_cpu_cores_of_a_running_kernel_stay_allocated(self, tmp_path: Path) -> None:
        alloc_map = _alloc_map()
        survivor = _kernel(tmp_path, "k2", ["2", "3"], GIB)

        await CPUPlugin({}, {}).restore_from_container(survivor, alloc_map)

        assert alloc_map.allocations[CPU][DeviceId("2")] == 1
        assert alloc_map.allocations[CPU][DeviceId("3")] == 1
        assert alloc_map.allocations[CPU][DeviceId("0")] == 0

    async def test_memory_is_restored_from_the_recorded_allocation(self, tmp_path: Path) -> None:
        alloc_map = _alloc_map()
        survivor = _kernel(tmp_path, "k2", ["2"], 2 * GIB)

        await MemoryPlugin({}, {}).restore_from_container(survivor, alloc_map)

        assert alloc_map.allocations[MEM][DeviceId("root")] == 2 * GIB

    async def test_rebuild_after_one_of_two_kernels_ended_keeps_the_other(
        self, tmp_path: Path
    ) -> None:
        alloc_map = _alloc_map()
        first = _kernel(tmp_path, "k1", ["0", "1"], GIB)
        second = _kernel(tmp_path, "k2", ["2", "3"], 2 * GIB)
        for kernel in (first, second):
            await CPUPlugin({}, {}).restore_from_container(kernel, alloc_map)
            await MemoryPlugin({}, {}).restore_from_container(kernel, alloc_map)

        # What reconstruct_resource_usage does once k1 is gone: clear, then restore the rest.
        alloc_map.clear()
        await CPUPlugin({}, {}).restore_from_container(second, alloc_map)
        await MemoryPlugin({}, {}).restore_from_container(second, alloc_map)

        assert {d for d, v in alloc_map.allocations[CPU].items() if v > 0} == {
            DeviceId("2"),
            DeviceId("3"),
        }
        assert alloc_map.allocations[MEM][DeviceId("root")] == 2 * GIB

    async def test_container_without_a_config_dir_label_is_skipped(self) -> None:
        alloc_map = _alloc_map()
        container = Container(
            id=ContainerId("x"),
            status=ContainerStatus.RUNNING,
            image="img:1",
            labels={},
            ports=[],
            backend_obj=None,
        )

        await CPUPlugin({}, {}).restore_from_container(container, alloc_map)

        assert all(v == 0 for v in alloc_map.allocations[CPU].values())

    async def test_missing_resource_file_is_reported_to_the_caller(self, tmp_path: Path) -> None:
        alloc_map = _alloc_map()
        container = _kernel(tmp_path, "k1", ["0"], GIB)
        (tmp_path / "k1" / "config" / "resource.txt").unlink()

        with pytest.raises(FileNotFoundError):
            await CPUPlugin({}, {}).restore_from_container(container, alloc_map)
