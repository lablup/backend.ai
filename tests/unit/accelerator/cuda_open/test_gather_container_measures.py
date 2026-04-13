from __future__ import annotations

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

    def _make_container_info(self, device_ids: list[str]) -> dict[str, Any]:
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

    async def test_container_show_is_called(
        self,
        cuda_plugin: CUDAPlugin,
        stat_context: MagicMock,
        mock_libnvml: MagicMock,
    ) -> None:
        """container.show() must be called to get the inspect dict (BA-5693)."""
        mock_container = AsyncMock()
        mock_container.show.return_value = self._make_container_info(["0"])

        mock_docker = AsyncMock()
        mock_docker.__aenter__ = AsyncMock(return_value=mock_docker)
        mock_docker.__aexit__ = AsyncMock(return_value=False)
        mock_docker.containers.get.return_value = mock_container

        with (
            patch("ai.backend.accelerator.cuda_open.plugin.libnvml", mock_libnvml),
            patch(
                "ai.backend.accelerator.cuda_open.plugin.aiodocker.Docker", return_value=mock_docker
            ),
        ):
            results = await cuda_plugin.gather_container_measures(stat_context, ["container_001"])

        mock_docker.containers.get.assert_called_once_with("container_001")
        mock_container.show.assert_called_once()

        cuda_mem, cuda_util = results
        assert cuda_mem.key == MetricKey("cuda_mem")
        assert cuda_util.key == MetricKey("cuda_util")
        assert "container_001" in cuda_mem.per_container
        assert cuda_mem.per_container["container_001"].value == Decimal(1024 * 1024 * 512)

    async def test_docker_error_skips_container(
        self,
        cuda_plugin: CUDAPlugin,
        stat_context: MagicMock,
        mock_libnvml: MagicMock,
    ) -> None:
        """DockerError on a vanished container should be skipped, not crash the loop."""
        mock_good_container = AsyncMock()
        mock_good_container.show.return_value = self._make_container_info(["0"])

        mock_docker = AsyncMock()
        mock_docker.__aenter__ = AsyncMock(return_value=mock_docker)
        mock_docker.__aexit__ = AsyncMock(return_value=False)
        mock_docker.containers.get.side_effect = [
            DockerError(status=404, data={"message": "No such container"}),
            mock_good_container,
        ]

        with (
            patch("ai.backend.accelerator.cuda_open.plugin.libnvml", mock_libnvml),
            patch(
                "ai.backend.accelerator.cuda_open.plugin.aiodocker.Docker", return_value=mock_docker
            ),
        ):
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
        mock_libnvml: MagicMock,
    ) -> None:
        """Container with multiple GPUs should aggregate metrics from all devices."""
        mock_container = AsyncMock()
        mock_container.show.return_value = self._make_container_info(["0", "1"])

        mock_docker = AsyncMock()
        mock_docker.__aenter__ = AsyncMock(return_value=mock_docker)
        mock_docker.__aexit__ = AsyncMock(return_value=False)
        mock_docker.containers.get.return_value = mock_container

        with (
            patch("ai.backend.accelerator.cuda_open.plugin.libnvml", mock_libnvml),
            patch(
                "ai.backend.accelerator.cuda_open.plugin.aiodocker.Docker", return_value=mock_docker
            ),
        ):
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
        mock_libnvml: MagicMock,
    ) -> None:
        """Container without nvidia DeviceRequests should be skipped."""
        mock_container = AsyncMock()
        mock_container.show.return_value = {"HostConfig": {"DeviceRequests": []}}

        mock_docker = AsyncMock()
        mock_docker.__aenter__ = AsyncMock(return_value=mock_docker)
        mock_docker.__aexit__ = AsyncMock(return_value=False)
        mock_docker.containers.get.return_value = mock_container

        with (
            patch("ai.backend.accelerator.cuda_open.plugin.libnvml", mock_libnvml),
            patch(
                "ai.backend.accelerator.cuda_open.plugin.aiodocker.Docker", return_value=mock_docker
            ),
        ):
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
