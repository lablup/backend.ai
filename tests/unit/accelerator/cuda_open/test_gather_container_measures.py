from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from ai.backend.accelerator.cuda_open.plugin import CUDAPlugin
from ai.backend.agent.stats import StatModes
from ai.backend.common.types import DeviceId, MetricKey, SlotName


@dataclass
class FakeDeviceStat:
    mem_used: int
    mem_total: int
    gpu_util: int


def _alloc(*device_ids: str) -> Mapping[SlotName, Mapping[DeviceId, Decimal]]:
    """What the agent reports a container holds — the same shape as
    ``KernelResourceSpec.allocations[DeviceName("cuda")]``."""
    return {SlotName("cuda.device"): {DeviceId(d): Decimal(1) for d in device_ids}}


class TestGatherContainerMeasures:
    """Per-container GPU measures come from the AGENT's allocation, not from the container runtime.

    Reading them back out of Docker's `HostConfig.DeviceRequests` (BA-5693) meant every containerd
    and enroot container raised `DockerError(404, 'No such container')` once per stat cycle and
    reported no GPU utilization at all. The agent already knows the allocation, for every backend.
    """

    @pytest.fixture
    def cuda_plugin(self) -> CUDAPlugin:
        plugin = CUDAPlugin.__new__(CUDAPlugin)
        plugin.plugin_config = {}
        plugin.local_config = {}
        plugin.enabled = True
        plugin.device_mask = []
        return plugin

    @pytest.fixture
    def allocations(self) -> dict[str, Mapping[SlotName, Mapping[DeviceId, Decimal]]]:
        """container id -> its cuda allocation; anything absent is a container the agent
        does not know about."""
        return {}

    @pytest.fixture
    def stat_context(
        self, allocations: dict[str, Mapping[SlotName, Mapping[DeviceId, Decimal]]]
    ) -> MagicMock:
        ctx = MagicMock()
        ctx.mode = StatModes.DOCKER
        ctx.agent.get_container_device_allocation.side_effect = (
            lambda container_id, device_name: allocations.get(container_id, {})
        )
        return ctx

    @pytest.fixture
    def mock_libnvml(self) -> MagicMock:
        nvml = MagicMock()
        nvml.get_device_count.return_value = 2
        nvml.get_device_stats.side_effect = lambda dev_id: FakeDeviceStat(
            mem_used=1024 * 1024 * 512,
            mem_total=1024 * 1024 * 1024 * 8,
            gpu_util=45,
        )
        return nvml

    @pytest.fixture
    def patched_nvml(self, mock_libnvml: MagicMock) -> Iterator[None]:
        with patch("ai.backend.accelerator.cuda_open.plugin.libnvml", mock_libnvml):
            yield

    async def test_measures_come_from_the_agent_allocation(
        self,
        cuda_plugin: CUDAPlugin,
        stat_context: MagicMock,
        allocations: dict[str, Mapping[SlotName, Mapping[DeviceId, Decimal]]],
        patched_nvml: None,
    ) -> None:
        allocations["container_001"] = _alloc("0")

        results = await cuda_plugin.gather_container_measures(stat_context, ["container_001"])

        cuda_mem, cuda_util = results
        assert cuda_mem.key == MetricKey("cuda_mem")
        assert cuda_util.key == MetricKey("cuda_util")
        assert cuda_mem.per_container["container_001"].value == Decimal(1024 * 1024 * 512)

    async def test_no_container_runtime_is_queried(
        self,
        cuda_plugin: CUDAPlugin,
        stat_context: MagicMock,
        allocations: dict[str, Mapping[SlotName, Mapping[DeviceId, Decimal]]],
        patched_nvml: None,
    ) -> None:
        """The whole point: measuring must not depend on Docker being the runtime."""
        allocations["container_001"] = _alloc("0")

        with patch("ai.backend.accelerator.cuda_open.plugin.aiodocker.Docker") as mock_docker_cls:
            await cuda_plugin.gather_container_measures(stat_context, ["container_001"])

        mock_docker_cls.assert_not_called()

    async def test_unknown_container_is_skipped(
        self,
        cuda_plugin: CUDAPlugin,
        stat_context: MagicMock,
        allocations: dict[str, Mapping[SlotName, Mapping[DeviceId, Decimal]]],
        patched_nvml: None,
    ) -> None:
        """A container that has already gone is skipped, not an error for the whole round."""
        allocations["good_cid"] = _alloc("0")

        results = await cuda_plugin.gather_container_measures(
            stat_context, ["vanished_cid", "good_cid"]
        )

        cuda_mem, _ = results
        assert "vanished_cid" not in cuda_mem.per_container
        assert "good_cid" in cuda_mem.per_container

    async def test_multi_gpu_container_aggregates(
        self,
        cuda_plugin: CUDAPlugin,
        stat_context: MagicMock,
        allocations: dict[str, Mapping[SlotName, Mapping[DeviceId, Decimal]]],
        patched_nvml: None,
    ) -> None:
        allocations["multi_gpu_cid"] = _alloc("0", "1")

        results = await cuda_plugin.gather_container_measures(stat_context, ["multi_gpu_cid"])

        cuda_mem, cuda_util = results
        mem = cuda_mem.per_container["multi_gpu_cid"]
        assert mem.value == Decimal(1024 * 1024 * 512 * 2)
        assert mem.capacity == Decimal(1024 * 1024 * 1024 * 8 * 2)
        util = cuda_util.per_container["multi_gpu_cid"]
        assert util.value == Decimal(45 * 2)
        assert util.capacity == Decimal(200)

    async def test_container_without_gpus_is_skipped(
        self,
        cuda_plugin: CUDAPlugin,
        stat_context: MagicMock,
        allocations: dict[str, Mapping[SlotName, Mapping[DeviceId, Decimal]]],
        patched_nvml: None,
    ) -> None:
        allocations["no_gpu_cid"] = {SlotName("cuda.device"): {}}

        results = await cuda_plugin.gather_container_measures(stat_context, ["no_gpu_cid"])

        cuda_mem, _ = results
        assert "no_gpu_cid" not in cuda_mem.per_container

    async def test_zero_allocation_is_skipped(
        self,
        cuda_plugin: CUDAPlugin,
        stat_context: MagicMock,
        allocations: dict[str, Mapping[SlotName, Mapping[DeviceId, Decimal]]],
        patched_nvml: None,
    ) -> None:
        """A device present in the map but allocated 0 is not this container's."""
        allocations["zero_cid"] = {SlotName("cuda.device"): {DeviceId("0"): Decimal(0)}}

        results = await cuda_plugin.gather_container_measures(stat_context, ["zero_cid"])

        cuda_mem, _ = results
        assert "zero_cid" not in cuda_mem.per_container

    async def test_masked_device_is_not_measured(
        self,
        cuda_plugin: CUDAPlugin,
        stat_context: MagicMock,
        allocations: dict[str, Mapping[SlotName, Mapping[DeviceId, Decimal]]],
        patched_nvml: None,
    ) -> None:
        """A masked device has no NVML stats; the container is still measured on the rest."""
        cuda_plugin.device_mask = [DeviceId("1")]
        allocations["masked_cid"] = _alloc("0", "1")

        results = await cuda_plugin.gather_container_measures(stat_context, ["masked_cid"])

        cuda_mem, cuda_util = results
        assert cuda_mem.per_container["masked_cid"].value == Decimal(1024 * 1024 * 512)
        assert cuda_util.per_container["masked_cid"].capacity == Decimal(100)

    async def test_disabled_plugin_returns_empty(
        self,
        cuda_plugin: CUDAPlugin,
        stat_context: MagicMock,
    ) -> None:
        cuda_plugin.enabled = False

        results = await cuda_plugin.gather_container_measures(stat_context, ["any_cid"])

        cuda_mem, cuda_util = results
        assert cuda_mem.per_container == {}
        assert cuda_util.per_container == {}
