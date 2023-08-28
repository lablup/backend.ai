import json
import tempfile
import textwrap
import unittest.mock
import uuid
from decimal import Decimal
from pathlib import Path
from unittest import mock

import pytest
from aioresponses import aioresponses

from ai.backend.agent.resources import scan_resource_usage_per_slot
from ai.backend.agent.vendor import linux
from ai.backend.common.types import KernelId, SlotName

# TODO: write tests for KernelResourceSpec (read/write consistency)
# from ai.backend.agent.resources import (
#     KernelResourceSpec,
# )

# TODO: write tests for DiscretePropertyAllocMap, FractionAllocMap


def test_parse_cpuset():
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


def test_node_of_cpu():
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


def test_num_nodes():
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
@pytest.mark.asyncio
async def test_get_available_cores_without_docker(monkeypatch):
    def mock_sched_getaffinity(pid):
        raise AttributeError

    def mock_sched_getaffinity2(pid):
        return {0, 1}

    numa = linux.libnuma()
    with aioresponses() as m:
        m.get(
            "http://docker/info",
            body=json.dumps(
                {
                    "NCPU": 4,
                }
            ),
        )

        monkeypatch.setattr(linux.os, "sched_getaffinity", mock_sched_getaffinity, raising=False)
        monkeypatch.setattr(linux.os, "cpu_count", lambda: 4)
        numa.get_available_cores.cache_clear()
        assert (await numa.get_available_cores()) == {0, 1, 2, 3}

        monkeypatch.setattr(linux.os, "sched_getaffinity", mock_sched_getaffinity2, raising=False)
        numa.get_available_cores.cache_clear()
        assert (await numa.get_available_cores()) == {0, 1}


@pytest.mark.asyncio
async def test_get_core_topology(mocker):
    mocker.patch.object(linux.libnuma, "num_nodes", return_value=2)
    mocker.patch.object(
        linux.libnuma, "get_available_cores", new=mock.AsyncMock(return_value={0, 1, 2, 3})
    )
    mocker.patch.object(linux.libnuma, "node_of_cpu", new=lambda n: n % 2 == 1)

    numa = linux.libnuma()
    assert (await numa.get_core_topology()) == ([0, 2], [1, 3])


@pytest.mark.asyncio
async def test_scan_resource_usage_per_slot(monkeypatch):
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
        (tmpdir / str(kernel_ids[0]) / "config" / "resource.txt").write_text(textwrap.dedent("""
        CID=a001
        SCRATCH_SIZE=0
        MOUNTS=
        SLOTS={"cpu":"5","mem":"4096","cuda.shares":"0.5"}
        """))
        (tmpdir / str(kernel_ids[1]) / "config" / "resource.txt").write_text(textwrap.dedent("""
        CID=a002
        SCRATCH_SIZE=0
        MOUNTS=
        SLOTS={"cpu":"7","mem":"2048","cuda.shares":"0.8"}
        """))
        (tmpdir / str(kernel_ids[2]) / "config" / "resource.txt").write_text(textwrap.dedent("""
        CID=a003
        SCRATCH_SIZE=0
        MOUNTS=
        SLOTS={"cpu":"13","mem":"1024","cuda.shares":"0.2"}
        """))
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
