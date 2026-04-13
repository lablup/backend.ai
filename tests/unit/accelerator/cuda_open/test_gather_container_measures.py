from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiodocker.exceptions import DockerError

from ai.backend.accelerator.cuda_open.plugin import CUDAPlugin
from ai.backend.agent.stats import StatModes
from ai.backend.common.types import MetricKey


@dataclass
class FakeDeviceStat:
    mem_used: int
    mem_total: int
    gpu_util: int


def _make_container_info(device_ids: list[str]) -> dict[str, Any]:
    return {
        "HostConfig": {
            "DeviceRequests": [
                {
                    "Driver": "nvidia",
                    "DeviceIDs": device_ids,
                    "Capabilities": [["utility", "compute"]],
                },
            ],
        },
    }


def _make_mock_docker() -> AsyncMock:
    mock = AsyncMock()
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=False)
    return mock


def _make_mock_container(container_info: dict[str, Any]) -> AsyncMock:
    mock = AsyncMock()
    mock.show.return_value = container_info
    return mock


class TestGatherContainerMeasures:
    """Tests for CUDAPlugin.gather_container_measures (BA-5693 regression)."""

    @pytest.fixture
    def cuda_plugin(self) -> CUDAPlugin:
        plugin = CUDAPlugin.__new__(CUDAPlugin)
        plugin.plugin_config = {}
        plugin.local_config = {}
        plugin.enabled = True
        plugin.device_mask = []
        return plugin

    @pytest.fixture
    def stat_context(self) -> MagicMock:
        ctx = MagicMock()
        ctx.mode = StatModes.DOCKER
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
    def mock_docker(self) -> AsyncMock:
        return _make_mock_docker()

    @pytest.fixture
    def single_gpu_container(self) -> AsyncMock:
        return _make_mock_container(_make_container_info(["0"]))

    @pytest.fixture
    def multi_gpu_container(self) -> AsyncMock:
        return _make_mock_container(_make_container_info(["0", "1"]))

    @pytest.fixture
    def no_gpu_container(self) -> AsyncMock:
        return _make_mock_container({"HostConfig": {"DeviceRequests": []}})

    @pytest.fixture
    def patched_env(
        self,
        mock_libnvml: MagicMock,
        mock_docker: AsyncMock,
    ) -> Iterator[None]:
        with (
            patch("ai.backend.accelerator.cuda_open.plugin.libnvml", mock_libnvml),
            patch(
                "ai.backend.accelerator.cuda_open.plugin.aiodocker.Docker",
                return_value=mock_docker,
            ),
        ):
            yield

    async def test_container_show_is_called(
        self,
        cuda_plugin: CUDAPlugin,
        stat_context: MagicMock,
        mock_docker: AsyncMock,
        single_gpu_container: AsyncMock,
        patched_env: None,
    ) -> None:
        """container.show() must be called to get the inspect dict (BA-5693)."""
        mock_docker.containers.get.return_value = single_gpu_container

        results = await cuda_plugin.gather_container_measures(stat_context, ["container_001"])

        mock_docker.containers.get.assert_called_once_with("container_001")
        single_gpu_container.show.assert_called_once()

        cuda_mem, cuda_util = results
        assert cuda_mem.key == MetricKey("cuda_mem")
        assert cuda_util.key == MetricKey("cuda_util")
        assert "container_001" in cuda_mem.per_container
        assert cuda_mem.per_container["container_001"].value == Decimal(1024 * 1024 * 512)

    async def test_docker_error_skips_container(
        self,
        cuda_plugin: CUDAPlugin,
        stat_context: MagicMock,
        mock_docker: AsyncMock,
        single_gpu_container: AsyncMock,
        patched_env: None,
    ) -> None:
        """DockerError on a vanished container should be skipped, not crash the loop."""
        mock_docker.containers.get.side_effect = [
            DockerError(status=404, data={"message": "No such container"}),
            single_gpu_container,
        ]

        results = await cuda_plugin.gather_container_measures(
            stat_context, ["vanished_cid", "good_cid"]
        )

        cuda_mem, cuda_util = results
        assert "vanished_cid" not in cuda_mem.per_container
        assert "good_cid" in cuda_mem.per_container

    async def test_multi_gpu_container(
        self,
        cuda_plugin: CUDAPlugin,
        stat_context: MagicMock,
        mock_docker: AsyncMock,
        multi_gpu_container: AsyncMock,
        patched_env: None,
    ) -> None:
        """Container with multiple GPUs should aggregate metrics from all devices."""
        mock_docker.containers.get.return_value = multi_gpu_container

        results = await cuda_plugin.gather_container_measures(stat_context, ["multi_gpu_cid"])

        cuda_mem, cuda_util = results
        mem = cuda_mem.per_container["multi_gpu_cid"]
        assert mem.value == Decimal(1024 * 1024 * 512 * 2)
        assert mem.capacity == Decimal(1024 * 1024 * 1024 * 8 * 2)
        util = cuda_util.per_container["multi_gpu_cid"]
        assert util.value == Decimal(45 * 2)
        assert util.capacity == Decimal(200)

    async def test_no_nvidia_device_requests(
        self,
        cuda_plugin: CUDAPlugin,
        stat_context: MagicMock,
        mock_docker: AsyncMock,
        no_gpu_container: AsyncMock,
        patched_env: None,
    ) -> None:
        """Container without nvidia DeviceRequests should be skipped."""
        mock_docker.containers.get.return_value = no_gpu_container

        results = await cuda_plugin.gather_container_measures(stat_context, ["no_gpu_cid"])

        cuda_mem, _ = results
        assert "no_gpu_cid" not in cuda_mem.per_container

    async def test_disabled_plugin_returns_empty(
        self,
        cuda_plugin: CUDAPlugin,
        stat_context: MagicMock,
    ) -> None:
        """Disabled plugin should return empty measurements without querying Docker."""
        cuda_plugin.enabled = False

        results = await cuda_plugin.gather_container_measures(stat_context, ["any_cid"])

        cuda_mem, cuda_util = results
        assert len(cuda_mem.per_container) == 0
        assert len(cuda_util.per_container) == 0
