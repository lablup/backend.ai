import copy
import json
import os
import tempfile
import textwrap
import unittest.mock
import uuid
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol, cast
from unittest import mock

import pytest
from aioresponses import aioresponses
from pytest_mock import MockerFixture

from ai.backend.accelerator.mock.plugin import MockPlugin
from ai.backend.agent import resources
from ai.backend.agent.affinity_map import AffinityMap, AffinityPolicy
from ai.backend.agent.alloc_map import (
    DeviceSlotInfo,
    DiscretePropertyAllocMap,
    FractionAllocMap,
)
from ai.backend.agent.dummy.intrinsic import CPUPlugin, MemoryPlugin
from ai.backend.agent.errors import FractionalResourceFragmented, InsufficientResource
from ai.backend.agent.resources import (
    AbstractComputePlugin,
    ComputerContext,
    align_memory,
    collect_device_capacities,
    scan_gpu_alloc_map,
    scan_resource_usage_per_slot,
)
from ai.backend.agent.vendor import linux
from ai.backend.common.types import (
    DeviceId,
    DeviceName,
    KernelId,
    ResourceSlot,
    SlotName,
    SlotTypes,
)


def test_parse_cpuset() -> None:
    assert {*linux.parse_cpuset("0")} == {0}
    assert {*linux.parse_cpuset("2-5")} == {2, 3, 4, 5}
    assert {*linux.parse_cpuset("1-1")} == {1}
    assert {*linux.parse_cpuset("12,35,99")} == {12, 35, 99}
    assert {*linux.parse_cpuset("0-1,5-8,120,150-153")} == {
        0,
        1,
        5,
        6,
        7,
        8,
        120,
        150,
        151,
        152,
        153,
    }
    with pytest.raises(ValueError):
        {*linux.parse_cpuset("")}
    with pytest.raises(ValueError):
        {*linux.parse_cpuset("abc")}
    with pytest.raises(ValueError):
        {*linux.parse_cpuset("1-0")}
    with pytest.raises(ValueError):
        {*linux.parse_cpuset("-99")}


def test_node_of_cpu() -> None:
    numa = linux.libnuma()

    # When NUMA is not supported.
    linux._numa_supported = False
    assert numa.node_of_cpu(5) == 0

    # When NUMA is supported.
    original_numa_supported = linux._numa_supported
    linux._numa_supported = True
    with mock.patch.object(linux, "_libnuma", create=True) as mock_libnuma:
        numa.node_of_cpu(5)
        mock_libnuma.numa_node_of_cpu.assert_called_once_with(5)

    linux._numa_supported = original_numa_supported


def test_num_nodes() -> None:
    numa = linux.libnuma()

    # When NUMA is not supported.
    linux._numa_supported = False
    assert numa.num_nodes() == 1

    # When NUMA is supported.
    original_numa_supported = linux._numa_supported
    linux._numa_supported = True
    with mock.patch.object(linux, "_libnuma", create=True) as mock_libnuma:
        numa.num_nodes()
        mock_libnuma.numa_num_configured_nodes.assert_called_once_with()

    linux._numa_supported = original_numa_supported


@pytest.mark.skip(reason="aioresponses 0.7 is incompatible with aiohttp 3.7+")
async def test_get_available_cores_without_docker(monkeypatch: Any) -> None:
    def mock_sched_getaffinity(pid: Any) -> None:
        raise AttributeError

    def mock_sched_getaffinity2(pid: Any) -> set[int]:
        return {0, 1}

    numa = linux.libnuma()
    with aioresponses() as m:
        m.get(
            "http://docker/info",
            body=json.dumps({
                "NCPU": 4,
            }),
        )

        monkeypatch.setattr(os, "sched_getaffinity", mock_sched_getaffinity, raising=False)
        monkeypatch.setattr(os, "cpu_count", lambda: 4)
        numa.get_available_cores.cache_clear()
        assert (await numa.get_available_cores()) == {0, 1, 2, 3}

        monkeypatch.setattr(os, "sched_getaffinity", mock_sched_getaffinity2, raising=False)
        numa.get_available_cores.cache_clear()
        assert (await numa.get_available_cores()) == {0, 1}


async def test_get_core_topology(mocker: MockerFixture) -> None:
    mocker.patch.object(linux.libnuma, "num_nodes", return_value=2)
    mocker.patch.object(
        linux.libnuma, "get_available_cores", new=mock.AsyncMock(return_value={0, 1, 2, 3})
    )
    mocker.patch.object(linux.libnuma, "node_of_cpu", new=lambda n: n % 2 == 1)

    numa = linux.libnuma()
    assert (await numa.get_core_topology()) == ([0, 2], [1, 3])


async def test_scan_resource_usage_per_slot() -> None:
    with tempfile.TemporaryDirectory() as tmpdir_name:
        tmpdir = Path(tmpdir_name)
        random_kernel_id = KernelId(uuid.uuid4())
        slot_allocs = await scan_resource_usage_per_slot([random_kernel_id], tmpdir)
        # should not raise FileNotFoundError
        assert not slot_allocs  # should be empty

        kernel_ids = [
            KernelId(uuid.uuid4()),
            KernelId(uuid.uuid4()),
            KernelId(uuid.uuid4()),
        ]
        (tmpdir / str(kernel_ids[0]) / "config").mkdir(parents=True, exist_ok=True)
        (tmpdir / str(kernel_ids[1]) / "config").mkdir(parents=True, exist_ok=True)
        (tmpdir / str(kernel_ids[2]) / "config").mkdir(parents=True, exist_ok=True)
        (tmpdir / str(kernel_ids[0]) / "config" / "resource.txt").write_text(
            textwrap.dedent(
                """
        CID=a001
        SCRATCH_SIZE=0
        MOUNTS=
        SLOTS={"cpu":"5","mem":"4096","cuda.shares":"0.5"}
        """
            )
        )
        (tmpdir / str(kernel_ids[1]) / "config" / "resource.txt").write_text(
            textwrap.dedent(
                """
        CID=a002
        SCRATCH_SIZE=0
        MOUNTS=
        SLOTS={"cpu":"7","mem":"2048","cuda.shares":"0.8"}
        """
            )
        )
        (tmpdir / str(kernel_ids[2]) / "config" / "resource.txt").write_text(
            textwrap.dedent(
                """
        CID=a003
        SCRATCH_SIZE=0
        MOUNTS=
        SLOTS={"cpu":"13","mem":"1024","cuda.shares":"0.2"}
        """
            )
        )
        slot_allocs = await scan_resource_usage_per_slot(kernel_ids, tmpdir)
        assert slot_allocs[SlotName("cpu")] == Decimal(25)
        assert slot_allocs[SlotName("mem")] == Decimal(7168)
        assert slot_allocs[SlotName("cuda.shares")] == Decimal("1.5")

        # Simulate that a container has terminated in the middle.
        (tmpdir / str(kernel_ids[1]) / "config" / "resource.txt").unlink()
        slot_allocs = await scan_resource_usage_per_slot(kernel_ids, tmpdir)
        assert slot_allocs[SlotName("cpu")] == Decimal(18)
        assert slot_allocs[SlotName("mem")] == Decimal(5120)
        assert slot_allocs[SlotName("cuda.shares")] == Decimal("0.7")

        # Other parsing errors should be an explicit error.
        with unittest.mock.patch(
            "ai.backend.agent.resources.KernelResourceSpec.read_from_string",
        ) as mock:
            mock.side_effect = ValueError("parsing error")
            with pytest.raises(ExceptionGroup):
                await scan_resource_usage_per_slot(kernel_ids, tmpdir)


async def test_allow_fractional_resource_fragmentation(monkeypatch: Any) -> None:
    def mock_read_from_file(path: Any, daemon_name: Any) -> tuple[dict[str, Any], Path]:
        return {
            "slot_name": "cuda",
            "device_plugin_name": "CUDADevice",
            "devices": [
                {
                    "mother_uuid": "c59395cd-ac91-4cd3-a1b0-3d2568aa2d01",
                    "model_name": "NVIDIA B200",
                    "numa_node": 0,
                    "subproc_count": 216,
                    "memory_size": "192G",
                    "is_mig_device": False,
                },
                {
                    "mother_uuid": "c59395cd-ac91-4cd3-a1b0-3d2568aa2d02",
                    "model_name": "NVIDIA B200",
                    "numa_node": 1,
                    "subproc_count": 216,
                    "memory_size": "192G",
                    "is_mig_device": False,
                },
            ],
            "attributes": {"nvidia_driver": "570.0.0", "cuda_runtime": "12.8"},
            "formats": {
                "shares": {
                    "human_readable_name": "fGPU",
                    "description": "CUDA-capable GPU (fractional)",
                    "display_unit": "fGPU",
                    "number_format": {
                        "binary": False,
                        "round_length": 0,
                    },
                    "display_icon": "gpu1",
                }
            },
        }, Path("/resolved/mock-accelerator.toml")

    monkeypatch.setattr("ai.backend.common.config.read_from_file", mock_read_from_file)
    plugin_config = {
        "allocation_mode": "fractional",
        "unit_proc": 216,
        "unit_mem": "192G",
    }
    local_config: dict[str, Any] = {}
    cuda_plugin = MockPlugin(plugin_config, local_config)
    await cuda_plugin.init()

    cpu_plugin = CPUPlugin(
        {},
        local_config,
        {
            "agent": {"resource": {"cpu": {"num-core": 4}}},
        },
    )
    mem_plugin = MemoryPlugin(
        {},
        local_config,
        {
            "agent": {"resource": {"memory": {"size": 4096}}},
        },
    )
    cuda_devices = await cuda_plugin.list_devices()
    cpu_devices = await cpu_plugin.list_devices()
    mem_devices = await mem_plugin.list_devices()
    computers = {
        DeviceName("cpu"): ComputerContext(
            cpu_plugin, cpu_devices, await cpu_plugin.create_alloc_map()
        ),
        DeviceName("mem"): ComputerContext(
            mem_plugin, mem_devices, await mem_plugin.create_alloc_map()
        ),
        DeviceName("cuda"): ComputerContext(
            cuda_plugin, cuda_devices, await cuda_plugin.create_alloc_map()
        ),
    }
    alloc_order = [DeviceName("cuda"), DeviceName("cpu"), DeviceName("mem")]
    affinity_map = AffinityMap.build(list(cuda_devices) + list(cpu_devices) + list(mem_devices))
    affinity_policy = AffinityPolicy.PREFER_SINGLE_NODE

    resource_spec = resources.KernelResourceSpec(
        ResourceSlot.from_json({
            "cpu": "1",
            "mem": "512",
            "cuda.shares": "0.8",
        }),
        allocations={},
        scratch_disk_size=0,
        mounts=[],
    )
    resources.allocate(computers, resource_spec, alloc_order, affinity_map, affinity_policy)
    assert computers[DeviceName("cpu")].alloc_map.allocations[SlotName("cpu")][
        DeviceId("0")
    ] == Decimal(1)
    assert computers[DeviceName("cpu")].alloc_map.allocations[SlotName("cpu")][
        DeviceId("1")
    ] == Decimal(0)
    assert computers[DeviceName("mem")].alloc_map.allocations[SlotName("mem")][
        DeviceId("root")
    ] == Decimal(512)
    assert computers[DeviceName("cuda")].alloc_map.allocations[SlotName("cuda.shares")][
        DeviceId("c59395cd-ac91-4cd3-a1b0-3d2568aa2d01")
    ] == Decimal(0)
    assert computers[DeviceName("cuda")].alloc_map.allocations[SlotName("cuda.shares")][
        DeviceId("c59395cd-ac91-4cd3-a1b0-3d2568aa2d02")
    ] == Decimal("0.8")

    resources.allocate(computers, resource_spec, alloc_order, affinity_map, affinity_policy)
    assert computers[DeviceName("cpu")].alloc_map.allocations[SlotName("cpu")][
        DeviceId("0")
    ] == Decimal(1)
    assert computers[DeviceName("cpu")].alloc_map.allocations[SlotName("cpu")][
        DeviceId("1")
    ] == Decimal(1)
    assert computers[DeviceName("mem")].alloc_map.allocations[SlotName("mem")][
        DeviceId("root")
    ] == Decimal(1024)
    assert computers[DeviceName("cuda")].alloc_map.allocations[SlotName("cuda.shares")][
        DeviceId("c59395cd-ac91-4cd3-a1b0-3d2568aa2d01")
    ] == Decimal("0.8")
    assert computers[DeviceName("cuda")].alloc_map.allocations[SlotName("cuda.shares")][
        DeviceId("c59395cd-ac91-4cd3-a1b0-3d2568aa2d02")
    ] == Decimal("0.8")

    resource_spec = resources.KernelResourceSpec(
        ResourceSlot.from_json({
            "cpu": "1",
            "mem": "512",
            "cuda.shares": "0.4",
        }),
        allocations={},
        scratch_disk_size=0,
        mounts=[],
    )
    with pytest.raises(FractionalResourceFragmented):
        resources.allocate(
            computers,
            resource_spec,
            alloc_order,
            affinity_map,
            affinity_policy,
            allow_fractional_resource_fragmentation=False,
        )
    assert computers[DeviceName("cpu")].alloc_map.allocations[SlotName("cpu")][
        DeviceId("0")
    ] == Decimal(1)
    assert computers[DeviceName("cpu")].alloc_map.allocations[SlotName("cpu")][
        DeviceId("1")
    ] == Decimal(1)
    assert computers[DeviceName("mem")].alloc_map.allocations[SlotName("mem")][
        DeviceId("root")
    ] == Decimal(1024)
    assert computers[DeviceName("cuda")].alloc_map.allocations[SlotName("cuda.shares")][
        DeviceId("c59395cd-ac91-4cd3-a1b0-3d2568aa2d01")
    ] == Decimal("0.8")
    assert computers[DeviceName("cuda")].alloc_map.allocations[SlotName("cuda.shares")][
        DeviceId("c59395cd-ac91-4cd3-a1b0-3d2568aa2d02")
    ] == Decimal("0.8")

    resources.allocate(
        computers,
        resource_spec,
        alloc_order,
        affinity_map,
        affinity_policy,
        allow_fractional_resource_fragmentation=True,
    )
    assert computers[DeviceName("cpu")].alloc_map.allocations[SlotName("cpu")][
        DeviceId("0")
    ] == Decimal(1)
    assert computers[DeviceName("cpu")].alloc_map.allocations[SlotName("cpu")][
        DeviceId("1")
    ] == Decimal(1)
    assert computers[DeviceName("cpu")].alloc_map.allocations[SlotName("cpu")][
        DeviceId("2")
    ] == Decimal(1)
    assert computers[DeviceName("mem")].alloc_map.allocations[SlotName("mem")][
        DeviceId("root")
    ] == Decimal(1536)
    assert computers[DeviceName("cuda")].alloc_map.allocations[SlotName("cuda.shares")][
        DeviceId("c59395cd-ac91-4cd3-a1b0-3d2568aa2d01")
    ] == Decimal("1.0")
    assert computers[DeviceName("cuda")].alloc_map.allocations[SlotName("cuda.shares")][
        DeviceId("c59395cd-ac91-4cd3-a1b0-3d2568aa2d02")
    ] == Decimal("1.0")


async def test_allocate_rollback(monkeypatch: Any) -> None:
    local_config: dict[str, Any] = {}
    cpu_plugin = CPUPlugin(
        {},
        local_config,
        {
            "agent": {"resource": {"cpu": {"num-core": 2}}},
        },
    )
    mem_plugin = MemoryPlugin(
        {},
        local_config,
        {
            "agent": {"resource": {"memory": {"size": 1024}}},
        },
    )
    cpu_devices = await cpu_plugin.list_devices()
    mem_devices = await mem_plugin.list_devices()
    computers = {
        DeviceName("cpu"): ComputerContext(
            cpu_plugin, cpu_devices, await cpu_plugin.create_alloc_map()
        ),
        DeviceName("mem"): ComputerContext(
            mem_plugin, mem_devices, await mem_plugin.create_alloc_map()
        ),
    }
    alloc_order = [DeviceName("cpu"), DeviceName("mem")]
    affinity_map = AffinityMap.build(list(cpu_devices) + list(mem_devices))
    affinity_policy = AffinityPolicy.PREFER_SINGLE_NODE

    resource_spec = resources.KernelResourceSpec(
        ResourceSlot.from_json({
            "cpu": "1",
            "mem": "512",
        }),
        allocations={},
        scratch_disk_size=0,
        mounts=[],
    )
    resources.allocate(computers, resource_spec, alloc_order, affinity_map, affinity_policy)
    assert computers[DeviceName("cpu")].alloc_map.allocations[SlotName("cpu")][
        DeviceId("0")
    ] == Decimal(1)
    assert computers[DeviceName("cpu")].alloc_map.allocations[SlotName("cpu")][
        DeviceId("1")
    ] == Decimal(0)
    assert computers[DeviceName("mem")].alloc_map.allocations[SlotName("mem")][
        DeviceId("root")
    ] == Decimal(512)
    resource_spec = resources.KernelResourceSpec(
        ResourceSlot.from_json({
            "cpu": "1",
            "mem": "1024",  # should fail to allocate
        }),
        allocations={},
        scratch_disk_size=0,
        mounts=[],
    )
    with pytest.raises(InsufficientResource):
        resources.allocate(computers, resource_spec, alloc_order, affinity_map, affinity_policy)
    # check if the cpu alloc is NOT rolled back
    assert computers[DeviceName("cpu")].alloc_map.allocations[SlotName("cpu")][
        DeviceId("0")
    ] == Decimal(1)
    assert computers[DeviceName("cpu")].alloc_map.allocations[SlotName("cpu")][
        DeviceId("1")
    ] == Decimal(0)  # has been rolled back
    assert computers[DeviceName("mem")].alloc_map.allocations[SlotName("mem")][
        DeviceId("root")
    ] == Decimal(512)

    # Now let's test the case when the rollback does not happen.
    # Reset the alloc map
    computers[DeviceName("cpu")].alloc_map.clear()
    computers[DeviceName("mem")].alloc_map.clear()

    # Make deepcopy a no-op returning the target object's reference as-is
    monkeypatch.setattr(copy, "deepcopy", lambda o: o)

    resource_spec = resources.KernelResourceSpec(
        ResourceSlot.from_json({
            "cpu": "1",
            "mem": "512",
        }),
        allocations={},
        scratch_disk_size=0,
        mounts=[],
    )
    resources.allocate(computers, resource_spec, alloc_order, affinity_map, affinity_policy)
    assert computers[DeviceName("cpu")].alloc_map.allocations[SlotName("cpu")][
        DeviceId("0")
    ] == Decimal(1)
    assert computers[DeviceName("cpu")].alloc_map.allocations[SlotName("cpu")][
        DeviceId("1")
    ] == Decimal(0)
    assert computers[DeviceName("mem")].alloc_map.allocations[SlotName("mem")][
        DeviceId("root")
    ] == Decimal(512)
    resource_spec = resources.KernelResourceSpec(
        ResourceSlot.from_json({
            "cpu": "1",
            "mem": "1024",  # should fail to allocate
        }),
        allocations={},
        scratch_disk_size=0,
        mounts=[],
    )
    with pytest.raises(InsufficientResource):
        resources.allocate(computers, resource_spec, alloc_order, affinity_map, affinity_policy)
    # check if the cpu alloc is NOT rolled back
    assert computers[DeviceName("cpu")].alloc_map.allocations[SlotName("cpu")][
        DeviceId("0")
    ] == Decimal(1)
    assert computers[DeviceName("cpu")].alloc_map.allocations[SlotName("cpu")][
        DeviceId("1")
    ] == Decimal(1)  # not rolled back...
    assert computers[DeviceName("mem")].alloc_map.allocations[SlotName("mem")][
        DeviceId("root")
    ] == Decimal(512)  # this is rolled back because it failed to allocate the mem slot.


def test_align_memory() -> None:
    align = 10
    reserved = 1000
    print(f"{align=} {reserved=}")
    for orig in range(19950, 20050):
        usable, actual_reserved = align_memory(orig, reserved, align=align)
        print(f"{orig=} -> {usable=} {actual_reserved=}")
        assert usable % align == 0
        assert usable + actual_reserved == orig
        assert 990 <= actual_reserved <= 1010


class WriteResourceSpec(Protocol):
    def __call__(self, kernel_id: KernelId, share_lines: Mapping[str, str]) -> None: ...


@pytest.fixture
def scratch_root(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def write_resource_spec(scratch_root: Path) -> WriteResourceSpec:
    def _write(kernel_id: KernelId, share_lines: Mapping[str, str]) -> None:
        config_dir = scratch_root / str(kernel_id) / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        header = textwrap.dedent("""\
            SCRATCH_SIZE=0
            MOUNTS=
            SLOTS={"cpu":"1","mem":"1024"}
        """)
        body = "".join(f"{key}={value}\n" for key, value in share_lines.items())
        (config_dir / "resource.txt").write_text(header + body)

    return _write


class TestNormalizeDeviceAlloc:
    def test_returns_the_ratio_against_the_device_capacity(self) -> None:
        capacities = {(SlotName("cuda.shares"), DeviceId("0")): Decimal("2")}
        assert resources._normalize_device_alloc(
            capacities, SlotName("cuda.shares"), DeviceId("0"), Decimal("0.5")
        ) == Decimal("0.25")

    def test_reports_the_raw_allocation_when_the_device_has_no_capacity(self) -> None:
        assert resources._normalize_device_alloc(
            {}, SlotName("cuda.shares"), DeviceId("0"), Decimal("0.5")
        ) == Decimal("0.5")

    def test_reports_the_raw_allocation_when_the_capacity_is_not_positive(self) -> None:
        capacities = {(SlotName("cuda.shares"), DeviceId("0")): Decimal("0")}
        assert resources._normalize_device_alloc(
            capacities, SlotName("cuda.shares"), DeviceId("0"), Decimal("0.5")
        ) == Decimal("0.5")


class TestCollectDeviceCapacities:
    def test_flattens_the_device_slots_of_every_computer(self) -> None:
        cpu_alloc_map = DiscretePropertyAllocMap(
            device_slots={
                DeviceId("0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal("1")),
                DeviceId("1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal("1")),
            },
        )
        cuda_alloc_map = FractionAllocMap(
            device_slots={
                DeviceId("gpu0"): DeviceSlotInfo(
                    SlotTypes.COUNT, SlotName("cuda.shares"), Decimal("2")
                ),
            },
        )
        computers = {
            DeviceName("cpu"): ComputerContext(
                cast(AbstractComputePlugin, mock.Mock()), [], cpu_alloc_map
            ),
            DeviceName("cuda"): ComputerContext(
                cast(AbstractComputePlugin, mock.Mock()), [], cuda_alloc_map
            ),
        }

        assert collect_device_capacities(computers) == {
            (SlotName("cpu"), DeviceId("0")): Decimal("1"),
            (SlotName("cpu"), DeviceId("1")): Decimal("1"),
            (SlotName("cuda.shares"), DeviceId("gpu0")): Decimal("2"),
        }

    def test_returns_an_empty_map_without_computers(self) -> None:
        assert collect_device_capacities({}) == {}


class TestScanGPUAllocMap:
    async def test_normalizes_the_allocation_into_a_capacity_ratio(
        self, scratch_root: Path, write_resource_spec: WriteResourceSpec
    ) -> None:
        kernel_id = KernelId(uuid.uuid4())
        write_resource_spec(kernel_id, {"CUDA.SHARES_SHARES": "0:0.5"})

        result = await scan_gpu_alloc_map(
            [kernel_id],
            scratch_root,
            {(SlotName("cuda.shares"), DeviceId("0")): Decimal("2")},
        )

        assert result == {DeviceId("0"): Decimal("0.2500")}

    async def test_sums_the_allocations_of_every_kernel_on_the_same_device(
        self, scratch_root: Path, write_resource_spec: WriteResourceSpec
    ) -> None:
        kernel_ids = [KernelId(uuid.uuid4()) for _ in range(3)]
        write_resource_spec(kernel_ids[0], {"CUDA.SHARES_SHARES": "0:0.5"})
        write_resource_spec(kernel_ids[1], {"CUDA.SHARES_SHARES": "0:0.25,1:1"})
        write_resource_spec(kernel_ids[2], {"CUDA.SHARES_SHARES": "1:0.5"})

        result = await scan_gpu_alloc_map(
            kernel_ids,
            scratch_root,
            {
                (SlotName("cuda.shares"), DeviceId("0")): Decimal("1"),
                (SlotName("cuda.shares"), DeviceId("1")): Decimal("2"),
            },
        )

        assert result == {
            DeviceId("0"): Decimal("0.7500"),
            DeviceId("1"): Decimal("0.7500"),
        }

    async def test_skips_a_kernel_whose_resource_spec_is_gone(
        self, scratch_root: Path, write_resource_spec: WriteResourceSpec
    ) -> None:
        alive_kernel_id = KernelId(uuid.uuid4())
        terminated_kernel_id = KernelId(uuid.uuid4())
        write_resource_spec(alive_kernel_id, {"CUDA.SHARES_SHARES": "0:1"})

        result = await scan_gpu_alloc_map(
            [alive_kernel_id, terminated_kernel_id],
            scratch_root,
            {(SlotName("cuda.shares"), DeviceId("0")): Decimal("2")},
        )

        assert result == {DeviceId("0"): Decimal("0.5000")}

    async def test_reports_the_raw_allocation_when_the_capacity_is_unknown(
        self, scratch_root: Path, write_resource_spec: WriteResourceSpec
    ) -> None:
        kernel_id = KernelId(uuid.uuid4())
        write_resource_spec(kernel_id, {"CUDA.SHARES_SHARES": "0:0.5"})

        result = await scan_gpu_alloc_map([kernel_id], scratch_root, {})

        assert result == {DeviceId("0"): Decimal("0.5000")}

    async def test_ignores_the_devices_other_than_cuda(
        self, scratch_root: Path, write_resource_spec: WriteResourceSpec
    ) -> None:
        kernel_id = KernelId(uuid.uuid4())
        write_resource_spec(kernel_id, {"CPU_SHARES": "0:2", "MEM_SHARES": "root:1024"})

        result = await scan_gpu_alloc_map(
            [kernel_id],
            scratch_root,
            {(SlotName("cpu"), DeviceId("0")): Decimal("4")},
        )

        assert result == {}

    async def test_quantizes_the_ratio_to_four_decimal_places(
        self, scratch_root: Path, write_resource_spec: WriteResourceSpec
    ) -> None:
        kernel_id = KernelId(uuid.uuid4())
        write_resource_spec(kernel_id, {"CUDA.SHARES_SHARES": "0:1"})

        result = await scan_gpu_alloc_map(
            [kernel_id],
            scratch_root,
            {(SlotName("cuda.shares"), DeviceId("0")): Decimal("3")},
        )

        assert result == {DeviceId("0"): Decimal("0.3333")}

    async def test_returns_an_empty_map_without_kernels(self, scratch_root: Path) -> None:
        assert await scan_gpu_alloc_map([], scratch_root, {}) == {}
